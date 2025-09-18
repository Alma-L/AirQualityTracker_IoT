# 🌬️ Air Quality Tracker IoT - Kosovo Monitoring

Real-time air quality monitoring system for Kosovo with Apache Kafka, Spark Streaming, and interactive web dashboard.

## 🗺️ Features

- **Real-time Data Processing**: Apache Spark Streaming for live data processing
- **Message Streaming**: Apache Kafka for reliable data transmission
- **Interactive Dashboard**: Real-time web interface with Kosovo map
- **Smart Virtual Sensors**: 6 sensors monitoring different areas in Kosovo
- **Data Validation**: Real-time data validation and quality control
- **Sliding Window Analytics**: 5min, 15min, and 1-hour aggregations
- **Anomaly Detection**: Automatic detection of unusual air quality patterns
- **Alert System**: Real-time alerts for poor air quality
- **Database Storage**: Apache Cassandra for scalable data persistence

## 🏗️ Project Structure

```
AirQualityTracker_IoT/
├── backend/
│   ├── app.py                              # Main FastAPI server
│   ├── multi_sensor_simulator.py           # Multi-sensor simulator
│   ├── web-interface/
│   │   ├── enhanced_spark_streaming.py     # Main Spark Streaming processor
│   │   ├── kafka_data_generator.py         # Kafka data generator
│   │   ├── spark_server.js                 # Web server with Spark integration
│   │   ├── simple_spark_server.js          # Simplified web server
│   │   ├── start_complete_system.py        # Complete system startup script
│   │   ├── server.js                       # Main web server
│   │   ├── public/
│   │   │   ├── spark_index.html            # Spark Streaming dashboard
│   │   │   ├── spark_app.js                # Frontend JavaScript for Spark
│   │   │   ├── index.html                  # Main dashboard
│   │   │   ├── app.js                      # Frontend JavaScript
│   │   │   ├── style.css                   # Styling
│   │   │   └── images/                     # Kosovo map and sensor icons
│   │   ├── requirements_spark.txt          # Spark Streaming dependencies
│   │   └── package.json                    # Node.js dependencies
│   ├── cassandra/
│   │   └── init-scripts/
│   │       └── create_schema.cql           # Database schema
│   ├── kafka/
│   │   └── consumer/
│   │       └── kafka_consumer.py           # Kafka consumer
│   └── spark/
│       └── spark_streaming.py              # Basic Spark streaming
├── docker-compose.yml                      # Docker services (Kafka, Cassandra)
└── requirements.txt                        # Python dependencies
```

## 🚀 Complete Project Startup

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Java 8 or 11** (for Spark)
- **Docker & Docker Compose**

### Step 1: Start Dependencies
```bash
docker-compose up -d

```

### Step 2: Install Dependencies
```bash
cd backend/web-interface

npm install

pip install -r requirements_spark.txt
```

### Step 3: Start Data Generator (Terminal 1)
```bash
python kafka_data_generator.py
```

### Step 4: Start Spark Streaming (Terminal 2)
```bash
python spark_streaming.py
```

### Step 5: Start Web Server (Terminal 3)
```bash

node server.js
```

### Step 6: Start Sensor Simulator (Terminal 4) - Optional
```bash

cd ..


python multi_sensor_simulator.py
```

### Step 7: Access the System
- **Main Web Dashboard**: http://localhost:8000
- **Spark Streaming Dashboard**: http://localhost:3001 (if using spark_server.js)
- **API Health Check**: http://localhost:8000/api/health
- **Real-time Data**: WebSocket connection for live updates

### Complete System Status
After starting all components, you should see:
- **Kafka**: Running on port 9092
- **Cassandra**: Running on port 9042
- **Data Generator**: Sending sensor data to Kafka
- **Spark Streaming**: Processing data in real-time
- **Web Server**: Running on port 8000
- **Sensor Simulator**: Generating additional data (optional)

## 🔧 System Architecture

```
Sensor Data → Kafka Topic → Spark Streaming → Cassandra Database
                    ↓
            WebSocket Updates → Web Dashboard
```

### Data Flow:
1. **Data Generation**: `kafka_data_generator.py` simulates sensor data
2. **Message Streaming**: Data sent to Kafka topic `air-quality-data`
3. **Real-time Processing**: Spark Streaming processes data with:
   - Data validation and filtering
   - Sliding window aggregations (5min, 15min, 1hour)
   - Anomaly detection
   - Alert generation
4. **Data Storage**: Processed data stored in Cassandra
5. **Web Interface**: Real-time dashboard with live updates

## Monitored Areas

- **Prishtina City Center** - Urban monitoring
- **Industrial Zone** - Industrial area monitoring
- **Residential Area** - Suburban monitoring
- **Bus Route** - Mobile sensor monitoring
- **Pedestrian Zone** - Wearable sensor monitoring
- **Aerial Survey** - Drone-based monitoring

## Data Metrics

- **PM2.5 & PM10** - Particulate matter levels
- **Air Quality Index (AQI)** - Real-time air quality assessment
- **Temperature & Humidity** - Environmental conditions
- **Wind Speed & Direction** - Weather conditions
- **CO2, NO2, O3** - Additional pollutants
- **Battery & Signal** - Sensor status monitoring
- **Anomaly Detection** - Unusual pattern identification
- **Alert Levels** - Health risk assessments

## 🔧 API Endpoints

### Main API
- `GET /api/sensors` - List all sensors
- `GET /api/sensors/latest` - Get latest readings for all sensors
- `GET /api/sensors/:sensorId/recent` - Get recent readings for a specific sensor
- `POST /api/sensors/:sensorId` - Submit a sensor reading

### Analytics
- `GET /api/analytics/:sensorId` - Get sensor analytics
- `GET /api/stats` - Get system statistics
- `GET /api/alerts` - Get active alerts

### System Health
- `GET /api/health` - Health check (Cassandra, Kafka, WebSocket status)

## Features

### Real-time Processing
- **Data Validation**: Comprehensive validation rules
- **Quality Control**: Filtering of invalid data
- **Sliding Windows**: 5min, 15min, 1hour aggregations
- **Anomaly Detection**: Statistical anomaly detection
- **Alert Generation**: Automatic health risk alerts

### Performance Features
- **Adaptive Query Execution**: Optimized processing
- **Checkpointing**: Fault tolerance
- **Parallel Processing**: Multi-core utilization
- **Memory Management**: Efficient resource usage

## 📚 Dependencies

### Node.js Requirements
- Express 4.21.2
- WebSocket 8.18.3
- CORS 2.8.5
- Axios 1.11.0
- Cassandra-Driver 4.8.0
- Kafka-Node 5.0.0
- UUID 9.0.0

### Python Requirements (Optional)
- PySpark 3.4.0
- Kafka-Python 2.0.2
- Cassandra-Driver 3.28.0
- FastAPI 0.104.1
- Pandas 2.0.3
- NumPy 1.24.3

### System Requirements
- Java 8 or 11
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.
