#!/usr/bin/env python3
"""
Multi-Sensor Air Quality Simulator
Simulates 3 different types of sensors with realistic characteristics
"""

import time
import math
import random
import requests
from datetime import datetime
import threading

API_URL = "http://localhost:8000/api/sensors"

# Sensor configurations
SENSORS = {
    "sensor-urban-1": {
        "type": "Urban",
        "location": "City Center",
        "baselines": {"pm2_5": 35, "pm10": 60, "temperature": 26, "humidity": 45},
        "variation": {"pm2_5": 8, "pm10": 15, "temperature": 3, "humidity": 8},
        "pollution_factor": 1.8,  # Higher pollution in urban areas
        "traffic_patterns": True
    },
    "sensor-industrial-1": {
        "type": "Industrial",
        "location": "Factory Zone",
        "baselines": {"pm2_5": 45, "pm10": 80, "temperature": 28, "humidity": 40},
        "variation": {"pm2_5": 12, "pm10": 20, "temperature": 4, "humidity": 10},
        "pollution_factor": 2.2,  # Highest pollution near factories
        "industrial_cycles": True
    },
    "sensor-residential-1": {
        "type": "Residential",
        "location": "Suburban Area",
        "baselines": {"pm2_5": 20, "pm10": 35, "temperature": 24, "humidity": 55},
        "variation": {"pm2_5": 4, "pm10": 8, "temperature": 2, "humidity": 6},
        "pollution_factor": 0.8,  # Cleaner air in residential areas
        "daily_patterns": True
    },
    "sensor-bus-1": {
        "type": "Mobile",
        "location": "City Bus Route",
        "baselines": {"pm2_5": 30, "pm10": 50, "temperature": 25, "humidity": 50},
        "variation": {"pm2_5": 12, "pm10": 18, "temperature": 3, "humidity": 5},
        "pollution_factor": 1.5,
        "mobile_patterns": True  
    },
    "sensor-wearable-1": {
        "type": "Wearable",
        "location": "Cyclist / Pedestrian",
        "baselines": {"pm2_5": 20, "pm10": 30, "temperature": 24, "humidity": 55},
        "variation": {"pm2_5": 8, "pm10": 12, "temperature": 2, "humidity": 4},
        "pollution_factor": 1.2,
        "mobile_patterns": True 
    },
    "sensor-drone-1": {
        "type": "Drone",
        "location": "Aerial / City Monitoring",
        "baselines": {"pm2_5": 25, "pm10": 40, "co": 0.8, "no2": 20, "o3": 15, "temperature": 22, "humidity": 50},
        "variation": {"pm2_5": 10, "pm10": 12, "co": 0.2, "no2": 5, "o3": 5, "temperature": 2, "humidity": 5},
        "pollution_factor": 1.3,
        "mobile_patterns": True,  
        "flight_patterns": True  
}
}

def diurnal_variation(base: float, amplitude: float, hour: int) -> float:
    """Generate diurnal (daily) variation patterns"""
    return base + amplitude * math.sin((2 * math.pi / 24) * hour)

def traffic_pattern(hour: int) -> float:
    """Simulate traffic-related pollution patterns"""
    # Morning rush hour (7-9 AM)
    if 7 <= hour <= 9:
        return 1.8
    # Evening rush hour (5-7 PM)
    elif 17 <= hour <= 19:
        return 1.6
    # Night time (10 PM - 6 AM)
    elif hour >= 22 or hour <= 6:
        return 0.4
    # Regular daytime
    else:
        return 1.0

def industrial_cycle(hour: int) -> float:
    """Simulate industrial activity cycles"""
    # Shift changes and peak production hours
    if 6 <= hour <= 14:  # Morning shift
        return 1.5
    elif 14 <= hour <= 22:  # Afternoon shift
        return 1.3
    elif 22 <= hour <= 6:  # Night shift (reduced)
        return 0.7
    else:
        return 1.0
    
def linear_scale(value, low, high, aqi_low, aqi_high):
    """Linear interpolation for AQI calculation"""
    return int(((value - low) / (high - low)) * (aqi_high - aqi_low) + aqi_low)
    
# AQI calculation functions
def calculate_aqi(pm25, pm10):
    """Calculate Air Quality Index based on PM2.5 and PM10 values"""
    # PM2.5 AQI calculation (EPA standard)
    if pm25 <= 12.0:
        aqi_pm25 = linear_scale(pm25, 0, 12.0, 0, 50)
    elif pm25 <= 35.4:
        aqi_pm25 = linear_scale(pm25, 12.1, 35.4, 51, 100)
    elif pm25 <= 55.4:
        aqi_pm25 = linear_scale(pm25, 35.5, 55.4, 101, 150)
    elif pm25 <= 150.4:
        aqi_pm25 = linear_scale(pm25, 55.5, 150.4, 151, 200)
    elif pm25 <= 250.4:
        aqi_pm25 = linear_scale(pm25, 150.5, 250.4, 201, 300)
    else:
        aqi_pm25 = linear_scale(pm25, 250.5, 500.4, 301, 500)
    
    # PM10 AQI calculation
    if pm10 <= 54:
        aqi_pm10 = linear_scale(pm10, 0, 54, 0, 50)
    elif pm10 <= 154:
        aqi_pm10 = linear_scale(pm10, 55, 154, 51, 100)
    elif pm10 <= 254:
        aqi_pm10 = linear_scale(pm10, 155, 254, 101, 150)
    elif pm10 <= 354:
        aqi_pm10 = linear_scale(pm10, 255, 354, 151, 200)
    elif pm10 <= 424:
        aqi_pm10 = linear_scale(pm10, 355, 424, 201, 300)
    else:
        aqi_pm10 = linear_scale(pm10, 425, 604, 301, 500)
    
    # Return the higher AQI value
    return max(aqi_pm25, aqi_pm10)

