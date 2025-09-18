#!/usr/bin/env python3
"""
Simple Working Processor for Air Quality IoT Data Processing
Windows-compatible solution using direct processing without complex Spark operations
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from kafka import KafkaConsumer
from cassandra.cluster import Cluster
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleWorkingProcessor:
    def __init__(self):
        # Configuration
        self.kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
        self.kafka_topic = os.environ.get('KAFKA_TOPIC', 'air-quality-data')
        self.cassandra_host = os.environ.get('CASSANDRA_HOST', 'localhost')
        
        # Connections
        self.kafka_consumer = None
        self.cassandra_session = None
        self.is_running = False
        
        # Processing statistics
        self.stats = {
            'total_records_processed': 0,
            'valid_records': 0,
            'invalid_records': 0,
            'aggregations_computed': 0,
            'alerts_generated': 0,
            'start_time': None
        }
        
        # Data buffer for batch processing
        self.data_buffer = []
        self.batch_size = 50
        
        # Sensor data history for aggregations
        self.sensor_history = {}
        
    def create_kafka_consumer(self):
        """Create Kafka consumer"""
        try:
            self.kafka_consumer = KafkaConsumer(
                self.kafka_topic,
                bootstrap_servers=[self.kafka_broker],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='simple-working-processor'
            )
            logger.info("✅ Kafka consumer created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create Kafka consumer: {e}")
            return False
    
    def create_cassandra_session(self):
        """Create Cassandra session"""
        try:
            cluster = Cluster([self.cassandra_host])
            self.cassandra_session = cluster.connect()
            logger.info("✅ Cassandra session created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create Cassandra session: {e}")
            return False
    
    def validate_data(self, data):
        """Validate single data record"""
        try:
            # Check required fields
            required_fields = ['sensor_id', 'timestamp', 'pm2_5', 'pm10', 'aqi']
            for field in required_fields:
                if field not in data or data[field] is None:
                    return False, f"Missing field: {field}"
            
            # Validate ranges
            if not (0 <= data['pm2_5'] <= 200):
                return False, f"Invalid PM2.5: {data['pm2_5']}"
            if not (0 <= data['pm10'] <= 300):
                return False, f"Invalid PM10: {data['pm10']}"
            if not (0 <= data['aqi'] <= 500):
                return False, f"Invalid AQI: {data['aqi']}"
            
            return True, "Valid"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def calculate_alert_level(self, aqi):
        """Calculate alert level based on AQI"""
        if aqi >= 300:
            return "Hazardous"
        elif aqi >= 200:
            return "Very Unhealthy"
        elif aqi >= 150:
            return "Unhealthy"
        elif aqi >= 100:
            return "Unhealthy for Sensitive Groups"
        elif aqi >= 50:
            return "Moderate"
        else:
            return "Good"
    
    def calculate_aggregations(self, sensor_id, data):
        """Calculate aggregations for a sensor"""
        if sensor_id not in self.sensor_history:
            self.sensor_history[sensor_id] = []
        
        # Add current data to history
        self.sensor_history[sensor_id].append({
            'timestamp': data['timestamp'],
            'pm2_5': data['pm2_5'],
            'pm10': data['pm10'],
            'aqi': data['aqi'],
            'temperature': data.get('temperature', 0),
            'humidity': data.get('humidity', 0)
        })
        
        # Keep only last 100 records per sensor
        if len(self.sensor_history[sensor_id]) > 100:
            self.sensor_history[sensor_id] = self.sensor_history[sensor_id][-100:]
        
        # Calculate aggregations
        history = self.sensor_history[sensor_id]
        if len(history) >= 2:
            # Calculate averages
            pm25_values = [h['pm2_5'] for h in history[-10:]]  # Last 10 readings
            pm10_values = [h['pm10'] for h in history[-10:]]
            aqi_values = [h['aqi'] for h in history[-10:]]
            
            pm25_avg = np.mean(pm25_values)
            pm10_avg = np.mean(pm10_values)
            aqi_avg = np.mean(aqi_values)
            
            # Calculate anomaly score
            current_pm25 = data['pm2_5']
            pm25_std = np.std(pm25_values)
            anomaly_score = abs(current_pm25 - pm25_avg) / pm25_avg if pm25_avg > 0 else 0
            
            return {
                'pm25_avg': pm25_avg,
                'pm10_avg': pm10_avg,
                'aqi_avg': aqi_avg,
                'pm25_max': max(pm25_values),
                'pm25_min': min(pm25_values),
                'anomaly_score': anomaly_score,
                'is_anomaly': anomaly_score > 0.5
            }
        
        return {
            'pm25_avg': data['pm2_5'],
            'pm10_avg': data['pm10'],
            'aqi_avg': data['aqi'],
            'pm25_max': data['pm2_5'],
            'pm25_min': data['pm2_5'],
            'anomaly_score': 0.0,
            'is_anomaly': False
        }
    
    def process_record(self, data):
        """Process a single data record"""
        try:
            # Validate data
            is_valid, error_msg = self.validate_data(data)
            if not is_valid:
                logger.warning(f"⚠️ Invalid data: {error_msg}")
                self.stats['invalid_records'] += 1
                return False
            
            # Calculate alert level
            alert_level = self.calculate_alert_level(data['aqi'])
            
            # Calculate aggregations
            aggregations = self.calculate_aggregations(data['sensor_id'], data)
            
            # Log processed data
            logger.info(f"📊 Processed: Sensor {data['sensor_id']} - PM2.5: {data['pm2_5']:.2f}, PM10: {data['pm10']:.2f}, AQI: {data['aqi']}, Alert: {alert_level}")
            logger.info(f"   📈 Aggregations: PM2.5 Avg: {aggregations['pm25_avg']:.2f}, Anomaly: {aggregations['anomaly_score']:.3f}")
            
            # Save to Cassandra
            try:
                insert_query = """
                INSERT INTO air_quality_monitoring.air_quality_data 
                (sensor_id, timestamp, location_name, area_type, latitude, longitude, 
                 pm2_5, pm10, aqi, health_risk, visibility_meters, co2, no2, o3, 
                 temperature, humidity, weather_condition, pressure_hpa, wind_speed, 
                 wind_direction, battery_level, signal_strength, firmware_version, last_calibration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                # Prepare data with proper type conversion
                insert_data = (
                    data.get('sensor_id'),
                    data.get('timestamp'),
                    data.get('location_name'),
                    data.get('area_type'),
                    float(data.get('latitude', 0.0)) if data.get('latitude') is not None else None,
                    float(data.get('longitude', 0.0)) if data.get('longitude') is not None else None,
                    float(data.get('pm2_5', 0.0)) if data.get('pm2_5') is not None else None,
                    float(data.get('pm10', 0.0)) if data.get('pm10') is not None else None,
                    int(data.get('aqi', 0)) if data.get('aqi') is not None else None,
                    data.get('health_risk'),
                    int(data.get('visibility_meters', 0)) if data.get('visibility_meters') is not None else None,
                    float(data.get('co2', 0.0)) if data.get('co2') is not None else None,
                    float(data.get('no2', 0.0)) if data.get('no2') is not None else None,
                    float(data.get('o3', 0.0)) if data.get('o3') is not None else None,
                    float(data.get('temperature', 0.0)) if data.get('temperature') is not None else None,
                    float(data.get('humidity', 0.0)) if data.get('humidity') is not None else None,
                    data.get('weather_condition'),
                    float(data.get('pressure_hpa', 0.0)) if data.get('pressure_hpa') is not None else None,
                    float(data.get('wind_speed', 0.0)) if data.get('wind_speed') is not None else None,
                    float(data.get('wind_direction', 0.0)) if data.get('wind_direction') is not None else None,
                    float(data.get('battery_level', 0.0)) if data.get('battery_level') is not None else None,
                    float(data.get('signal_strength', 0.0)) if data.get('signal_strength') is not None else None,
                    data.get('firmware_version'),
                    data.get('last_calibration')
                )
                
                self.cassandra_session.execute(insert_query, insert_data)
                logger.info("✅ Data saved to Cassandra")
                
            except Exception as e:
                logger.warning(f"⚠️ Failed to save to Cassandra: {e}")
            
            # Update statistics
            self.stats['total_records_processed'] += 1
            self.stats['valid_records'] += 1
            if alert_level != "Good":
                self.stats['alerts_generated'] += 1
            if aggregations['is_anomaly']:
                self.stats['aggregations_computed'] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing record: {e}")
            return False
    
    def consume_and_process(self):
        """Main consumer loop"""
        try:
            logger.info("🚀 Starting Kafka consumer with advanced processing...")
            
            for message in self.kafka_consumer:
                if not self.is_running:
                    break
                
                try:
                    # Get message data
                    data = message.value
                    
                    # Process record
                    self.process_record(data)
                    
                    # Log statistics every 10 records
                    if self.stats['total_records_processed'] % 10 == 0:
                        logger.info(f"📈 Statistics: Total: {self.stats['total_records_processed']}, Valid: {self.stats['valid_records']}, Invalid: {self.stats['invalid_records']}, Alerts: {self.stats['alerts_generated']}, Anomalies: {self.stats['aggregations_computed']}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in consumer loop: {e}")
    
    def start_processing(self):
        """Start the processing system"""
        try:
            if not self.create_kafka_consumer():
                return False
            if not self.create_cassandra_session():
                return False
                
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("🎉 Simple Working Processor is running!")
            logger.info("📊 Features enabled:")
            logger.info("   ✅ Kafka consumer")
            logger.info("   ✅ Real-time data validation")
            logger.info("   ✅ Advanced aggregations (sliding windows)")
            logger.info("   ✅ Anomaly detection")
            logger.info("   ✅ Alert level classification")
            logger.info("   ✅ Cassandra storage")
            logger.info("   ✅ Windows compatible")
            logger.info("   ✅ No Spark (simplified but powerful)")
            
            # Start consumer
            self.consume_and_process()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start processing: {e}")
            return False
        finally:
            self.stop_processing()
    
    def stop_processing(self):
        """Stop the processing system"""
        try:
            self.is_running = False
            if self.kafka_consumer:
                self.kafka_consumer.close()
            if self.cassandra_session:
                self.cassandra_session.shutdown()
            logger.info("🛑 Processing system stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping system: {e}")
    
    def run(self):
        """Main method to run the processor"""
        return self.start_processing()

if __name__ == "__main__":
    processor = SimpleWorkingProcessor()
    processor.run()
