import asyncio
import math
import random
import requests
from datetime import datetime

API_URL = "http://127.0.0.1:8000/api/sensors"  # Change if backend runs elsewhere

# Define multiple sensors with different baselines
SENSORS = {
    "sensor-virtual-1": {"pm2_5": 25, "pm10": 40, "temperature": 24, "humidity": 55},
    "sensor-virtual-2": {"pm2_5": 35, "pm10": 55, "temperature": 22, "humidity": 60},
    "sensor-virtual-3": {"pm2_5": 18, "pm10": 30, "temperature": 26, "humidity": 45},
}


def diurnal_variation(base: float, amplitude: float, hour: int) -> float:
    """Simulate daily cycle (sinusoidal variation)."""
    return base + amplitude * math.sin((2 * math.pi / 24) * hour)


def generate_reading(sensor_id: str, profile: dict):
    now = datetime.utcnow()
    hour = now.hour

    pm2_5 = round(random.gauss(profile["pm2_5"], 5), 2)
    pm10 = round(random.gauss(profile["pm10"], 8), 2)
    temperature = round(diurnal_variation(profile["temperature"], 5, hour) + random.gauss(0, 0.5), 2)
    humidity = round(diurnal_variation(profile["humidity"], 10, (hour + 6) % 24) + random.gauss(0, 2), 2)

    # occasional pollution spikes
    if random.random() < 0.05:
        pm2_5 += random.randint(20, 50)
        pm10 += random.randint(30, 80)

    return {
        "sensor_id": sensor_id,
        "timestamp": now.isoformat(),
        "pm2_5": pm2_5,
        "pm10": pm10,
        "temperature": temperature,
        "humidity": humidity,
    }


async def run_sensor(sensor_id: str, profile: dict):
    """Simulate one sensor sending data forever."""
    while True:
        reading = generate_reading(sensor_id, profile)
        try:
            r = requests.post(f"{API_URL}/{sensor_id}", json=reading)
            print(f"[{datetime.utcnow()}] {sensor_id} -> {r.status_code} | {reading}")
        except Exception as e:
            print(f"Error sending data for {sensor_id}: {e}")

        await asyncio.sleep(30)  # send every 30s


async def main():
    tasks = [asyncio.create_task(run_sensor(sid, profile)) for sid, profile in SENSORS.items()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
