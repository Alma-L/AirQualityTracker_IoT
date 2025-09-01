import time
import math
import random
import requests
from datetime import datetime

API_URL = "http://localhost:8000/api/sensors"

# Virtual sensor config
SENSOR_ID = "sensor-virtual-1"
BASELINES = {"pm2_5": 25, "pm10": 40, "temperature": 24, "humidity": 55}

def diurnal_variation(base: float, amplitude: float, hour: int) -> float:
    return base + amplitude * math.sin((2 * math.pi / 24) * hour)

def generate_reading():
    now = datetime.utcnow()
    hour = now.hour

    pm2_5 = round(random.gauss(BASELINES["pm2_5"], 5), 2)
    pm10 = round(random.gauss(BASELINES["pm10"], 8), 2)
    temperature = round(diurnal_variation(BASELINES["temperature"], 5, hour) + random.gauss(0, 0.5), 2)
    humidity = round(diurnal_variation(BASELINES["humidity"], 10, (hour + 6) % 24) + random.gauss(0, 2), 2)

    # occasional pollution spikes
    if random.random() < 0.05:
        pm2_5 += random.randint(20, 50)
        pm10 += random.randint(30, 80)

    return {
        "sensor_id": SENSOR_ID,
        "timestamp": now.isoformat(),
        "pm2_5": pm2_5,
        "pm10": pm10,
        "temperature": temperature,
        "humidity": humidity
    }

def main():
    while True:
        reading = generate_reading()
        try:
            r = requests.post(f"{API_URL}/{SENSOR_ID}", json=reading)
            print(f"[{datetime.utcnow()}] Sent: {reading} -> {r.status_code}")
        except Exception as e:
            print("Error sending data:", e)

        time.sleep(30)  # send every 30s

if __name__ == "__main__":
    main()
