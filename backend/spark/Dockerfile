FROM python:3.9-slim

WORKDIR /app

    # Install system dependencies
    RUN apt-get update && apt-get install -y \
        gcc \
        default-jdk \
        && rm -rf /var/lib/apt/lists/*

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$PATH:$JAVA_HOME/bin

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Spark streaming script
COPY spark_streaming.py .

# Run the Spark streaming application
CMD ["python", "spark_streaming.py"]
