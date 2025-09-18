#!/usr/bin/env python3
"""
Enhanced Apache Spark Streaming Application for Air Quality IoT Data Processing
Task 4: Real-time sensor data processing with Apache Spark Streaming

Features:
- Real-time data processing from Kafka
- Data aggregation and validation
- Filtering and analysis
- Sliding window operations
- Database preparation for storage
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
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedAirQualityStreamProcessor:
    def __init__(self):
        # Configuration
        self.kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
        self.kafka_topic = os.environ.get('KAFKA_TOPIC', 'air-quality-data')
        self.cassandra_host = os.environ.get('CASSANDRA_HOST', 'localhost')
        self.spark_master = os.environ.get('SPARK_MASTER', 'local[*]')
        
        # Spark session
        self.spark = None
        self.streaming_query = None
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
        """Create Spark session with optimized configuration for streaming"""
        try:
            self.spark = SparkSession.builder \
                .appName("EnhancedAirQualityStreaming") \
                .master(self.spark_master) \
                .config("spark.jars.packages", 
                        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,"
                        "com.datastax.spark:spark-cassandra-connector_2.12:3.4.0") \
                .config("spark.cassandra.connection.host", self.cassandra_host) \
                .config("spark.cassandra.connection.port", "9042") \
                .config("spark.sql.streaming.checkpointLocation", "file:///C:/tmp/checkpoint_enhanced") \
                .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
                .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                .config("spark.sql.adaptive.enabled", "false") \
                .config("spark.sql.adaptive.coalescePartitions.enabled", "false") \
                .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.LocalFileSystem") \
                .getOrCreate()
            
            self.spark.sparkContext.setLogLevel("WARN")
            logger.info("✅ Enhanced Spark session created successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create Spark session: {e}")
            return False
    
    def get_air_quality_schema(self):
        """Define comprehensive schema for air quality data"""
        return StructType([
            StructField("sensor_id", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("location", StructType([
                StructField("lat", DoubleType(), True),
                StructField("lon", DoubleType(), True),
                StructField("name", StringType(), True),
                StructField("area_type", StringType(), True),
                StructField("city", StringType(), True)
            ]), True),
            StructField("air_quality_data", StructType([
                StructField("pm2_5", DoubleType(), True),
                StructField("pm10", DoubleType(), True),
                StructField("aqi", IntegerType(), True),
                StructField("health_risk", StringType(), True),
                StructField("visibility_meters", IntegerType(), True),
                StructField("co2", DoubleType(), True),
                StructField("no2", DoubleType(), True),
                StructField("o3", DoubleType(), True)
            ]), True),
            StructField("environmental_data", StructType([
                StructField("temperature_celsius", DoubleType(), True),
                StructField("humidity_percent", DoubleType(), True),
                StructField("weather_condition", StringType(), True),
                StructField("pressure_hpa", DoubleType(), True),
                StructField("wind_speed", DoubleType(), True),
                StructField("wind_direction", DoubleType(), True)
            ]), True),
            StructField("sensor_metadata", StructType([
                StructField("battery_level", DoubleType(), True),
                StructField("signal_strength", DoubleType(), True),
                StructField("firmware_version", StringType(), True),
                StructField("last_calibration", StringType(), True)
            ]), True)
        ])
    
    def validate_sensor_data(self, df):
        """Validate sensor data and add validation flags"""
        logger.info("🔍 Validating sensor data...")
        
        # Add validation rules
        validated_df = df.withColumn("is_valid", 
            (col("air_quality_data.pm2_5").isNotNull()) &
            (col("air_quality_data.pm10").isNotNull()) &
            (col("air_quality_data.aqi").isNotNull()) &
            (col("air_quality_data.pm2_5") >= 0) &
            (col("air_quality_data.pm10") >= 0) &
            (col("air_quality_data.aqi") >= 0) &
            (col("air_quality_data.aqi") <= 500) &
            (col("environmental_data.temperature_celsius").isNotNull()) &
            (col("environmental_data.humidity_percent").isNotNull()) &
            (col("environmental_data.temperature_celsius") >= -50) &
            (col("environmental_data.temperature_celsius") <= 60) &
            (col("environmental_data.humidity_percent") >= 0) &
            (col("environmental_data.humidity_percent") <= 100)
        ).withColumn("validation_errors", 
            when(col("is_valid") == False, 
                concat_ws(", ",
                    when(col("air_quality_data.pm2_5").isNull(), lit("PM2.5 missing")),
                    when(col("air_quality_data.pm10").isNull(), lit("PM10 missing")),
                    when(col("air_quality_data.aqi").isNull(), lit("AQI missing")),
                    when(col("air_quality_data.pm2_5") < 0, lit("PM2.5 negative")),
                    when(col("air_quality_data.pm10") < 0, lit("PM10 negative")),
                    when(col("air_quality_data.aqi") < 0, lit("AQI negative")),
                    when(col("air_quality_data.aqi") > 500, lit("AQI too high")),
                    when(col("environmental_data.temperature_celsius").isNull(), lit("Temperature missing")),
                    when(col("environmental_data.humidity_percent").isNull(), lit("Humidity missing")),
                    when(col("environmental_data.temperature_celsius") < -50, lit("Temperature too low")),
                    when(col("environmental_data.temperature_celsius") > 60, lit("Temperature too high")),
                    when(col("environmental_data.humidity_percent") < 0, lit("Humidity negative")),
                    when(col("environmental_data.humidity_percent") > 100, lit("Humidity too high"))
                )
            ).otherwise(lit(""))
        )
        
        return validated_df
    
    def apply_data_filters(self, df):
        """Apply various data filters for quality control"""
        logger.info("🔧 Applying data filters...")
        
        # Filter out invalid records
        filtered_df = df.filter(col("is_valid") == True)
        
        # Additional quality filters
        quality_filtered_df = filtered_df.filter(
            # Remove extreme outliers
            (col("air_quality_data.pm2_5") <= 200) &  # Reasonable PM2.5 limit
            (col("air_quality_data.pm10") <= 300) &   # Reasonable PM10 limit
            (col("environmental_data.temperature_celsius") >= -20) &
            (col("environmental_data.temperature_celsius") <= 50) &
            (col("environmental_data.humidity_percent") >= 5) &
            (col("environmental_data.humidity_percent") <= 95)
        )
        
        return quality_filtered_df
    
    def compute_aggregations(self, df):
        """Compute various aggregations on the streaming data"""
        logger.info("📊 Computing aggregations...")
        
        # Define window specifications
        window_spec_5min = Window.partitionBy("sensor_id").orderBy("timestamp").rangeBetween(-300, 0)  # 5 minutes
        window_spec_15min = Window.partitionBy("sensor_id").orderBy("timestamp").rangeBetween(-900, 0)  # 15 minutes
        window_spec_1hour = Window.partitionBy("sensor_id").orderBy("timestamp").rangeBetween(-3600, 0)  # 1 hour
        
        # Add aggregated columns
        aggregated_df = df.withColumn("pm25_5min_avg", 
            avg("air_quality_data.pm2_5").over(window_spec_5min)) \
            .withColumn("pm25_15min_avg", 
            avg("air_quality_data.pm2_5").over(window_spec_15min)) \
            .withColumn("pm25_1hour_avg", 
            avg("air_quality_data.pm2_5").over(window_spec_1hour)) \
            .withColumn("pm10_5min_avg", 
            avg("air_quality_data.pm10").over(window_spec_5min)) \
            .withColumn("aqi_5min_avg", 
            avg("air_quality_data.aqi").over(window_spec_5min)) \
            .withColumn("temp_5min_avg", 
            avg("environmental_data.temperature_celsius").over(window_spec_5min)) \
            .withColumn("humidity_5min_avg", 
            avg("environmental_data.humidity_percent").over(window_spec_5min)) \
            .withColumn("pm25_5min_max", 
            max("air_quality_data.pm2_5").over(window_spec_5min)) \
            .withColumn("pm25_5min_min", 
            min("air_quality_data.pm2_5").over(window_spec_5min)) \
            .withColumn("aqi_5min_max", 
            max("air_quality_data.aqi").over(window_spec_5min)) \
            .withColumn("aqi_5min_min", 
            min("air_quality_data.aqi").over(window_spec_5min))
        
        return aggregated_df
    
    def detect_anomalies(self, df):
        """Detect anomalies in sensor data using statistical methods"""
        logger.info("🚨 Detecting anomalies...")
        
        # Simple anomaly detection based on standard deviation
        anomaly_df = df.withColumn("pm25_anomaly", 
            abs(col("air_quality_data.pm2_5") - col("pm25_5min_avg")) > (2 * stddev("air_quality_data.pm2_5").over(Window.partitionBy("sensor_id")))
        ).withColumn("aqi_anomaly", 
            abs(col("air_quality_data.aqi") - col("aqi_5min_avg")) > (2 * stddev("air_quality_data.aqi").over(Window.partitionBy("sensor_id")))
        ).withColumn("is_anomaly", 
            col("pm25_anomaly") | col("aqi_anomaly")
        ).withColumn("anomaly_score", 
            when(col("is_anomaly"), 
                (abs(col("air_quality_data.pm2_5") - col("pm25_5min_avg")) / col("pm25_5min_avg")) +
                (abs(col("air_quality_data.aqi") - col("aqi_5min_avg")) / col("aqi_5min_avg"))
            ).otherwise(0.0)
        )
        
        return anomaly_df
    
    def generate_alerts(self, df):
        """Generate alerts based on air quality thresholds"""
        logger.info("🚨 Generating alerts...")
        
        alert_df = df.withColumn("alert_level", 
            when(col("air_quality_data.aqi") >= 300, "Hazardous") \
            .when(col("air_quality_data.aqi") >= 200, "Very Unhealthy") \
            .when(col("air_quality_data.aqi") >= 150, "Unhealthy") \
            .when(col("air_quality_data.aqi") >= 100, "Unhealthy for Sensitive Groups") \
            .when(col("air_quality_data.aqi") >= 50, "Moderate") \
            .otherwise("Good")
        ).withColumn("alert_message", 
            when(col("air_quality_data.aqi") >= 300, "Hazardous air quality! Avoid outdoor activities!") \
            .when(col("air_quality_data.aqi") >= 200, "Very unhealthy air quality! Limit outdoor activities!") \
            .when(col("air_quality_data.aqi") >= 150, "Unhealthy air quality! Sensitive groups should avoid outdoor activities!") \
            .when(col("air_quality_data.aqi") >= 100, "Moderate air quality. Sensitive groups may experience minor health effects.") \
            .otherwise("Good air quality. No health concerns.")
        ).withColumn("has_alert", 
            col("air_quality_data.aqi") >= 100
        )
        
        return alert_df
    
    def prepare_for_database(self, df):
        """Prepare processed data for database storage"""
        logger.info("💾 Preparing data for database storage...")
        
        # Flatten the nested structure for Cassandra storage
        prepared_df = df.select(
            col("sensor_id"),
            to_timestamp(col("timestamp")).alias("timestamp"),
            col("location.name").alias("location_name"),
            col("location.area_type").alias("area_type"),
            col("location.city").alias("city"),
            col("location.lat").alias("latitude"),
            col("location.lon").alias("longitude"),
            col("air_quality_data.pm2_5").alias("pm2_5"),
            col("air_quality_data.pm10").alias("pm10"),
            col("air_quality_data.aqi").alias("aqi"),
            col("air_quality_data.health_risk").alias("health_risk"),
            col("air_quality_data.visibility_meters").alias("visibility_meters"),
            col("air_quality_data.co2").alias("co2"),
            col("air_quality_data.no2").alias("no2"),
            col("air_quality_data.o3").alias("o3"),
            col("environmental_data.temperature_celsius").alias("temperature_celsius"),
            col("environmental_data.humidity_percent").alias("humidity_percent"),
            col("environmental_data.weather_condition").alias("weather_condition"),
            col("environmental_data.pressure_hpa").alias("pressure_hpa"),
            col("environmental_data.wind_speed").alias("wind_speed"),
            col("environmental_data.wind_direction").alias("wind_direction"),
            col("sensor_metadata.battery_level").alias("battery_level"),
            col("sensor_metadata.signal_strength").alias("signal_strength"),
            col("sensor_metadata.firmware_version").alias("firmware_version"),
            col("sensor_metadata.last_calibration").alias("last_calibration"),
            # Aggregated values
            col("pm25_5min_avg"),
            col("pm25_15min_avg"),
            col("pm25_1hour_avg"),
            col("pm10_5min_avg"),
            col("aqi_5min_avg"),
            col("temp_5min_avg"),
            col("humidity_5min_avg"),
            col("pm25_5min_max"),
            col("pm25_5min_min"),
            col("aqi_5min_max"),
            col("aqi_5min_min"),
            # Anomaly detection
            col("is_anomaly"),
            col("anomaly_score"),
            col("pm25_anomaly"),
            col("aqi_anomaly"),
            # Alerts
            col("alert_level"),
            col("alert_message"),
            col("has_alert"),
            # Validation
            col("is_valid"),
            col("validation_errors"),
            # Processing metadata
            current_timestamp().alias("processed_at"),
            lit("enhanced_spark_streaming").alias("processing_version")
        )
        
        return prepared_df
    
    def process_batch(self, df, epoch_id):
        """Process each batch of streaming data"""
        try:
            logger.info(f"🔄 Processing batch {epoch_id} with {df.count()} records")
            
            # Step 1: Validate data
            validated_df = self.validate_sensor_data(df)
            
            # Step 2: Apply filters
            filtered_df = self.apply_data_filters(validated_df)
            
            # Step 3: Compute aggregations
            aggregated_df = self.compute_aggregations(filtered_df)
            
            # Step 4: Detect anomalies
            anomaly_df = self.detect_anomalies(aggregated_df)
            
            # Step 5: Generate alerts
            alert_df = self.generate_alerts(anomaly_df)
            
            # Step 6: Prepare for database
            final_df = self.prepare_for_database(alert_df)
            
            # Write to Cassandra
            final_df.write \
                .format("org.apache.spark.sql.cassandra") \
                .mode("append") \
                .options(table="air_quality_data", keyspace="air_quality_monitoring") \
                .save()
            
            # Update statistics
            record_count = final_df.count()
            valid_count = final_df.filter(col("is_valid") == True).count()
            invalid_count = record_count - valid_count
            alert_count = final_df.filter(col("has_alert") == True).count()
            anomaly_count = final_df.filter(col("is_anomaly") == True).count()
            
            self.stats['total_records_processed'] += record_count
            self.stats['valid_records'] += valid_count
            self.stats['invalid_records'] += invalid_count
            self.stats['aggregations_computed'] += 1
            self.stats['alerts_generated'] += alert_count
            
            logger.info(f"✅ Batch {epoch_id} processed successfully:")
            logger.info(f"   📊 Records: {record_count} (Valid: {valid_count}, Invalid: {invalid_count})")
            logger.info(f"   🚨 Alerts: {alert_count}")
            logger.info(f"   ⚠️  Anomalies: {anomaly_count}")
            logger.info(f"   📈 Total processed: {self.stats['total_records_processed']}")
            
        except Exception as e:
            logger.error(f"❌ Error processing batch {epoch_id}: {e}")
            raise
    
    def start_streaming(self):
        """Start the enhanced streaming application"""
        try:
            if not self.create_spark_session():
                return False
                
            logger.info("🚀 Starting Enhanced Air Quality Streaming Application...")
            self.stats['start_time'] = datetime.now()
            
            # Create streaming query from Kafka
            streaming_query = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", self.kafka_broker) \
                .option("subscribe", self.kafka_topic) \
                .option("startingOffsets", "latest") \
                .option("maxOffsetsPerTrigger", 1000) \
                .load()
            
            # Parse JSON data
            parsed_stream = streaming_query \
                .selectExpr("CAST(value AS STRING)") \
                .select(from_json(col("value"), self.get_air_quality_schema()).alias("data")) \
                .select("data.*")
            
            # Start streaming with batch processing
            self.streaming_query = parsed_stream \
                .writeStream \
                .foreachBatch(self.process_batch) \
                .outputMode("append") \
                .trigger(processingTime='10 seconds') \
                .start()
            
            self.is_running = True
            logger.info("✅ Enhanced streaming application started successfully")
            logger.info("📊 Processing configuration:")
            logger.info(f"   🔄 Batch interval: 10 seconds")
            logger.info(f"   📦 Max records per batch: 1000")
            logger.info(f"   🎯 Kafka topic: {self.kafka_topic}")
            logger.info(f"   💾 Database: Cassandra")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error starting streaming: {e}")
            return False
    
    def stop_streaming(self):
        """Stop the streaming application"""
        try:
            if self.streaming_query:
                self.streaming_query.stop()
            if self.spark:
                self.spark.stop()
            self.is_running = False
            logger.info("🛑 Enhanced streaming application stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping streaming: {e}")
    
    def get_statistics(self):
        """Get processing statistics"""
        if self.stats['start_time']:
            uptime = datetime.now() - self.stats['start_time']
            self.stats['uptime_seconds'] = uptime.total_seconds()
        
        return self.stats
    
    def run(self):
        """Main method to run the enhanced streaming application"""
        try:
            if self.start_streaming():
                logger.info("🎉 Enhanced Air Quality Streaming Application is running!")
                logger.info("📊 Features enabled:")
                logger.info("   ✅ Real-time data validation")
                logger.info("   ✅ Data filtering and quality control")
                logger.info("   ✅ Sliding window aggregations (5min, 15min, 1hour)")
                logger.info("   ✅ Anomaly detection")
                logger.info("   ✅ Alert generation")
                logger.info("   ✅ Database preparation")
                logger.info("   ✅ Comprehensive statistics")
                
                # Keep running
                self.streaming_query.awaitTermination()
            else:
                logger.error("❌ Failed to start streaming application")
                return False
                
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"❌ Failed to run streaming application: {e}")
            return False
        finally:
            self.stop_streaming()
        
        return True

if __name__ == "__main__":
    processor = EnhancedAirQualityStreamProcessor()
    processor.run()
