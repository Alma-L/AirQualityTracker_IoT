#!/usr/bin/env python3
"""
Working Spark Processor for Air Quality IoT Data Processing
Windows-compatible solution using Spark batch processing with Kafka
"""

import os
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window
from kafka import KafkaConsumer
from cassandra.cluster import Cluster

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkingSparkProcessor:
    def __init__(self):
        # Configuration
        self.kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
        self.kafka_topic = os.environ.get('KAFKA_TOPIC', 'air-quality-data')
        self.cassandra_host = os.environ.get('CASSANDRA_HOST', 'localhost')
        self.spark_master = os.environ.get('SPARK_MASTER', 'local[*]')
        
        # Spark session
        self.spark = None
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
        
    def create_spark_session(self):
        """Create Spark session with Windows-optimized configuration"""
        try:
            # Get the correct Python path
            import sys
            python_path = sys.executable
            
            self.spark = SparkSession.builder \
                .appName("WorkingSparkProcessor") \
                .master(self.spark_master) \
                .config("spark.jars.packages", 
                        "com.datastax.spark:spark-cassandra-connector_2.12:3.4.0") \
                .config("spark.cassandra.connection.host", self.cassandra_host) \
                .config("spark.cassandra.connection.port", "9042") \
                .config("spark.sql.adaptive.enabled", "false") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "false") \
                .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
                .config("spark.sql.adaptive.skewJoin.enabled", "false") \
                .config("spark.sql.adaptive.localShuffleReader.enabled", "false") \
                .config("spark.pyspark.python", python_path) \
                .config("spark.pyspark.driver.python", python_path) \
                .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("WARN")
            logger.info("✅ Working Spark session created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create Spark session: {e}")
            return False
    
    def create_kafka_consumer(self):
        """Create Kafka consumer"""
        try:
            self.kafka_consumer = KafkaConsumer(
                self.kafka_topic,
                bootstrap_servers=[self.kafka_broker],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='working-spark-processor'
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
    
    def get_air_quality_schema(self):
        """Define comprehensive schema for air quality data"""
        return StructType([
            StructField("sensor_id", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("location_name", StringType(), True),
            StructField("area_type", StringType(), True),
            StructField("latitude", DoubleType(), True),
            StructField("longitude", DoubleType(), True),
            StructField("pm2_5", DoubleType(), True),
            StructField("pm10", DoubleType(), True),
            StructField("aqi", IntegerType(), True),
            StructField("health_risk", StringType(), True),
            StructField("visibility_meters", IntegerType(), True),
            StructField("co2", DoubleType(), True),
            StructField("no2", DoubleType(), True),
            StructField("o3", DoubleType(), True),
            StructField("temperature", DoubleType(), True),
            StructField("humidity", DoubleType(), True),
            StructField("weather_condition", StringType(), True),
            StructField("pressure_hpa", DoubleType(), True),
            StructField("wind_speed", DoubleType(), True),
            StructField("wind_direction", DoubleType(), True),
            StructField("battery_level", DoubleType(), True),
            StructField("signal_strength", DoubleType(), True),
            StructField("firmware_version", StringType(), True),
            StructField("last_calibration", StringType(), True)
        ])
    
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
    
    def process_batch_with_spark(self, data_batch):
        """Process a batch of data using Spark"""
        try:
            if not data_batch:
                return
            
            logger.info(f"🔄 Processing batch with {len(data_batch)} records using Spark")
            
            # Clean and convert data types before creating DataFrame
            cleaned_batch = []
            for data in data_batch:
                cleaned_data = {}
                for key, value in data.items():
                    if value is None:
                        cleaned_data[key] = None
                    elif key in ['latitude', 'longitude', 'pm2_5', 'pm10', 'co2', 'no2', 'o3', 
                                'temperature', 'humidity', 'pressure_hpa', 'wind_speed', 
                                'wind_direction', 'battery_level', 'signal_strength']:
                        # Convert to float
                        try:
                            cleaned_data[key] = float(value) if value is not None else None
                        except (ValueError, TypeError):
                            cleaned_data[key] = None
                    elif key in ['aqi', 'visibility_meters']:
                        # Convert to int
                        try:
                            cleaned_data[key] = int(value) if value is not None else None
                        except (ValueError, TypeError):
                            cleaned_data[key] = None
                    else:
                        # Keep as string
                        cleaned_data[key] = str(value) if value is not None else None
                cleaned_batch.append(cleaned_data)
            
            # Create DataFrame from cleaned batch data
            df = self.spark.createDataFrame(cleaned_batch, self.get_air_quality_schema())
            
            # Validate data
            validated_df = df.filter(
                (col("pm2_5").isNotNull()) &
                (col("pm10").isNotNull()) &
                (col("aqi").isNotNull()) &
                (col("pm2_5") >= 0) &
                (col("pm10") >= 0) &
                (col("aqi") >= 0) &
                (col("aqi") <= 500)
            )
            
            # Add aggregations using Spark
            window_spec = Window.partitionBy("sensor_id").orderBy("timestamp")
            
            aggregated_df = validated_df.withColumn("pm25_avg", 
                avg("pm2_5").over(window_spec)) \
                .withColumn("pm10_avg", 
                avg("pm10").over(window_spec)) \
                .withColumn("aqi_avg", 
                avg("aqi").over(window_spec)) \
                .withColumn("pm25_max", 
                max("pm2_5").over(window_spec)) \
                .withColumn("pm25_min", 
                min("pm2_5").over(window_spec)) \
                .withColumn("alert_level", 
                    when(col("aqi") >= 200, "Very Unhealthy") \
                    .when(col("aqi") >= 150, "Unhealthy") \
                    .when(col("aqi") >= 100, "Unhealthy for Sensitive Groups") \
                    .when(col("aqi") >= 50, "Moderate") \
                    .otherwise("Good")
                ) \
                .withColumn("anomaly_score", 
                    abs(col("pm2_5") - col("pm25_avg")) / col("pm25_avg")
                ) \
                .withColumn("is_anomaly", 
                    col("anomaly_score") > 0.5
                )
            
            # Show results
            logger.info("📊 Spark processed data:")
            aggregated_df.select("sensor_id", "timestamp", "pm2_5", "pm10", "aqi", "alert_level", "anomaly_score") \
                .show(20, truncate=False)
            
            # Save to Cassandra using Spark
            try:
                aggregated_df.write \
                    .format("org.apache.spark.sql.cassandra") \
                    .mode("append") \
                    .options(table="air_quality_data", keyspace="air_quality_monitoring") \
                    .save()
                logger.info("✅ Data saved to Cassandra via Spark")
            except Exception as e:
                logger.warning(f"⚠️ Failed to save to Cassandra via Spark: {e}")
                # Fallback to direct Cassandra insertion
                self.save_to_cassandra_direct(aggregated_df.collect())
            
            # Update statistics
            record_count = aggregated_df.count()
            self.stats['total_records_processed'] += record_count
            self.stats['valid_records'] += record_count
            self.stats['aggregations_computed'] += 1
            
            logger.info(f"✅ Spark batch processed successfully: {record_count} records")
            logger.info(f"📈 Total processed: {self.stats['total_records_processed']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing batch with Spark: {e}")
    
    def save_to_cassandra_direct(self, records):
        """Fallback method to save records directly to Cassandra"""
        try:
            insert_query = """
            INSERT INTO air_quality_monitoring.air_quality_data 
            (sensor_id, timestamp, location_name, area_type, latitude, longitude, 
             pm2_5, pm10, aqi, health_risk, visibility_meters, co2, no2, o3, 
             temperature, humidity, weather_condition, pressure_hpa, wind_speed, 
             wind_direction, battery_level, signal_strength, firmware_version, last_calibration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for record in records:
                insert_data = (
                    record['sensor_id'],
                    record['timestamp'],
                    record['location_name'],
                    record['area_type'],
                    record['latitude'],
                    record['longitude'],
                    record['pm2_5'],
                    record['pm10'],
                    record['aqi'],
                    record['health_risk'],
                    record['visibility_meters'],
                    record['co2'],
                    record['no2'],
                    record['o3'],
                    record['temperature'],
                    record['humidity'],
                    record['weather_condition'],
                    record['pressure_hpa'],
                    record['wind_speed'],
                    record['wind_direction'],
                    record['battery_level'],
                    record['signal_strength'],
                    record['firmware_version'],
                    record['last_calibration']
                )
                
                self.cassandra_session.execute(insert_query, insert_data)
            
            logger.info("✅ Data saved to Cassandra via direct connection")
            
        except Exception as e:
            logger.error(f"❌ Failed to save to Cassandra directly: {e}")
    
    def consume_and_process(self):
        """Main consumer loop"""
        try:
            logger.info("🚀 Starting Kafka consumer with Spark processing...")
            
            for message in self.kafka_consumer:
                if not self.is_running:
                    break
                
                try:
                    # Get message data
                    data = message.value
                    
                    # Validate data
                    is_valid, error_msg = self.validate_data(data)
                    if not is_valid:
                        logger.warning(f"⚠️ Invalid data: {error_msg}")
                        self.stats['invalid_records'] += 1
                        continue
                    
                    # Add to buffer
                    self.data_buffer.append(data)
                    
                    # Process batch when buffer is full
                    if len(self.data_buffer) >= self.batch_size:
                        self.process_batch_with_spark(self.data_buffer)
                        self.data_buffer = []
                    
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Error in consumer loop: {e}")
    
    def start_processing(self):
        """Start the processing system"""
        try:
            if not self.create_spark_session():
                return False
            if not self.create_kafka_consumer():
                return False
            if not self.create_cassandra_session():
                return False
                
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("🎉 Working Spark Processor is running!")
            logger.info("📊 Features enabled:")
            logger.info("   ✅ Kafka consumer")
            logger.info("   ✅ Spark batch processing")
            logger.info("   ✅ Real-time data validation")
            logger.info("   ✅ Advanced aggregations")
            logger.info("   ✅ Anomaly detection")
            logger.info("   ✅ Alert level classification")
            logger.info("   ✅ Cassandra storage")
            logger.info("   ✅ Windows compatible")
            
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
            if self.spark:
                self.spark.stop()
            logger.info("🛑 Processing system stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping system: {e}")
    
    def run(self):
        """Main method to run the processor"""
        return self.start_processing()

if __name__ == "__main__":
    processor = WorkingSparkProcessor()
    processor.run()
