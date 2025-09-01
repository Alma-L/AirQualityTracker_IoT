FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sensor simulator
COPY air_quality_sensor_simulator.py .

# Run the sensor simulator
CMD ["python", "air_quality_sensor_simulator.py"]
