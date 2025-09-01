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

def generate_reading(sensor_id: str, sensor_config: dict):
    """Generate realistic reading for a specific sensor"""
    now = datetime.utcnow()
    hour = now.hour
    
    # Get baseline values
    baselines = sensor_config["baselines"]
    variations = sensor_config["variation"]
    pollution_factor = sensor_config["pollution_factor"]
    
    # Apply diurnal variation
    temperature = diurnal_variation(baselines["temperature"], variations["temperature"], hour)
    humidity = diurnal_variation(baselines["humidity"], variations["humidity"], (hour + 6) % 24)
    
    # Base pollution levels
    pm2_5_base = baselines["pm2_5"]
    pm10_base = baselines["pm10"]
    
    # Apply traffic patterns for urban sensors
    if sensor_config.get("traffic_patterns"):
        traffic_multiplier = traffic_pattern(hour)
        pm2_5_base *= traffic_multiplier
        pm10_base *= traffic_multiplier
    
    # Apply industrial cycles for industrial sensors
    if sensor_config.get("industrial_cycles"):
        industrial_multiplier = industrial_cycle(hour)
        pm2_5_base *= industrial_multiplier
        pm10_base *= industrial_multiplier
    
    # Apply daily patterns for residential sensors
    if sensor_config.get("daily_patterns"):
        # Lower pollution during night
        if 22 <= hour or hour <= 6:
            pm2_5_base *= 0.6
            pm10_base *= 0.6
    
    # Add random variation
    pm2_5 = round(random.gauss(pm2_5_base, variations["pm2_5"]), 2)
    pm10 = round(random.gauss(pm10_base, variations["pm10"]), 2)
    temperature = round(random.gauss(temperature, 0.5), 2)
    humidity = round(random.gauss(humidity, 2), 2)
    
    # Apply pollution factor
    pm2_5 *= pollution_factor
    pm10 *= pollution_factor
    
    # Ensure minimum values
    pm2_5 = max(0, pm2_5)
    pm10 = max(0, pm10)
    humidity = max(0, min(100, humidity))
    
    # Occasional pollution spikes (more frequent in industrial areas)
    spike_probability = 0.08 if sensor_config["type"] == "Industrial" else 0.05
    if random.random() < spike_probability:
        spike_intensity = random.uniform(1.5, 3.0)
        pm2_5 *= spike_intensity
        pm10 *= spike_intensity
    
    return {
        "sensor_id": sensor_id,
        "timestamp": now.isoformat(),
        "pm2_5": round(pm2_5, 2),
        "pm10": round(pm10, 2),
        "temperature": temperature,
        "humidity": humidity,
        "sensor_type": sensor_config["type"],
        "location": sensor_config["location"]
    }

def send_sensor_data(sensor_id: str, sensor_config: dict):
    """Send data for a specific sensor"""
    while True:
        try:
            reading = generate_reading(sensor_id, sensor_config)
            response = requests.post(f"{API_URL}/{sensor_id}", json=reading)
            
            if response.status_code == 200:
                print(f"[{datetime.utcnow()}] {sensor_config['type']} Sensor ({sensor_id}): "
                      f"PM2.5={reading['pm2_5']}, PM10={reading['pm10']}, "
                      f"Temp={reading['temperature']}°C, Humidity={reading['humidity']}%")
            else:
                print(f"❌ Error sending data for {sensor_id}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error with {sensor_id}: {e}")
        
        # Different update frequencies for different sensor types
        if sensor_config["type"] == "Industrial":
            time.sleep(20)  # Industrial sensors update every 20 seconds
        elif sensor_config["type"] == "Urban":
            time.sleep(25)  # Urban sensors update every 25 seconds
        else:
            time.sleep(30)  # Residential sensors update every 30 seconds

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
