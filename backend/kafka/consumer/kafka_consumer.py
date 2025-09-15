import json
import time
import logging
from datetime import datetime
from kafka import KafkaConsumer
from cassandra.cluster import Cluster
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AirQualityDataConsumer:
    def __init__(self):
        # Kafka configuration
        self.kafka_bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.topic_name = os.getenv('KAFKA_TOPIC', 'air-quality-data')
        
        # Cassandra configuration
        self.cassandra_hosts = os.getenv('CASSANDRA_HOSTS', 'localhost').split(',')
        self.cassandra_keyspace = os.getenv('CASSANDRA_KEYSPACE', 'air_quality_monitoring')
        
        # Initialize Kafka consumer for air quality data
        self.air_quality_consumer = KafkaConsumer(
            self.topic_name,
            bootstrap_servers=self.kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='air-quality-consumer-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        # Initialize Kafka consumer for alerts
        self.alerts_consumer = KafkaConsumer(
            'air-quality-alerts',
            bootstrap_servers=self.kafka_bootstrap_servers,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='alerts-consumer-group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        
        # Initialize Cassandra connection
        self.cassandra_cluster = Cluster(self.cassandra_hosts)
        self.cassandra_session = self.cassandra_cluster.connect()
        
        # Initialize database
        self.init_cassandra()
    
    def init_cassandra(self):
        """Initialize Cassandra keyspace and tables"""
        try:
            self.cassandra_session.execute(f"""
                CREATE KEYSPACE IF NOT EXISTS {self.cassandra_keyspace}
                WITH replication = {{ 'class': 'SimpleStrategy', 'replication_factor': '1' }}
            """)

            self.cassandra_session.set_keyspace(self.cassandra_keyspace)

            # Air quality data table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS air_quality_data (
                    sensor_id text,
                    timestamp timestamp,
                    location_name text,
                    area_type text,
                    latitude double,
                    longitude double,
                    pm2_5 double,
                    pm10 double,
                    aqi text,
                    health_risk text,
                    visibility_meters double,
                    temperature_celsius double,
                    humidity_percent double,
                    weather_condition text,
                    pressure_hpa double,
                    PRIMARY KEY (sensor_id, timestamp)
                ) WITH CLUSTERING ORDER BY (timestamp DESC);
            """)

            # Alerts table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS air_quality_alerts (
                    alert_id text,
                    sensor_id text,
                    timestamp timestamp,
                    alert_type text,
                    severity text,
                    message text,
                    aqi_level text,
                    is_active boolean,
                    PRIMARY KEY (alert_id)
                );
            """)

            # Aggregated data table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS air_quality_aggregates (
                    sensor_id text,
                    window_start timestamp,
                    window_end timestamp,
                    avg_pm2_5 double,
                    avg_pm10 double,
                    max_pm2_5 double,
                    max_pm10 double,
                    min_pm2_5 double,
                    min_pm10 double,
                    total_readings int,
                    PRIMARY KEY (sensor_id, window_start)
                ) WITH CLUSTERING ORDER BY (window_start DESC);
            """)

            # Smart Virtual Sensors data table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS smart_virtual_sensors (
                    sensor_id text,
                    timestamp timestamp,
                    air_quality_index double,
                    pm2_5 double,
                    pm10 double,
                    temperature double,
                    humidity double,
                    pressure double,
                    wind_speed double,
                    wind_direction double,
                    sensor_type text,
                    location text,
                    category text,
                    battery_level double,
                    signal_strength double,
                    PRIMARY KEY (sensor_id, timestamp)
                ) WITH CLUSTERING ORDER BY (timestamp DESC);
            """)

            # Smart Virtual Sensors alerts table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS smart_sensor_alerts (
                    alert_id text,
                    sensor_id text,
                    timestamp timestamp,
                    alert_type text,
                    severity text,
                    message text,
                    battery_low boolean,
                    signal_weak boolean,
                    PRIMARY KEY (alert_id)
                );
            """)

            # Smart Virtual Sensors statistics table
            self.cassandra_session.execute("""
                CREATE TABLE IF NOT EXISTS smart_sensor_stats (
                    sensor_id text,
                    window_start timestamp,
                    window_end timestamp,
                    total_readings int,
                    avg_aqi double,
                    max_aqi double,
                    min_aqi double,
                    avg_pm2_5 double,
                    max_pm2_5 double,
                    min_pm2_5 double,
                    avg_battery double,
                    avg_signal double,
                    PRIMARY KEY (sensor_id, window_start)
                ) WITH CLUSTERING ORDER BY (window_start DESC);
            """)

            logger.info("✅ All Cassandra tables created successfully")

        except Exception as e:
            logger.error(f"❌ Error initializing Cassandra: {e}")
            raise

    
    def process_air_quality_message(self, message):
        """Process incoming air quality data message"""
        try:
            data = message.value
            logger.info(f"Received air quality data: {data['sensor_id']}")
            
            # Insert data into Cassandra
            self.insert_to_cassandra(data)
            
            # Check for alerts
            self.check_and_create_alerts(data)
            
        except Exception as e:
            logger.error(f"Error processing air quality message: {e}")
    
    def process_alert_message(self, message):
        """Process incoming alert message"""
        try:
            alert = message.value
            logger.info(f"Received alert: {alert}")
            
            # Insert alert into Cassandra
            self.insert_alert_to_cassandra(alert)
            
        except Exception as e:
            logger.error(f"Error processing alert message: {e}")
    
    def check_and_create_alerts(self, data):
        """Check air quality data and create alerts if needed"""
        try:
            pm2_5 = data.get('air_quality_data', {}).get('pm2_5', 0)
            pm10 = data.get('air_quality_data', {}).get('pm10', 0)
            aqi = data.get('air_quality_data', {}).get('aqi', 'Unknown')
            health_risk = data.get('air_quality_data', {}).get('health_risk', 'Unknown')
            
            # Create alerts based on air quality thresholds
            if pm2_5 > 55.4 or pm10 > 254:  # Unhealthy levels
                alert = {
                    'alert_id': f"alert_{int(time.time())}_{data['sensor_id']}",
                    'sensor_id': data['sensor_id'],
                    'timestamp': datetime.now(),
                    'alert_type': 'POOR_AIR_QUALITY',
                    'severity': 'HIGH',
                    'message': f'Poor air quality detected: PM2.5={pm2_5}, PM10={pm10}, AQI={aqi}',
                    'aqi_level': aqi
                }
                self.insert_alert_to_cassandra(alert)
                
            elif pm2_5 > 35.4 or pm10 > 154:  # Moderate levels
                alert = {
                    'alert_id': f"alert_{int(time.time())}_{data['sensor_id']}",
                    'sensor_id': data['sensor_id'],
                    'timestamp': datetime.now(),
                    'alert_type': 'MODERATE_AIR_QUALITY',
                    'severity': 'MEDIUM',
                    'message': f'Moderate air quality: PM2.5={pm2_5}, PM10={pm10}, AQI={aqi}',
                    'aqi_level': aqi
                }
                self.insert_alert_to_cassandra(alert)
                
        except Exception as e:
            logger.error(f"Error creating alerts: {e}")
    
    def insert_alert_to_cassandra(self, alert):
        """Insert alert data into Cassandra"""
        try:
            # Create the INSERT statement for alerts
            insert_query = """
                INSERT INTO air_quality_alerts (
                    alert_id, sensor_id, timestamp, alert_type, severity, message, aqi_level
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # Prepare the values
            values = (
                alert.get('alert_id'),
                alert.get('sensor_id', ''),
                alert.get('timestamp', datetime.now()),
                alert.get('alert_type', ''),
                alert.get('severity', 'MEDIUM'),
                alert.get('message', ''),
                alert.get('aqi_level', 'Unknown')
            )
            
            self.cassandra_session.execute(insert_query, values)
            logger.info(f"Alert inserted into Cassandra: {alert.get('sensor_id')} - {alert.get('severity')}")
            
        except Exception as e:
            logger.error(f"Error inserting alert to Cassandra: {e}")
    
    def insert_to_cassandra(self, data):
        """Insert air quality data into Cassandra"""
        try:
            # Convert timestamp string to datetime object
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()
            
            # Extract data from the message
            sensor_id = data.get('sensor_id', '')
            location = data.get('location', {})
            air_quality_data = data.get('air_quality_data', {})
            environmental_data = data.get('environmental_data', {})
            
            # Create the INSERT statement with all fields
            insert_query = """
                INSERT INTO air_quality_data (
                    sensor_id, timestamp, location_name, area_type, latitude, longitude,
                    pm2_5, pm10, aqi, health_risk, visibility_meters,
                    temperature_celsius, humidity_percent, weather_condition, pressure_hpa
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Prepare the values
            values = (
                sensor_id,
                timestamp,
                location.get('name'),
                location.get('area_type'),
                location.get('lat'),
                location.get('lon'),
                air_quality_data.get('pm2_5'),
                air_quality_data.get('pm10'),
                air_quality_data.get('aqi'),
                air_quality_data.get('health_risk'),
                air_quality_data.get('visibility_meters'),
                environmental_data.get('temperature_celsius'),
                environmental_data.get('humidity_percent'),
                environmental_data.get('weather_condition'),
                environmental_data.get('pressure_hpa')
            )
            
            self.cassandra_session.execute(insert_query, values)
            logger.info(f"Data inserted into Cassandra: {sensor_id} - PM2.5: {air_quality_data.get('pm2_5', 0)}")
            
        except Exception as e:
            logger.error(f"Error inserting to Cassandra: {e}")
    
    def start_consuming(self):
        """Start consuming messages from Kafka"""
        logger.info(f"Starting to consume from topics: {self.topic_name} and air-quality-alerts")
        
        try:
            # Use Kafka's consumer group functionality to handle multiple topics
            from kafka import KafkaConsumer
            from threading import Thread
            
            # Create a combined consumer for both topics
            combined_consumer = KafkaConsumer(
                self.topic_name, 'air-quality-alerts',
                bootstrap_servers=self.kafka_bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='combined-consumer-group',
                value_deserializer=lambda x: json.loads(x.decode('utf-8'))
            )
            
            for message in combined_consumer:
                if message.topic == self.topic_name:
                    self.process_air_quality_message(message)
                elif message.topic == 'air-quality-alerts':
                    self.process_alert_message(message)
                
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
        finally:
            if 'combined_consumer' in locals():
                combined_consumer.close()
            self.cassandra_cluster.shutdown()

if __name__ == "__main__":
    consumer = AirQualityDataConsumer()
    consumer.start_consuming()
