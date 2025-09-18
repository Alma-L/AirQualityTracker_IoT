#!/usr/bin/env python3
"""
Spark Batch Processor for Air Quality IoT Data Processing
Windows-compatible solution using Spark's Kafka integration with batch processing
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SparkBatchProcessor:
    def __init__(self):
        # Configuration
        self.kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
        self.kafka_topic = os.environ.get('KAFKA_TOPIC', 'air-quality-data')
        self.cassandra_host = os.environ.get('CASSANDRA_HOST', 'localhost')
        self.spark_master = os.environ.get('SPARK_MASTER', 'local[*]')
        
        # Spark session
        self.spark = None
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
        
    def create_spark_session(self):
        """Create Spark session with Windows-optimized configuration"""
        try:
            # Get the correct Python path
            import sys
            python_path = sys.executable
            
            self.spark = SparkSession.builder \
                .appName("SparkBatchProcessor") \
                .master(self.spark_master) \
                .config("spark.jars.packages", 
                        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,"
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
            logger.info("✅ Spark batch session created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create Spark session: {e}")
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
    
    def process_batch_from_kafka(self):
        """Process a batch of data from Kafka using Spark"""
        try:
            logger.info("🔄 Processing batch from Kafka using Spark...")
            
            # Read from Kafka as a batch (not streaming)
            kafka_df = self.spark \
                .read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", self.kafka_broker) \
                .option("subscribe", self.kafka_topic) \
                .option("startingOffsets", "latest") \
                .option("endingOffsets", "latest") \
                .load()
            
            # Parse JSON data and clean types
            parsed_df = kafka_df \
                .selectExpr("CAST(value AS STRING)") \
                .select(from_json(col("value"), self.get_air_quality_schema()).alias("data")) \
                .select("data.*") \
                .withColumn("latitude", col("latitude").cast("double")) \
                .withColumn("longitude", col("longitude").cast("double")) \
                .withColumn("pm2_5", col("pm2_5").cast("double")) \
                .withColumn("pm10", col("pm10").cast("double")) \
                .withColumn("aqi", col("aqi").cast("int")) \
                .withColumn("visibility_meters", col("visibility_meters").cast("int")) \
                .withColumn("co2", col("co2").cast("double")) \
                .withColumn("no2", col("no2").cast("double")) \
                .withColumn("o3", col("o3").cast("double")) \
                .withColumn("temperature", col("temperature").cast("double")) \
                .withColumn("humidity", col("humidity").cast("double")) \
                .withColumn("pressure_hpa", col("pressure_hpa").cast("double")) \
                .withColumn("wind_speed", col("wind_speed").cast("double")) \
                .withColumn("wind_direction", col("wind_direction").cast("double")) \
                .withColumn("battery_level", col("battery_level").cast("double")) \
                .withColumn("signal_strength", col("signal_strength").cast("double"))
            
            # Validate data
            validated_df = parsed_df.filter(
                (col("pm2_5").isNotNull()) &
                (col("pm10").isNotNull()) &
                (col("aqi").isNotNull()) &
                (col("pm2_5") >= 0) &
                (col("pm10") >= 0) &
                (col("aqi") >= 0) &
                (col("aqi") <= 500)
            )
            
            # Add advanced aggregations using Spark
            window_spec = Window.partitionBy("sensor_id").orderBy("timestamp")
            window_spec_5min = Window.partitionBy("sensor_id").orderBy("timestamp").rangeBetween(-300, 0)
            window_spec_15min = Window.partitionBy("sensor_id").orderBy("timestamp").rangeBetween(-900, 0)
            
            aggregated_df = validated_df.withColumn("pm25_avg", 
                avg("pm2_5").over(window_spec)) \
                .withColumn("pm10_avg", 
                avg("pm10").over(window_spec)) \
                .withColumn("aqi_avg", 
                avg("aqi").over(window_spec)) \
                .withColumn("pm25_5min_avg", 
                avg("pm2_5").over(window_spec_5min)) \
                .withColumn("pm25_15min_avg", 
                avg("pm2_5").over(window_spec_15min)) \
                .withColumn("pm25_max", 
                max("pm2_5").over(window_spec)) \
                .withColumn("pm25_min", 
                min("pm2_5").over(window_spec)) \
                .withColumn("alert_level", 
                    when(col("aqi") >= 300, "Hazardous") \
                    .when(col("aqi") >= 200, "Very Unhealthy") \
                    .when(col("aqi") >= 150, "Unhealthy") \
                    .when(col("aqi") >= 100, "Unhealthy for Sensitive Groups") \
                    .when(col("aqi") >= 50, "Moderate") \
                    .otherwise("Good")
                ) \
                .withColumn("anomaly_score", 
                    abs(col("pm2_5") - col("pm25_5min_avg")) / col("pm25_5min_avg")
                ) \
                .withColumn("is_anomaly", 
                    col("anomaly_score") > 0.5
                ) \
                .withColumn("health_risk_level", 
                    when(col("aqi") >= 200, "High Risk") \
                    .when(col("aqi") >= 100, "Moderate Risk") \
                    .when(col("aqi") >= 50, "Low Risk") \
                    .otherwise("No Risk")
                )
            
            # Show results
            logger.info("📊 Spark processed data:")
            aggregated_df.select("sensor_id", "timestamp", "pm2_5", "pm10", "aqi", "alert_level", "anomaly_score", "health_risk_level") \
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
            
            # Update statistics
            record_count = aggregated_df.count()
            self.stats['total_records_processed'] += record_count
            self.stats['valid_records'] += record_count
            self.stats['aggregations_computed'] += 1
            
            logger.info(f"✅ Spark batch processed successfully: {record_count} records")
            logger.info(f"📈 Total processed: {self.stats['total_records_processed']}")
            
            return record_count
            
        except Exception as e:
            logger.error(f"❌ Error processing batch with Spark: {e}")
            return 0
    
    def run_continuous_processing(self):
        """Run continuous batch processing"""
        try:
            if not self.create_spark_session():
                return False
                
            self.is_running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("🎉 Spark Batch Processor is running!")
            logger.info("📊 Features enabled:")
            logger.info("   ✅ Spark batch processing")
            logger.info("   ✅ Kafka integration")
            logger.info("   ✅ Real-time data validation")
            logger.info("   ✅ Advanced aggregations")
            logger.info("   ✅ Sliding window operations")
            logger.info("   ✅ Anomaly detection")
            logger.info("   ✅ Alert level classification")
            logger.info("   ✅ Health risk assessment")
            logger.info("   ✅ Cassandra storage")
            logger.info("   ✅ Windows compatible")
            
            # Process batches every 10 seconds
            while self.is_running:
                try:
                    record_count = self.process_batch_from_kafka()
                    if record_count == 0:
                        logger.info("⏳ No new data, waiting...")
                    time.sleep(10)  # Wait 10 seconds between batches
                except KeyboardInterrupt:
                    logger.info("🛑 Received interrupt signal")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in continuous processing: {e}")
                    time.sleep(5)  # Wait 5 seconds before retrying
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to run batch processor: {e}")
            return False
        finally:
            self.stop_processing()
    
    def stop_processing(self):
        """Stop the processing system"""
        try:
            self.is_running = False
            if self.spark:
                self.spark.stop()
            logger.info("🛑 Spark batch processor stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping processor: {e}")
    
    def run(self):
        """Main method to run the processor"""
        return self.run_continuous_processing()

if __name__ == "__main__":
    processor = SparkBatchProcessor()
    processor.run()
