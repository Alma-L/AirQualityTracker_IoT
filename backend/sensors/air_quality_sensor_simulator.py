import json
import time
import random
import os
import logging
from datetime import datetime
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualitySensorSimulator:
    def __init__(self):
        self.kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
        self.sensor_count = int(os.environ.get('SENSOR_COUNT', 50))
        self.update_interval = int(os.environ.get('UPDATE_INTERVAL', 30))
        self.location = os.environ.get('LOCATION', 'kosovo')
        
        # Initialize Kafka producer
        self.producer = None
        self.connect_to_kafka()
        
        # Define sensor locations around Kosovo (Prishtina region)
        # Prishtina center: 42.6629° N, 21.1655° E
        self.sensor_locations = [
            {"id": f"AQ_SENSOR_{i:03d}", 
             "lat": 42.6629 + random.uniform(-0.05, 0.05),  # ~5km radius around Prishtina
             "lon": 21.1655 + random.uniform(-0.05, 0.05), 
             "location_name": f"Location_{i}", 
             "area_type": random.choice(['urban', 'industrial', 'residential', 'rural'])}
            for i in range(1, self.sensor_count + 1)
        ]
        
    def connect_to_kafka(self):
        """Connect to Kafka with retry logic"""
        max_retries = 10
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.kafka_broker,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    key_serializer=lambda k: k.encode('utf-8') if k else None
                )
                logger.info(f"Connected to Kafka broker at {self.kafka_broker}")
                return
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to connect to Kafka (attempt {retry_count}/{max_retries}): {e}")
                time.sleep(5)
        
        raise Exception("Failed to connect to Kafka after maximum retries")
    
    def generate_air_quality_data(self, sensor):
        """Generate realistic air quality data for a sensor"""
        current_hour = datetime.now().hour
        current_minute = datetime.now().minute
        
        # Base air quality based on area type
        area_type = sensor.get('area_type', 'urban')
        if area_type == 'industrial':
            base_pm2_5 = random.uniform(30, 60)
            base_pm10 = random.uniform(50, 100)
        elif area_type == 'urban':
            base_pm2_5 = random.uniform(20, 40)
            base_pm10 = random.uniform(35, 70)
        elif area_type == 'residential':
            base_pm2_5 = random.uniform(15, 30)
            base_pm10 = random.uniform(25, 50)
        else:  # rural
            base_pm2_5 = random.uniform(8, 20)
            base_pm10 = random.uniform(15, 35)
        
        # Time-based variations (rush hour, industrial activity)
        if 7 <= current_hour <= 9 or 17 <= current_hour <= 19:  # Rush hours
            base_pm2_5 *= 1.3
            base_pm10 *= 1.4
        elif 22 <= current_hour or current_hour <= 6:  # Night time
            base_pm2_5 *= 0.7
            base_pm10 *= 0.8
        
        # Add some randomness and occasional pollution spikes
        if random.random() < 0.05:  # 5% chance of pollution spike
            base_pm2_5 *= random.uniform(2.0, 4.0)
            base_pm10 *= random.uniform(2.0, 4.0)
        
        # Generate final values with realistic variations
        pm2_5 = max(0, round(base_pm2_5 + random.gauss(0, 5), 2))
        pm10 = max(0, round(base_pm10 + random.gauss(0, 8), 2))
        
        # Generate environmental data with realistic patterns
        temperature = round(15 + random.uniform(-8, 15), 1)
        humidity = round(40 + random.uniform(-20, 40), 1)
        
        # Weather conditions with time-based patterns
        if 6 <= current_hour <= 18:  # Daytime
            weather_conditions = ["clear", "cloudy", "clear", "cloudy", "clear"]
        else:  # Nighttime
            weather_conditions = ["clear", "cloudy", "fog", "clear"]
        
        weather_condition = random.choice(weather_conditions)
        
        # Visibility based on weather and air quality
        if weather_condition == "fog":
            visibility = random.choice([200, 500, 800])
        elif weather_condition == "light_rain":
            visibility = random.choice([1000, 2000, 3000])
        else:
            visibility = random.choice([5000, 8000, 10000])
        
        # Adjust visibility based on air quality
        if pm2_5 > 35:  # Poor air quality
            visibility = max(500, visibility * 0.7)
        
        # Calculate AQI (Air Quality Index)
        aqi = self.calculate_aqi(pm2_5, pm10)
        health_risk = self.get_health_risk(aqi)
        
        return {
            "sensor_id": sensor["id"],
            "timestamp": datetime.now().isoformat(),
            "location": {
                "lat": sensor["lat"],
                "lon": sensor["lon"],
                "name": sensor["location_name"],
                "area_type": sensor["area_type"]
            },
            "air_quality_data": {
                "pm2_5": pm2_5,
                "pm10": pm10,
                "aqi": aqi,
                "health_risk": health_risk,
                "visibility_meters": visibility
            },
            "environmental_data": {
                "temperature_celsius": temperature,
                "humidity_percent": humidity,
                "weather_condition": weather_condition,
                "pressure_hpa": round(1013 + random.uniform(-20, 20), 1)
            }
        }
    
    def calculate_aqi(self, pm2_5, pm10):
        """Calculate Air Quality Index based on PM2.5 and PM10"""
        # Simplified AQI calculation
        if pm2_5 <= 12 and pm10 <= 54:
            return "Good"
        elif pm2_5 <= 35.4 and pm10 <= 154:
            return "Moderate"
        elif pm2_5 <= 55.4 and pm10 <= 254:
            return "Unhealthy for Sensitive Groups"
        elif pm2_5 <= 150.4 and pm10 <= 354:
            return "Unhealthy"
        elif pm2_5 <= 250.4 and pm10 <= 424:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def get_health_risk(self, aqi):
        """Get health risk level based on AQI"""
        risk_levels = {
            "Good": "Low",
            "Moderate": "Low",
            "Unhealthy for Sensitive Groups": "Medium",
            "Unhealthy": "High",
            "Very Unhealthy": "Very High",
            "Hazardous": "Extreme"
        }
        return risk_levels.get(aqi, "Unknown")
    
    def send_to_kafka(self, data):
        """Send data to Kafka topic"""
        try:
            self.producer.send(
                'air-quality-data',
                key=data['sensor_id'],
                value=data
            )
            logger.info(f"Sent data from sensor {data['sensor_id']}")
        except Exception as e:
            logger.error(f"Error sending data to Kafka: {e}")
    
    def run(self):
        """Main simulation loop"""
        logger.info(f"Starting air quality sensor simulation with {self.sensor_count} sensors")
        
        while True:
            try:
                # Generate and send data for each sensor
                for sensor in self.sensor_locations:
                    air_quality_data = self.generate_air_quality_data(sensor)
                    self.send_to_kafka(air_quality_data)
                
                # Flush to ensure data is sent
                self.producer.flush()
                
                # Wait before next update
                time.sleep(self.update_interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down sensor simulator")
                break
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                time.sleep(5)
        
        if self.producer:
            self.producer.close()

if __name__ == "__main__":
    simulator = AirQualitySensorSimulator()
    simulator.run()
