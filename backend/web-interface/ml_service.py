from fastapi import FastAPI, Query, HTTPException
from cassandra.cluster import Cluster
from cassandra.query import dict_factory
from datetime import datetime, timedelta
import pandas as pd
import uvicorn

from ml_algorithms import run_ml_algorithm

app = FastAPI(title="ML Analysis Service")

# ----------------------------
# Cassandra Setup
# ----------------------------
cluster = Cluster(["127.0.0.1"])
session = cluster.connect("air_quality_monitoring")
session.row_factory = dict_factory

SUPPORTED_ALGORITHMS = ["random-forest", "svm", "kmeans"]

# ----------------------------
# ML Analysis Endpoint
# ----------------------------
@app.get("/api/ml-analysis")
async def ml_analysis(
    sensor: str = Query(...),
    algorithm: str = Query("random-forest"),
    hours: int = Query(24)
):
    if algorithm.lower() not in SUPPORTED_ALGORITHMS:
        raise HTTPException(
            status_code=400,
            detail=f"Algorithm '{algorithm}' not supported. Choose from {SUPPORTED_ALGORITHMS}"
        )

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    query = """
        SELECT timestamp, pm2_5, pm10, temperature_celsius AS temp, humidity_percent AS humidity
        FROM air_quality_data
        WHERE sensor_id = %s AND timestamp >= %s
        ORDER BY timestamp DESC
    """
    rows = session.execute(query, [sensor, cutoff_time])

    if not rows:
        return {"error": "No data available for this sensor in the requested period", "anomalies": []}

    readings = []
    for row in rows:
        readings.append({
            "timestamp": row["timestamp"].isoformat() if hasattr(row["timestamp"], "isoformat") else str(row["timestamp"]),
            "pm2_5": row.get("pm2_5"),
            "pm10": row.get("pm10"),
            "temp": row.get("temp"),
            "humidity": row.get("humidity"),
        })

    df = pd.DataFrame(readings)
    if df.empty:
        return {"error": "No data available for this sensor in the requested period", "anomalies": []}

    anomalies = run_ml_algorithm(df, algorithm=algorithm.lower())

    timestamps = df["timestamp"].astype(str).tolist()
    pm25_values = df["pm2_5"].tolist()
    pm10_values = df["pm10"].tolist()
    scores = [1 if ts in [a["timestamp"] for a in anomalies] else 0 for ts in timestamps]

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
        "scores": scores,
    }

if __name__ == "__main__":
    uvicorn.run("ml_service:app", host="0.0.0.0", port=8002, reload=True)
