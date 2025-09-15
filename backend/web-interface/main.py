# main.py

from fastapi import FastAPI, WebSocket, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
import os
from datetime import datetime, timedelta
import json
import pandas as pd
from ml_algorithms import run_ml_algorithm
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
import asyncio

# Initialize FastAPI
app = FastAPI(title="Air Quality Tracker IoT", version="2.0.0")

# Allow frontend (CORS config)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cassandra Configuration
CASSANDRA_HOST = os.getenv("CASSANDRA_HOST", "localhost")
CASSANDRA_KEYSPACE = "air_quality_monitoring"

# Initialize Cassandra connection
cassandra_session = None
cassandra_connected = False

def connect_to_cassandra():
    global cassandra_session, cassandra_connected
    try:
        cluster = Cluster([CASSANDRA_HOST])
        session = cluster.connect()
        session.set_keyspace(CASSANDRA_KEYSPACE)
        session.row_factory = dict_factory
        cassandra_session = session
        cassandra_connected = True
        print("✅ Connected to Cassandra")
    except Exception as e:
        print(f"❌ Failed to connect to Cassandra: {e}")
        cassandra_connected = False

# Connect to Cassandra on startup
@app.on_event("startup")
async def startup_event():
    connect_to_cassandra()

# ----------------------------
# AQI calculation functions
# ----------------------------
def linear_scale(value, low, high, aqi_low, aqi_high):
    """Linear interpolation for AQI calculation"""
    return int(((value - low) / (high - low)) * (aqi_high - aqi_low) + aqi_low)

def calculate_aqi(pm25, pm10):
    """Calculate Air Quality Index based on PM2.5 and PM10 values"""
    # PM2.5 AQI calculation
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

    return max(aqi_pm25, aqi_pm10)

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

# ----------------------------
# Health check endpoint
# ----------------------------
system_start_time = datetime.utcnow()

@app.get("/api/health")
def health_check():
    uptime = datetime.utcnow() - system_start_time
    return {
        "status": "ok",
        "message": "Air Quality Tracker IoT Backend is running",
        "version": "2.0.0",
        "uptime_seconds": int(uptime.total_seconds()),
        "cassandra": "connected" if cassandra_connected else "disconnected",
    }

# ----------------------------
# ML Analysis endpoint
# ----------------------------
SUPPORTED_ALGORITHMS = ["random-forest", "svm", "kmeans"]

@app.get("/api/ml-analysis")
async def ml_analysis(
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

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    query = """
        SELECT timestamp, pm2_5, pm10, temperature_celsius as temperature
        FROM air_quality_data
        WHERE sensor_id = %s AND timestamp >= %s
        ORDER BY timestamp DESC
    """
    result = cassandra_session.execute(query, [sensor, cutoff_time])

    if not result:
        return {"error": "No data available for this sensor in the requested period", "anomalies": []}

    readings = []
    for row in result:
        readings.append({
            "timestamp": row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp']),
            "pm2_5": row.get('pm2_5'),
            "pm10": row.get('pm10'),
            "temperature": row.get('temperature')
        })

    df = pd.DataFrame(readings)
    if df.empty:
        return {"error": "No data available for this sensor in the requested period", "anomalies": []}

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

# ----------------------------
# Serve static frontend files
# ----------------------------
current_dir = os.path.dirname(__file__)
public_dir = os.path.join(current_dir, "public")
if not os.path.exists(public_dir):
    raise RuntimeError(f"Public directory not found: {public_dir}")

app.mount("/static", StaticFiles(directory=public_dir), name="public")

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

# ----------------------------
# Run the app
# ----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
