FROM python:3.9-slim

WORKDIR /app

# Install system dependencies and upgrade packages
RUN apt-get update && apt-get install -y \
    gcc \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy consumer script
COPY kafka_consumer.py .

# Run the consumer
CMD ["python", "kafka_consumer.py"]
