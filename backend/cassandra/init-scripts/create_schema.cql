-- Keyspace
CREATE KEYSPACE IF NOT EXISTS air_quality_monitoring
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE air_quality_monitoring;

-- Main air quality data table
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

-- Alerts table
CREATE TABLE IF NOT EXISTS air_quality_alerts (
    alert_id text,
    sensor_id text,
    timestamp timestamp,
    alert_type text,
    severity text,
    message text,
    aqi_level text,
    PRIMARY KEY (alert_id)
);

-- Aggregated data table for analytics
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

ALTER TABLE air_quality_alerts ADD is_active boolean;
