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

## 🚀 Quick Start

### Option 1: Simple Startup (Recommended)
```bash
python start.py
```

### Option 2: Manual Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Backend Server**
   ```bash
   cd backend
   python app.py
   ```

3. **Start Smart Sensors** (in another terminal)
   ```bash
   cd backend
   python smart_virtual_sensors.py
   ```

4. **Access Dashboard**
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

- `GET /api/sensors` - List all sensors
- `GET /api/sensors/latest` - Latest readings
- `GET /api/stats` - System statistics
- `GET /api/alerts` - Active alerts

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

