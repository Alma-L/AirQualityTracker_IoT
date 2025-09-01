import os
import json
import logging
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityStreamProcessor:
    def __init__(self):
        self.kafka_broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
        self.kafka_topic = os.environ.get('KAFKA_TOPIC', 'air-quality-data')
        self.cassandra_host = os.environ.get('CASSANDRA_HOST', 'localhost')
        self.spark_master = os.environ.get('SPARK_MASTER', 'local[*]')
        
        self.spark = None
        
    def create_spark_session(self):
        """Create Spark session with Kafka and Cassandra support"""
        self.spark = SparkSession.builder \
            .appName("AirQualityMonitoringStream") \
            .master(self.spark_master) \
            .config("spark.jars.packages", 
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,"
                    "com.datastax.spark:spark-cassandra-connector_2.12:3.4.0") \
            .config("spark.cassandra.connection.host", self.cassandra_host) \
            .config("spark.cassandra.connection.port", "9042") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
        logger.info("Spark session created successfully")
        
    def init_cassandra(self):
        """Initialize Cassandra connection and create keyspace/tables"""
        # Tables are already created by the consumer
        logger.info("Cassandra tables should be created via consumer")
        return True
    
    def get_air_quality_schema(self):
        """Define the schema for air quality data"""
        return StructType([
            StructField("sensor_id", StringType(), True),
            StructField("timestamp", StringType(), True),
            StructField("location", StructType([
                StructField("lat", DoubleType(), True),
                StructField("lon", DoubleType(), True),
                StructField("name", StringType(), True),
                StructField("area_type", StringType(), True)
            ]), True),
            StructField("air_quality_data", StructType([
                StructField("pm2_5", DoubleType(), True),
                StructField("pm10", DoubleType(), True),
                StructField("aqi", StringType(), True),
                StructField("health_risk", StringType(), True),
                StructField("visibility_meters", IntegerType(), True)
            ]), True),
            StructField("environmental_data", StructType([
                StructField("temperature_celsius", DoubleType(), True),
                StructField("humidity_percent", DoubleType(), True),
                StructField("weather_condition", StringType(), True),
                StructField("pressure_hpa", DoubleType(), True)
            ]), True)
        ])
    
    def process_batch(self, df, epoch_id):
        """Process each batch of data"""
        try:
            # Convert to proper format for Cassandra
            processed_df = df.select(
                col("sensor_id"),
                to_timestamp(col("timestamp")).alias("timestamp"),
                col("location.name").alias("location_name"),
                col("location.area_type").alias("area_type"),
                col("location.lat").alias("latitude"),
                col("location.lon").alias("longitude"),
                col("air_quality_data.pm2_5").alias("pm2_5"),
                col("air_quality_data.pm10").alias("pm10"),
                col("air_quality_data.aqi").alias("aqi"),
                col("air_quality_data.health_risk").alias("health_risk"),
                col("air_quality_data.visibility_meters").alias("visibility_meters"),
                col("environmental_data.temperature_celsius").alias("temperature_celsius"),
                col("environmental_data.humidity_percent").alias("humidity_percent"),
                col("environmental_data.weather_condition").alias("weather_condition"),
                col("environmental_data.pressure_hpa").alias("pressure_hpa")
            )
            
            # Write to Cassandra
            processed_df.write \
                .format("org.apache.spark.sql.cassandra") \
                .mode("append") \
                .options(table="air_quality_data", keyspace="air_quality_monitoring") \
                .save()
            
            logger.info(f"Batch {epoch_id} processed and saved to Cassandra")
            
        except Exception as e:
            logger.error(f"Error processing batch {epoch_id}: {e}")
    
    def start_streaming(self):
        """Start the streaming application"""
        try:
            logger.info("Starting air quality streaming application...")
            
            # Create streaming query
            streaming_query = self.spark \
                .readStream \
                .format("kafka") \
                .option("kafka.bootstrap.servers", self.kafka_broker) \
                .option("subscribe", self.kafka_topic) \
                .option("startingOffsets", "latest") \
                .load()
            
            # Parse JSON data
            parsed_stream = streaming_query \
                .selectExpr("CAST(value AS STRING)") \
                .select(from_json(col("value"), self.get_air_quality_schema()).alias("data")) \
                .select("data.*")
            
            # Start streaming with batch processing
            query = parsed_stream \
                .writeStream \
                .foreachBatch(self.process_batch) \
                .outputMode("append") \
                .start()
            
            logger.info("Streaming query started successfully")
            
            # Wait for termination
            query.awaitTermination()
            
        except Exception as e:
            logger.error(f"Error in streaming application: {e}")
            raise
    
    def run(self):
        """Main method to run the streaming application"""
        try:
            self.create_spark_session()
            self.init_cassandra()
            self.start_streaming()
        except Exception as e:
            logger.error(f"Failed to run streaming application: {e}")
            raise
        finally:
            if self.spark:
                self.spark.stop()

if __name__ == "__main__":
    processor = AirQualityStreamProcessor()
    processor.run()
