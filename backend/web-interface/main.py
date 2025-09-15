from turtle import pd
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os
from datetime import datetime, timedelta
import json
from ml_algorithms import run_ml_algorithm 
from requests import session
from fastapi import Query, HTTPException
from datetime import datetime, timedelta
import pandas as pd

app = FastAPI(title="Air Quality Tracker IoT", version="2.0.0")

# Allow frontend (CORS config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced sensor storage with AQI and alerts
sensors_data = {}
alerts_history = []
system_start_time = datetime.utcnow()

# Smart sensors are now handled client-side with sample data

# AQI calculation functions
def calculate_aqi(pm25, pm10):
    """Calculate Air Quality Index based on PM2.5 and PM10 values"""
    # PM2.5 AQI calculation (EPA standard)
    if pm25 <= 12.0:
        aqi_pm25 = linear_scale(pm25, 0, 12.0, 0, 50)
    elif pm25 <= 35.4:
        aqi_pm25 = linear_scale(pm25, 12.1, 35.4, 51, 100)
    elif pm25 <= 55.4:
        aqi_pm25 = linear_scale(pm25, 35.5, 55.4, 101, 150)
    elif pm25 <= 150.4:
        aqi_pm25 = linear_scale(pm25, 55.5, 150.4, 151, 200)
    elif pm25 <= 250.4:
        aqi_pm25 = linear_scale(pm25, 150.5, 250.4, 201, 300)
    else:
        aqi_pm25 = linear_scale(pm25, 250.5, 500.4, 301, 500)
    
    # PM10 AQI calculation
    if pm10 <= 54:
        aqi_pm10 = linear_scale(pm10, 0, 54, 0, 50)
    elif pm10 <= 154:
        aqi_pm10 = linear_scale(pm10, 55, 154, 51, 100)
    elif pm10 <= 254:
        aqi_pm10 = linear_scale(pm10, 155, 254, 101, 150)
    elif pm10 <= 354:
        aqi_pm10 = linear_scale(pm10, 255, 354, 151, 200)
    elif pm10 <= 424:
        aqi_pm10 = linear_scale(pm10, 355, 424, 201, 300)
    else:
        aqi_pm10 = linear_scale(pm10, 425, 604, 301, 500)
    
    # Return the higher AQI value
    return max(aqi_pm25, aqi_pm10)

def linear_scale(value, low, high, aqi_low, aqi_high):
    """Linear interpolation for AQI calculation"""
    return int(((value - low) / (high - low)) * (aqi_high - aqi_low) + aqi_low)

def get_aqi_category(aqi):
    """Get AQI category and health risk"""
    if aqi <= 50:
        return "Good", "🟢 Air quality is satisfactory"
    elif aqi <= 100:
        return "Moderate", "🟡 Some pollutants may be a concern"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "🟠 Sensitive groups may experience health effects"
    elif aqi <= 200:
        return "Unhealthy", "🔴 Everyone may begin to experience health effects"
    elif aqi <= 300:
        return "Very Unhealthy", "🟣 Health warnings of emergency conditions"
    else:
        return "Hazardous", "⚫ Health alert: everyone may experience serious health effects"

def check_alerts(sensor_id, reading):
    """Check if readings trigger alerts"""
    alerts = []
    aqi = calculate_aqi(reading['pm2_5'], reading['pm10'])
    
    # High PM2.5 alert
    if reading['pm2_5'] > 55.4:
        alerts.append({
            "type": "High PM2.5",
            "severity": "warning",
            "message": f"PM2.5 level {reading['pm2_5']} exceeds healthy limit",
            "value": reading['pm2_5'],
            "threshold": 55.4
        })
    
    # High PM10 alert
    if reading['pm10'] > 154:
        alerts.append({
            "type": "High PM10",
            "severity": "warning", 
            "message": f"PM10 level {reading['pm10']} exceeds healthy limit",
            "value": reading['pm10'],
            "threshold": 154
        })
    
    # Poor air quality alert
    if aqi > 150:
        alerts.append({
            "type": "Poor Air Quality",
            "severity": "danger",
            "message": f"AQI {aqi} indicates unhealthy air quality",
            "value": aqi,
            "threshold": 150
        })
    
    # Temperature extremes
    if reading['temperature'] > 35 or reading['temperature'] < 0:
        alerts.append({
            "type": "Temperature Extreme",
            "severity": "warning",
            "message": f"Temperature {reading['temperature']}°C is outside normal range",
            "value": reading['temperature'],
            "threshold": "0-35°C"
        })
    
    return alerts

