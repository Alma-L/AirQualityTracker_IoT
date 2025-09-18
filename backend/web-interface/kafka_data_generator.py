#!/usr/bin/env python3
"""
Kafka Data Generator for Air Quality IoT Sensors
Generates realistic sensor data and sends it to Kafka for Spark Streaming processing
"""

import json
import random
import time
import logging
from datetime import datetime, timedelta
from kafka import KafkaProducer
import threading
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityDataGenerator:
    def __init__(self):
        self.kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
        self.kafka_topic = os.environ.get('KAFKA_TOPIC', 'air-quality-data')
        self.producer = None
        self.is_running = False
        
        # Sensor configurations
        self.sensors = [
            {
                "sensor_id": "sensor-urban-001",
                "location": {
                    "lat": 42.6629,
                    "lon": 21.1655,
                    "name": "Prishtina City Center",
                    "area_type": "urban",
                    "city": "Prishtina"
                },
                "base_pm25": 25.0,
                "base_pm10": 40.0,
                "base_temp": 20.0,
                "base_humidity": 60.0
            },
            {
                "sensor_id": "sensor-industrial-002",
                "location": {
                    "lat": 42.6500,
                    "lon": 21.1500,
                    "name": "Industrial Zone",
                    "area_type": "industrial",
                    "city": "Prishtina"
                },
                "base_pm25": 45.0,
                "base_pm10": 70.0,
                "base_temp": 22.0,
                "base_humidity": 55.0
            },
            {
                "sensor_id": "sensor-residential-003",
                "location": {
                    "lat": 42.6800,
                    "lon": 21.1800,
                    "name": "Residential Area",
                    "area_type": "residential",
                    "city": "Prishtina"
                },
                "base_pm25": 15.0,
                "base_pm10": 25.0,
                "base_temp": 19.0,
                "base_humidity": 65.0
            },
            {
                "sensor_id": "sensor-mobile-004",
                "location": {
                    "lat": 42.6600,
                    "lon": 21.1700,
                    "name": "Bus Route",
                    "area_type": "mobile",
                    "city": "Prishtina"
                },
                "base_pm25": 30.0,
                "base_pm10": 50.0,
                "base_temp": 21.0,
                "base_humidity": 58.0
            },
            {
                "sensor_id": "sensor-wearable-005",
                "location": {
                    "lat": 42.6700,
                    "lon": 21.1600,
                    "name": "Pedestrian Zone",
                    "area_type": "wearable",
                    "city": "Prishtina"
                },
                "base_pm25": 20.0,
                "base_pm10": 35.0,
                "base_temp": 20.5,
                "base_humidity": 62.0
            },
            {
                "sensor_id": "sensor-drone-006",
                "location": {
                    "lat": 42.6400,
                    "lon": 21.1400,
                    "name": "Aerial Survey",
                    "area_type": "drone",
                    "city": "Prishtina"
                },
                "base_pm25": 18.0,
                "base_pm10": 30.0,
                "base_temp": 18.5,
                "base_humidity": 68.0
            }
        ]
        
        # Weather conditions
        self.weather_conditions = [
            "Clear", "Partly Cloudy", "Cloudy", "Rainy", "Foggy", "Windy"
        ]
        
        # Health risk messages
        self.health_risks = {
            "Good": "Air quality is satisfactory",
            "Moderate": "Some pollutants may be a concern for sensitive groups",
            "Unhealthy for Sensitive Groups": "Sensitive groups may experience health effects",
            "Unhealthy": "Everyone may begin to experience health effects",
            "Very Unhealthy": "Health warnings of emergency conditions",
            "Hazardous": "Health alert: everyone may experience serious health effects"
        }
    
    def connect_kafka(self):
        """Connect to Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.kafka_broker],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10,
                buffer_memory=33554432
            )
            logger.info(f"✅ Connected to Kafka at {self.kafka_broker}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            return False
    
    def calculate_aqi(self, pm25, pm10):
        """Calculate Air Quality Index based on PM2.5 and PM10"""
        # PM2.5 AQI calculation
        if pm25 <= 12.0:
            aqi_pm25 = ((pm25 - 0) / (12.0 - 0)) * (50 - 0) + 0
        elif pm25 <= 35.4:
            aqi_pm25 = ((pm25 - 12.1) / (35.4 - 12.1)) * (100 - 51) + 51
        elif pm25 <= 55.4:
            aqi_pm25 = ((pm25 - 35.5) / (55.4 - 35.5)) * (150 - 101) + 101
        elif pm25 <= 150.4:
            aqi_pm25 = ((pm25 - 55.5) / (150.4 - 55.5)) * (200 - 151) + 151
        elif pm25 <= 250.4:
            aqi_pm25 = ((pm25 - 150.5) / (250.4 - 150.5)) * (300 - 201) + 201
        else:
            aqi_pm25 = ((pm25 - 250.5) / (500.4 - 250.5)) * (500 - 301) + 301
        
        # PM10 AQI calculation
        if pm10 <= 54:
            aqi_pm10 = ((pm10 - 0) / (54 - 0)) * (50 - 0) + 0
        elif pm10 <= 154:
            aqi_pm10 = ((pm10 - 55) / (154 - 55)) * (100 - 51) + 51
        elif pm10 <= 254:
            aqi_pm10 = ((pm10 - 155) / (254 - 155)) * (150 - 101) + 101
        elif pm10 <= 354:
            aqi_pm10 = ((pm10 - 255) / (354 - 255)) * (200 - 151) + 151
        elif pm10 <= 424:
            aqi_pm10 = ((pm10 - 355) / (424 - 355)) * (300 - 201) + 201
        else:
            aqi_pm10 = ((pm10 - 425) / (604 - 425)) * (500 - 301) + 301
        
        return max(int(aqi_pm25), int(aqi_pm10))
    
    def get_aqi_category(self, aqi):
        """Get AQI category and health risk"""
        if aqi <= 50:
            return "Good", self.health_risks["Good"]
        elif aqi <= 100:
            return "Moderate", self.health_risks["Moderate"]
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups", self.health_risks["Unhealthy for Sensitive Groups"]
        elif aqi <= 200:
            return "Unhealthy", self.health_risks["Unhealthy"]
        elif aqi <= 300:
            return "Very Unhealthy", self.health_risks["Very Unhealthy"]
        else:
            return "Hazardous", self.health_risks["Hazardous"]
    
    def generate_sensor_data(self, sensor_config):
        """Generate realistic sensor data for a specific sensor"""
        # Add some randomness and trends
        time_factor = time.time() / 3600  # Hour-based variation
        
        # Simulate daily patterns
        hour = datetime.now().hour
        if 6 <= hour <= 8:  # Morning rush
            traffic_factor = 1.5
        elif 17 <= hour <= 19:  # Evening rush
            traffic_factor = 1.3
        elif 22 <= hour or hour <= 5:  # Night
            traffic_factor = 0.7
        else:
            traffic_factor = 1.0
        
        # Generate PM2.5 with realistic variations
        pm25 = sensor_config["base_pm25"] * traffic_factor * (1 + random.uniform(-0.3, 0.3))
        pm25 = max(0, pm25)
        
        # Generate PM10 (usually higher than PM2.5)
        pm10 = sensor_config["base_pm10"] * traffic_factor * (1 + random.uniform(-0.3, 0.3))
        pm10 = max(pm25, pm10)  # PM10 should be >= PM2.5
        
        # Calculate AQI
        aqi = self.calculate_aqi(pm25, pm10)
        aqi_category, health_risk = self.get_aqi_category(aqi)
        
        # Generate environmental data
        temperature = sensor_config["base_temp"] + random.uniform(-5, 5) + (time_factor % 24 - 12) * 0.5
        humidity = sensor_config["base_humidity"] + random.uniform(-10, 10)
        humidity = max(0, min(100, humidity))
        
        # Generate additional pollutants
        co2 = 400 + random.uniform(0, 100) + traffic_factor * 50
        no2 = random.uniform(10, 50) * traffic_factor
        o3 = random.uniform(20, 80) * (1 + random.uniform(-0.2, 0.2))
        
        # Generate sensor metadata
        battery_level = max(0, 100 - (time_factor * 0.1))  # Gradual battery drain
        signal_strength = random.uniform(70, 100)
        
        # Create the data structure (flattened for Cassandra schema)
        data = {
            "sensor_id": sensor_config["sensor_id"],
            "timestamp": datetime.now().isoformat(),
            # Flatten location data
            "location_name": sensor_config["location"]["name"],
            "area_type": sensor_config["location"]["area_type"],
            "latitude": sensor_config["location"]["lat"],
            "longitude": sensor_config["location"]["lon"],
            # Flatten air quality data
            "pm2_5": round(pm25, 2),
            "pm10": round(pm10, 2),
            "aqi": aqi,
            "health_risk": health_risk,
            "visibility_meters": max(100, int(10000 - pm10 * 50)),
            # Flatten environmental data
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "weather_condition": random.choice(self.weather_conditions),
            "pressure_hpa": round(1013 + random.uniform(-20, 20), 2),
            "wind_speed": round(random.uniform(0, 15), 2),
            "wind_direction": random.uniform(0, 360),
            # Additional fields for compatibility
            "co2": round(co2, 2),
            "no2": round(no2, 2),
            "o3": round(o3, 2),
            "battery_level": round(battery_level, 2),
            "signal_strength": round(signal_strength, 2),
            "firmware_version": "2.1.0",
            "last_calibration": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        }
        
        return data
    
    def send_data_to_kafka(self, data):
        """Send data to Kafka topic"""
        try:
            self.producer.send(
                self.kafka_topic,
                key=data["sensor_id"],
                value=data
            )
            logger.debug(f"📤 Sent data for {data['sensor_id']} to Kafka")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send data to Kafka: {e}")
            return False
    
    def generate_and_send_data(self):
        """Generate data for all sensors and send to Kafka"""
        for sensor_config in self.sensors:
            try:
                data = self.generate_sensor_data(sensor_config)
                self.send_data_to_kafka(data)
            except Exception as e:
                logger.error(f"❌ Error generating data for {sensor_config['sensor_id']}: {e}")
    
    def start_generation(self, interval_seconds=5):
        """Start generating data at specified intervals"""
        if not self.connect_kafka():
            return False
        
        self.is_running = True
        logger.info(f"🚀 Starting data generation every {interval_seconds} seconds")
        logger.info(f"📊 Generating data for {len(self.sensors)} sensors")
        logger.info(f"🎯 Sending to topic: {self.kafka_topic}")
        
        try:
            while self.is_running:
                self.generate_and_send_data()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ Error in data generation: {e}")
        finally:
            self.stop_generation()
        
        return True
    
    def stop_generation(self):
        """Stop data generation"""
        self.is_running = False
        if self.producer:
            self.producer.close()
        logger.info("🛑 Data generation stopped")
    
    def run(self, interval_seconds=5):
        """Main method to run the data generator"""
        return self.start_generation(interval_seconds)

if __name__ == "__main__":
    generator = AirQualityDataGenerator()
    generator.run(interval_seconds=3)  # Generate data every 3 seconds