def get_aqi_category(aqi):
    """Get AQI category and health risk"""
    if aqi <= 50:
        return "Good", "🟢 Air quality is satisfactory"
    elif aqi <= 100:
        return "Moderate", "🟡 Some pollutants may be a concern"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "🟠 Sensitive groups may experience health effects"
    elif aqi <= 200:
        return "Unhealthy", "🔴 Everyone may begin to experience health effects"
    elif aqi <= 300:
        return "Very Unhealthy", "🟣 Health warnings of emergency conditions"
    else:
        return "Hazardous", "⚫ Health alert: everyone may experience serious health effects"
    
def generate_reading(sensor_id: str, sensor_config: dict):
    now = datetime.utcnow()
    hour = now.hour
    baselines = sensor_config["baselines"]
    variations = sensor_config["variation"]
    pollution_factor = sensor_config["pollution_factor"]

    # PM and environmental calculations...
    pm2_5 = max(0, round(random.gauss(baselines["pm2_5"]*pollution_factor, variations["pm2_5"]), 2))
    pm10 = max(0, round(random.gauss(baselines["pm10"]*pollution_factor, variations["pm10"]), 2))
    temperature = round(random.gauss(baselines["temperature"], variations["temperature"]), 2)
    humidity = round(random.gauss(baselines["humidity"], variations["humidity"]), 2)
    
    aqi = calculate_aqi(pm2_5, pm10)
    category, health_message = get_aqi_category(aqi)

    # Simulated additional fields
    latitude = sensor_config.get("latitude", round(random.uniform(-90, 90), 6))
    longitude = sensor_config.get("longitude", round(random.uniform(-180, 180), 6))
    visibility_meters = round(random.uniform(200, 10000), 2)
    weather_condition = random.choice(["Clear", "Cloudy", "Rain", "Fog"])
    pressure_hpa = round(random.uniform(980, 1050), 2)

    return {
        "sensor_id": sensor_id,
        "timestamp": now.isoformat(),
        "location_name": sensor_config["location"],
        "area_type": sensor_config["type"],
        "latitude": latitude,
        "longitude": longitude,
        "pm2_5": pm2_5,
        "pm10": pm10,
        "aqi": calculate_aqi(pm2_5, pm10),
        "health_risk": health_message,
        "visibility_meters": visibility_meters,
        "temperature": temperature,
        "humidity": humidity,
        "weather_condition": weather_condition,
        "pressure_hpa": pressure_hpa
        }


def send_sensor_data(sensor_id: str, sensor_config: dict):
    """Send data for a specific sensor with detailed logging"""
    while True:
        try:
            reading = generate_reading(sensor_id, sensor_config)
            response = requests.post(f"{API_URL}/{sensor_id}", json=reading)
            
            timestamp = datetime.utcnow().isoformat()
            
            if response.status_code == 200:
                print(f"[{timestamp}] ✅ SUCCESS - {sensor_config['type']} Sensor ({sensor_id}) sent data")
                print(f"    Data: PM2.5={reading['pm2_5']}, PM10={reading['pm10']}, "
                    f"Location={reading['location_name']}, AQI={reading['aqi']}, "
                    f"Health Risk=({reading['health_risk']}), "
                    f"Temp={reading['temperature']}°C, Humidity={reading['humidity']}%")

            else:
                print(f"[{timestamp}] ❌ ERROR - {sensor_config['type']} Sensor ({sensor_id}) HTTP {response.status_code}")
                print(f"    Payload: {reading}")
                
        except requests.exceptions.RequestException as req_err:
            print(f"[{datetime.utcnow().isoformat()}] ❌ REQUEST ERROR - {sensor_id}: {req_err}")
        except Exception as e:
            print(f"[{datetime.utcnow().isoformat()}] ❌ GENERAL ERROR - {sensor_id}: {e}")
        
        # Set sleep interval based on sensor type
        if sensor_config["type"] == "Industrial":
            time.sleep(20)
        elif sensor_config["type"] == "Urban":
            time.sleep(25)
        else:
            time.sleep(30)


def main():
    """Main function to start all sensors"""
    print("🌬️  Multi-Sensor Air Quality Simulator Starting...")
    print("=" * 60)
    
    # Display sensor information
    for sensor_id, config in SENSORS.items():
        print(f"📡 {config['type']} Sensor: {sensor_id}")
        print(f"   Location: {config['location']}")
        print(f"   Pollution Factor: {config['pollution_factor']}x")
        print(f"   Update Frequency: {20 if config['type'] == 'Industrial' else 25 if config['type'] == 'Urban' else 30}s")
        print()
    
    print("🚀 Starting all sensors...")
    print("Press Ctrl+C to stop all sensors")
    print("=" * 60)
    
    # Start each sensor in a separate thread
    threads = []
    for sensor_id, config in SENSORS.items():
        thread = threading.Thread(
            target=send_sensor_data,
            args=(sensor_id, config),
            daemon=True,
            name=f"Sensor-{sensor_id}"
        )
        thread.start()
        threads.append(thread)
        print(f"✅ Started {config['type']} sensor: {sensor_id}")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
            # Check if all threads are still running
            alive_threads = [t for t in threads if t.is_alive()]
            if len(alive_threads) < len(threads):
                print("⚠️  Some sensor threads have stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down sensors...")
        print("✅ All sensor threads stopped")

if __name__ == "__main__":
    main()