@app.get("/api/health")
def health_check():
    uptime = datetime.utcnow() - system_start_time
    return {
        "status": "ok", 
        "message": "Air Quality Tracker IoT Backend is running",
        "version": "2.0.0",
        "uptime_seconds": int(uptime.total_seconds())
    }

@app.post("/api/sensors/{sensor_id}")
def add_sensor_reading(sensor_id: str, reading: dict):
    """Add a new sensor reading with enhanced processing"""
    if sensor_id not in sensors_data:
        sensors_data[sensor_id] = []
    
    # Calculate AQI and health risk
    aqi = calculate_aqi(reading['pm2_5'], reading['pm10'])
    category, health_message = get_aqi_category(aqi)
    
    # Enhanced reading with AQI data
    enhanced_reading = {
        **reading,
        "aqi": aqi,
        "aqi_category": category,
        "health_message": health_message,
        "timestamp": reading.get('timestamp', datetime.utcnow().isoformat())
    }
    
    sensors_data[sensor_id].append(enhanced_reading)
    
    # Check for alerts
    alerts = check_alerts(sensor_id, enhanced_reading)
    for alert in alerts:
        alert_data = {
            **alert,
            "sensor_id": sensor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "location": "IoT Sensor Network",
            "status": "active"
        }
        alerts_history.append(alert_data)
    
    return {
        "message": "Reading stored successfully", 
        "sensor_id": sensor_id,
        "aqi": aqi,
        "category": category,
        "alerts_generated": len(alerts)
    }

@app.get("/api/sensors/latest")
def get_latest_readings():
    """Get the latest reading from each sensor with enhanced data"""
    latest = []
    for sensor_id, readings in sensors_data.items():
        if readings:
            latest.append(readings[-1])
    return latest

@app.get("/api/sensors/{sensor_id}/recent")
def get_recent_readings(sensor_id: str, limit: int = 20):
    """Get recent readings from a specific sensor"""
    if sensor_id not in sensors_data:
        return []
    
    readings = sensors_data[sensor_id]
    return readings[-limit:] if readings else []

@app.get("/api/stats")
def get_stats():
    """Get system statistics"""
    total_readings = sum(len(readings) for readings in sensors_data.values())
    active_alerts = len([a for a in alerts_history if a.get("status") == "active"])
    uptime_seconds = (datetime.utcnow() - system_start_time).total_seconds()
    
    # Calculate average AQI across all sensors
    all_aqis = []
    for sensor_readings in sensors_data.values():
        for reading in sensor_readings:
            if "aqi" in reading:
                all_aqis.append(reading["aqi"])
    
    average_aqi = round(sum(all_aqis) / len(all_aqis), 1) if all_aqis else 0
    
    # Get list of active sensors
    active_sensors = list(sensors_data.keys())
    
    return {
        "sensor_count": len(sensors_data),
        "total_readings": total_readings,
        "active_alerts": active_alerts,
        "uptime_seconds": int(uptime_seconds),
        "average_aqi": average_aqi,
        "sensors": active_sensors,
        "system_version": "2.0.0"
    }

@app.get("/api/alerts")
def get_alerts(limit: int = 10):
    """Return recent active alerts from in-memory history"""
    active_alerts = [a for a in alerts_history if a.get("status") == "active"]
    return list(reversed(active_alerts))[:limit]


@app.get("/api/analytics/{sensor_id}")
def get_sensor_analytics(sensor_id: str, hours: int = 24):
    """Get analytics data for a specific sensor"""
    if sensor_id not in sensors_data:
        return {"error": "Sensor not found"}
    
    readings = sensors_data[sensor_id]
    if not readings:
        return {"error": "No data available"}
    
    # Filter readings from last N hours
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    recent_readings = [
        r for r in readings 
        if datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')) > cutoff_time
    ]
    
    if not recent_readings:
        return {"error": "No recent data available"}
    
    # Calculate statistics
    pm25_values = [r['pm2_5'] for r in recent_readings]
    pm10_values = [r['pm10'] for r in recent_readings]
    aqi_values = [r.get('aqi', 0) for r in recent_readings]
    
    return {
        "sensor_id": sensor_id,
        "time_period_hours": hours,
        "readings_count": len(recent_readings),
        "pm25": {
            "min": min(pm25_values),
            "max": max(pm25_values),
            "average": round(sum(pm25_values) / len(pm25_values), 2)
        },
        "pm10": {
            "min": min(pm10_values),
            "max": max(pm10_values),
            "average": round(sum(pm10_values) / len(pm10_values), 2)
        },
        "aqi": {
            "min": min(aqi_values),
            "max": max(aqi_values),
            "average": round(sum(aqi_values) / len(aqi_values), 1)
        },
        "trend": "stable"  # Simplified trend calculation
    }


