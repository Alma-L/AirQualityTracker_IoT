import os
os.environ["CASSANDRA_DRIVER_EVENT_LOOP"] = "gevent"

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from random import uniform
import asyncio

from .db_connection import get_cluster_session, init_db

app = FastAPI(title="IoT API (Cassandra)", version="4.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/", include_in_schema=False)
def serve_index():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

# Pydantic model
class SensorReading(BaseModel):
    sensor_id: str
    timestamp: datetime
    pm2_5: float
    pm10: float
    temperature: float
    humidity: float

# Cassandra cluster/session
cluster = None
session = None

@app.on_event("startup")
async def startup_event():
    global cluster, session
    cluster, session = get_cluster_session()
    init_db(session)

    # Seed fake data if empty
    rows = session.execute("SELECT COUNT(*) FROM sensor_readings")
    if rows.one().count == 0:
        for sid in ["sensor-1", "sensor-2", "sensor-3"]:
            simulate_readings(sid, count=10)

    # Start background simulator
    asyncio.create_task(background_simulator())

@app.on_event("shutdown")
def shutdown_event():
    global cluster
    if cluster:
        cluster.shutdown()

# --- API endpoints ---
@app.get("/api/sensors/latest", response_model=List[SensorReading])
def get_latest():
    results = []
    sensors = session.execute("SELECT DISTINCT sensor_id FROM sensor_readings")
    for row in sensors:
        rows = session.execute(
            "SELECT * FROM sensor_readings WHERE sensor_id=%s LIMIT 1",
            [row.sensor_id]
        )
        for r in rows:
            results.append({
                "sensor_id": r.sensor_id,
                "timestamp": r.ts,
                "pm2_5": r.pm2_5,
                "pm10": r.pm10,
                "temperature": r.temperature,
                "humidity": r.humidity,
            })
    return results

@app.get("/api/sensors/{sensor_id}/recent", response_model=List[SensorReading])
def get_recent(sensor_id: str, limit: int = Query(20, ge=1, le=500)):
    rows = session.execute(
        "SELECT * FROM sensor_readings WHERE sensor_id=%s LIMIT %s",
        (sensor_id, limit)
    )
    return [
        {
            "sensor_id": r.sensor_id,
            "timestamp": r.ts,
            "pm2_5": r.pm2_5,
            "pm10": r.pm10,
            "temperature": r.temperature,
            "humidity": r.humidity,
        }
        for r in rows
    ]

@app.post("/api/sensors/{sensor_id}", status_code=201)
def add_reading(sensor_id: str, reading: SensorReading):
    if reading.sensor_id != sensor_id:
        raise HTTPException(status_code=400, detail="sensor_id mismatch")
    session.execute(
        """
        INSERT INTO sensor_readings (sensor_id, ts, pm2_5, pm10, temperature, humidity)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (reading.sensor_id, reading.timestamp, reading.pm2_5,
         reading.pm10, reading.temperature, reading.humidity)
    )
    return {"status": "ok"}

@app.post("/api/simulate/{sensor_id}", status_code=201)
def simulate_readings(sensor_id: str, count: int = Query(10, ge=1, le=100)):
    """
    Insert N fake readings for a sensor (for testing UI without real IoT devices).
    """
    now = datetime.utcnow()
    for i in range(count):
        ts = now - timedelta(seconds=i * 10)  # spaced by 10s
        pm2_5 = round(uniform(5, 50), 2)
        pm10 = round(uniform(10, 100), 2)
        temperature = round(uniform(15, 35), 2)
        humidity = round(uniform(30, 70), 2)

        session.execute(
            """
            INSERT INTO sensor_readings (sensor_id, ts, pm2_5, pm10, temperature, humidity)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (sensor_id, ts, pm2_5, pm10, temperature, humidity)
        )

    return {"status": "ok", "inserted": count}

# --- Background simulator for multiple sensors ---
async def background_simulator():
    """
    Keeps inserting fake data for multiple sensors every 30 seconds.
    """
    sensor_ids = ["sensor-1", "sensor-2", "sensor-3"]
    while True:
        ts = datetime.utcnow()
        for sid in sensor_ids:
            pm2_5 = round(uniform(5, 50), 2)
            pm10 = round(uniform(10, 100), 2)
            temperature = round(uniform(15, 35), 2)
            humidity = round(uniform(30, 70), 2)

            session.execute(
                """
                INSERT INTO sensor_readings (sensor_id, ts, pm2_5, pm10, temperature, humidity)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (sid, ts, pm2_5, pm10, temperature, humidity)
            )
        await asyncio.sleep(30)
