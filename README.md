# 🌬️ Air Quality Tracker IoT - Kosovo Monitoring

Real-time air quality monitoring system for Kosovo with smart virtual sensors and interactive web dashboard.

## 🗺️ Features

- **Interactive Kosovo Map**: Visual representation of air quality across major cities
- **Smart Virtual Sensors**: 8 sensors monitoring different cities in Kosovo
- **Real-time Data**: Live air quality updates with AQI calculations
- **Clean Dashboard**: Simple, user-friendly interface
- **Data Export**: CSV export functionality

## 🏗️ Project Structure

```
AirQualityTracker_IoT/
├── backend/
│   ├── app.py                          # Main Flask API server
│   ├── smart_virtual_sensors.py        # Smart sensor simulation
│   ├── multi_sensor_simulator.py       # Multi-sensor simulator
│   ├── multi_virtual_sensors.py        # Enhanced virtual sensors
│   ├── web-interface/
│   │   ├── public/
│   │   │   ├── index.html              # Main dashboard
│   │   │   ├── app.js                  # Frontend JavaScript
│   │   │   ├── style.css               # Styling
│   │   │   └── images/
│   │   │       ├── kosovo-map.svg      # Kosovo map
│   │   │       └── sensor_*.png        # Sensor icons
│   │   └── server.js                   # Web server
│   ├── sensors/                        # Sensor modules
│   ├── kafka/                          # Kafka consumer
│   └── spark/                          # Spark streaming
├── start.py                            # Simple startup script
└── requirements.txt                    # Python dependencies
```


## ▶️ Start the Project  

1. **Start Cassandra (database)**  
   ```bash
   docker compose up -d

2. **Backend startup** 
   ```bash
   uvicorn backend.app:app --reload --port 5000  

3. **Start Multi-Sensor Simulator** 
   ```bash 
   python multi_sensor_simulator.py

4. **Start Server** 
   ```bash
   cd backend\web-interface 
   npm install  
   node server.js

5. **For machine learning analysis**
   ```bash
   python backend/web-interface/ml_service.py


6. **Access Dashboard**
   - Open your browser to: http://localhost:8000
   - View the Kosovo map with real-time sensor data

## 🌍 Monitored Cities

- **Prishtina** - Capital city monitoring
- **Peja** - Industrial zone monitoring  
- **Prizren** - Historic district monitoring
- **Gjakova** - Mobile sensor monitoring
- **Mitrovica** - Aerial survey monitoring
- **Ferizaj** - Underground monitoring
- **Gjilan** - Urban monitoring
- **Vushtrri** - Residential monitoring

## 📊 Data Metrics

- **PM2.5 & PM10** - Particulate matter levels
- **Air Quality Index (AQI)** - Real-time air quality assessment
- **Temperature & Humidity** - Environmental conditions
- **Battery & Signal** - Sensor status monitoring


## 🔧 API Endpoints

### Sensors
- `GET /api/sensors` – List all sensors (with type & location info)  
- `GET /api/sensors/latest` – Latest readings for all sensors  
- `GET /api/sensors/:sensorId/recent?limit=N` – Recent readings for a specific sensor (default 20)  
- `POST /api/sensors/:sensorId` – Submit a sensor reading  

### Smart Sensors
- `GET /api/smart-sensors` – List all smart virtual sensors (latest in-memory data)  
- `POST /api/smart-sensors/:sensorId` – Update/insert a smart sensor reading (stores alerts & stats)  

### Analytics
- `GET /api/analytics/:sensorId?hours=N` – Get PM2.5, PM10, and AQI stats for the last N hours (default 24)  

### Alerts
- `GET /api/alerts?limit=N` – Get active alerts (default 10)  

### ML Analysis
- `GET /api/ml-analysis?sensor=ID&algorithm=random-forest|svm|kmeans&hours=N` – Run ML analysis for a sensor for the last N hours  

### System
- `GET /api/stats` – System statistics (total sensors, records, alerts, uptime)  
- `GET /api/health` – Health check (Cassandra, Kafka, WebSocket status, uptime, system version)  


## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