SUPPORTED_ALGORITHMS = ["random-forest", "svm", "kmeans"]

@app.get("/api/ml-analysis")
def ml_analysis(
    sensor: str = Query(...),
    algorithm: str = Query("random-forest"),
    hours: int = Query(24)
):
    """Run ML analysis for a sensor over a time period (hours)."""
    if algorithm.lower() not in SUPPORTED_ALGORITHMS:
        raise HTTPException(
            status_code=400,
            detail=f"Algorithm '{algorithm}' not supported. Choose from {SUPPORTED_ALGORITHMS}"
        )

    if sensor not in sensors_data:
        return {"error": f"Sensor '{sensor}' not found", "anomalies": []}

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    readings = [
        r for r in sensors_data[sensor]
        if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) >= cutoff
    ]
    if not readings:
        return {"error": "No data available for this sensor in the requested period", "anomalies": []}

    df = pd.DataFrame(readings).rename(columns={"temperature": "temp"})

    anomalies = run_ml_algorithm(df, algorithm=algorithm.lower())

    timestamps = df['timestamp'].astype(str).tolist()
    pm25_values = df['pm2_5'].tolist()
    pm10_values = df['pm10'].tolist()
    scores = [1 if ts in [a['timestamp'] for a in anomalies] else 0 for ts in timestamps]

    return {
        "sensor": sensor,
        "algorithm": algorithm,
        "hours": hours,
        "total_readings": len(df),
        "anomalies_count": len(anomalies),
        "anomalies": anomalies,
        "timestamps": timestamps,
        "pm25": pm25_values,
        "pm10": pm10_values,
        "scores": scores
    }


@app.get("/api/sensors")
def get_all_sensors():
    """Return all sensors with type, location, and icon info for frontend"""
    sensors_list = []
    for sensor_id in sensors_data.keys():
        sensor_type = "Unknown"
        location = "Unknown"
        if "urban" in sensor_id:
            sensor_type = "Urban"
            location = "City Center"
        elif "industrial" in sensor_id:
            sensor_type = "Industrial"
            location = "Factory Zone"
        elif "residential" in sensor_id:
            sensor_type = "Residential"
            location = "Suburban Area"
        elif "bus" in sensor_id:
            sensor_type = "Mobile"
            location = "City Bus Route"
        elif "wearable" in sensor_id:
            sensor_type = "Wearable"
            location = "Cyclist / Pedestrian"
        elif "drone" in sensor_id:
            sensor_type = "Drone"
            location = "Aerial / City Monitoring"

        sensors_list.append({
            "id": sensor_id,
            "type": sensor_type,
            "location": location,
            "img": f"/static/images/sensor_{sensor_type.lower()}.png"
        })

    return {"sensors": sensors_list}

# WebSocket support for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    await ws.send_text("✅ WebSocket connected to Air Quality Tracker IoT v2.0")
    
    try:
        while True:
            # Send real-time updates
            latest_data = get_latest_readings()
            await ws.send_text(json.dumps({
                "type": "realtime_update",
                "data": latest_data,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Send alerts if any
            recent_alerts = [a for a in alerts_history[-5:]]  # Last 5 alerts
            if recent_alerts:
                await ws.send_text(json.dumps({
                    "type": "alerts_update",
                    "alerts": recent_alerts
                }))
            
            # Wait 5 seconds before next update
            import asyncio
            await asyncio.sleep(5)
            
    except Exception:
        pass

# Serve static files from "public" folder (frontend)
current_dir = os.path.dirname(__file__)
public_dir = os.path.join(current_dir, "public")

if not os.path.exists(public_dir):
    raise RuntimeError(f"Public directory not found: {public_dir}")

app.mount("/static", StaticFiles(directory=public_dir), name="public")

# Redirect root (/) to index.html
@app.get("/")
async def serve_index():
    """Serve the main frontend page"""
    index_path = os.path.join(public_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return RedirectResponse(url="/static/")

@app.get("/favicon.ico")
async def favicon():
    """Serve favicon if it exists"""
    favicon_path = os.path.join(public_dir, "favicon.ico")
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return {"message": "No favicon found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
