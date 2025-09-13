#!/usr/bin/env python3
"""
Smart Virtual Air Quality Sensors
A completely different virtual sensor system with unique sensor types and patterns
"""

import asyncio
import math
import random
import json
import csv
import os
from datetime import datetime, timezone
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class SensorCategory(Enum):
    STATIONARY = "stationary"
    MOBILE = "mobile"
    AERIAL = "aerial"
    UNDERGROUND = "underground"

@dataclass
class SensorReading:
    sensor_id: str
    timestamp: str
    air_quality_index: float
    pm2_5: float
    pm10: float
    temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: float
    sensor_type: str
    location: str
    category: str
    battery_level: float
    signal_strength: float

class SmartVirtualSensors:
    def __init__(self):
        self.sensors = self._initialize_sensors()
        self.data_storage = []
        self.running = False
        
    def _initialize_sensors(self) -> Dict[str, Dict]:
        """Initialize completely different sensor types with unique characteristics"""
        return {
    "smart-prishtina-001": {
        "type": "Capital City Monitor",
        "category": SensorCategory.STATIONARY,
        "location": "Prishtina City Center",
                "baseline_aqi": 45,
                "baseline_pm2_5": 18,
                "baseline_pm10": 28,
                "baseline_temp": 22,
                "baseline_humidity": 65,
                "baseline_pressure": 1013,
                "variation_factor": 0.3,
                "update_interval": 45,
                "battery_capacity": 100,
                "signal_base": 85,
                "environmental_factors": ["vegetation", "traffic_proximity", "weather"]
            },
    "smart-peja-002": {
        "type": "Industrial Monitor",
        "category": SensorCategory.STATIONARY,
        "location": "Peja Industrial Zone",
                "baseline_aqi": 65,
                "baseline_pm2_5": 28,
                "baseline_pm10": 45,
                "baseline_temp": 25,
                "baseline_humidity": 55,
                "baseline_pressure": 1012,
                "variation_factor": 0.5,
                "update_interval": 30,
                "battery_capacity": 100,
                "signal_base": 90,
                "environmental_factors": ["traffic_density", "construction", "time_of_day"]
            },
    "smart-prizren-003": {
        "type": "Historic City Monitor",
        "category": SensorCategory.STATIONARY,
        "location": "Prizren Historic District",
                "baseline_aqi": 55,
                "baseline_pm2_5": 22,
                "baseline_pm10": 35,
                "baseline_temp": 24,
                "baseline_humidity": 60,
                "baseline_pressure": 1013,
                "variation_factor": 0.7,
                "update_interval": 20,
                "battery_capacity": 100,
                "signal_base": 75,
                "environmental_factors": ["route_type", "speed", "traffic_conditions"]
            },
    "smart-gjakova-004": {
        "type": "Mobile Monitor",
        "category": SensorCategory.MOBILE,
        "location": "Gjakova Bus Route",
                "baseline_aqi": 40,
                "baseline_pm2_5": 15,
                "baseline_pm10": 25,
                "baseline_temp": 20,
                "baseline_humidity": 70,
                "baseline_pressure": 1000,
                "variation_factor": 0.4,
                "update_interval": 15,
                "battery_capacity": 100,
                "signal_base": 95,
                "environmental_factors": ["altitude", "weather_conditions", "flight_pattern"]
            },
    "smart-mitrovica-005": {
        "type": "Aerial Survey",
        "category": SensorCategory.AERIAL,
        "location": "Mitrovica Airspace",
                "baseline_aqi": 75,
                "baseline_pm2_5": 35,
                "baseline_pm10": 55,
                "baseline_temp": 28,
                "baseline_humidity": 80,
                "baseline_pressure": 1020,
                "variation_factor": 0.6,
                "update_interval": 35,
                "battery_capacity": 100,
                "signal_base": 60,
                "environmental_factors": ["passenger_flow", "train_frequency", "ventilation"]
            },
    "smart-ferizaj-006": {
        "type": "Underground Monitor",
        "category": SensorCategory.UNDERGROUND,
        "location": "Ferizaj Underground Street",
                "baseline_aqi": 50,
                "baseline_pm2_5": 20,
                "baseline_pm10": 32,
                "baseline_temp": 23,
                "baseline_humidity": 65,
                "baseline_pressure": 1014,
                "variation_factor": 0.8,
                "update_interval": 25,
                "battery_capacity": 100,
                "signal_base": 70,
                "environmental_factors": ["cycling_speed", "route_elevation", "traffic_exposure"]
            },
    "smart-gjilan-007": {
        "type": "Urban Monitor",
        "category": SensorCategory.STATIONARY,
        "location": "Gjilan City Center",
                "baseline_aqi": 50,
                "baseline_pm2_5": 20,
                "baseline_pm10": 32,
                "baseline_temp": 23,
                "baseline_humidity": 65,
                "baseline_pressure": 1014,
                "variation_factor": 0.7,
                "update_interval": 30,
                "battery_capacity": 100,
                "signal_base": 75,
                "environmental_factors": ["urban_heat", "traffic_density", "industrial_proximity"]
            },
    "smart-vushtrri-008": {
        "type": "Residential Monitor",
        "category": SensorCategory.STATIONARY,
        "location": "Vushtrri Residential Area",
                "baseline_aqi": 42,
                "baseline_pm2_5": 17,
                "baseline_pm10": 29,
                "baseline_temp": 21,
                "baseline_humidity": 68,
                "baseline_pressure": 1012,
                "variation_factor": 0.6,
                "update_interval": 40,
                "battery_capacity": 100,
                "signal_base": 80,
                "environmental_factors": ["residential_heating", "local_traffic", "weather_patterns"]
            }
        }

    def _calculate_environmental_modifier(self, sensor_id: str, sensor_config: Dict) -> float:
        """Calculate environmental modifier based on unique factors for each sensor"""
        now = datetime.now(timezone.utc)
        hour = now.hour
        day_of_week = now.weekday()
        
        base_modifier = 1.0
        factors = sensor_config["environmental_factors"]
        
        # Time-based patterns
        if "time_of_day" in factors:
            if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
                base_modifier *= 1.4
            elif 22 <= hour or hour <= 6:  # Night time
                base_modifier *= 0.7
            else:
                base_modifier *= 1.0
        
        # Day of week patterns
        if "traffic_density" in factors:
            if day_of_week < 5:  # Weekdays
                base_modifier *= 1.2
            else:  # Weekends
                base_modifier *= 0.8
        
        # Weather simulation
        if "weather_conditions" in factors:
            weather_factor = random.uniform(0.8, 1.3)
            base_modifier *= weather_factor
        
        # Traffic patterns
        if "traffic_proximity" in factors:
            traffic_factor = random.uniform(0.9, 1.5)
            base_modifier *= traffic_factor
        
        # Construction activity
        if "construction" in factors:
            if random.random() < 0.1:  # 10% chance of construction activity
                base_modifier *= 1.6
        
        # Passenger flow (for underground)
        if "passenger_flow" in factors:
            if 7 <= hour <= 9 or 17 <= hour <= 19:
                base_modifier *= 1.3
        
        return base_modifier

    def _simulate_sensor_reading(self, sensor_id: str, sensor_config: Dict) -> SensorReading:
        """Generate a realistic sensor reading with unique patterns"""
        now = datetime.now(timezone.utc)
        
        # Get environmental modifier
        env_modifier = self._calculate_environmental_modifier(sensor_id, sensor_config)
        
        # Base values with environmental influence
        base_aqi = sensor_config["baseline_aqi"] * env_modifier
        base_pm2_5 = sensor_config["baseline_pm2_5"] * env_modifier
        base_pm10 = sensor_config["baseline_pm10"] * env_modifier
        base_temp = sensor_config["baseline_temp"]
        base_humidity = sensor_config["baseline_humidity"]
        base_pressure = sensor_config["baseline_pressure"]
        
        # Add realistic variations
        variation = sensor_config["variation_factor"]
        
        aqi = max(0, random.gauss(base_aqi, base_aqi * variation))
        pm2_5 = max(0, random.gauss(base_pm2_5, base_pm2_5 * variation))
        pm10 = max(0, random.gauss(base_pm10, base_pm10 * variation))
        temperature = random.gauss(base_temp, 2)
        humidity = max(0, min(100, random.gauss(base_humidity, 5)))
        pressure = random.gauss(base_pressure, 5)
        
        # Wind simulation (only for outdoor sensors)
        wind_speed = 0
        wind_direction = 0
        if sensor_config["category"] != SensorCategory.UNDERGROUND:
            wind_speed = random.uniform(0, 15)
            wind_direction = random.uniform(0, 360)
        
        # Battery simulation (decreases over time)
        battery_drain = random.uniform(0.1, 0.3)
        sensor_config["battery_capacity"] = max(0, sensor_config["battery_capacity"] - battery_drain)
        
        # Signal strength simulation
        signal_strength = max(0, sensor_config["signal_base"] + random.uniform(-10, 5))
        
        return SensorReading(
            sensor_id=sensor_id,
            timestamp=now.isoformat(),
            air_quality_index=round(aqi, 1),
            pm2_5=round(pm2_5, 2),
            pm10=round(pm10, 2),
            temperature=round(temperature, 1),
            humidity=round(humidity, 1),
            pressure=round(pressure, 1),
            wind_speed=round(wind_speed, 1),
            wind_direction=round(wind_direction, 1),
            sensor_type=sensor_config["type"],
            location=sensor_config["location"],
            category=sensor_config["category"].value,
            battery_level=round(sensor_config["battery_capacity"], 1),
            signal_strength=round(signal_strength, 1)
        )

    async def _run_sensor(self, sensor_id: str, sensor_config: Dict):
        """Run a single sensor simulation"""
        while self.running:
            try:
                reading = self._simulate_sensor_reading(sensor_id, sensor_config)
                
                # Store the reading
                self.data_storage.append(reading)
                
                # Keep only last 1000 readings to prevent memory issues
                if len(self.data_storage) > 1000:
                    self.data_storage = self.data_storage[-1000:]
                
                # Print status
                print(f"🌡️  {sensor_config['type']} ({sensor_id}): "
                      f"AQI={reading.air_quality_index}, PM2.5={reading.pm2_5}, "
                      f"Temp={reading.temperature}°C, Battery={reading.battery_level}%")
                
                await asyncio.sleep(sensor_config["update_interval"])
                
            except Exception as e:
                print(f"❌ Error in sensor {sensor_id}: {e}")
                await asyncio.sleep(5)

    def save_data_to_csv(self, filename: str = "smart_sensor_data.csv"):
        """Save sensor data to CSV file"""
        if not self.data_storage:
            print("No data to save")
            return
        
        fieldnames = [
            'sensor_id', 'timestamp', 'air_quality_index', 'pm2_5', 'pm10',
            'temperature', 'humidity', 'pressure', 'wind_speed', 'wind_direction',
            'sensor_type', 'location', 'category', 'battery_level', 'signal_strength'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for reading in self.data_storage:
                writer.writerow(reading.__dict__)
        
        print(f"💾 Data saved to {filename} ({len(self.data_storage)} readings)")

    def get_latest_readings(self) -> List[Dict]:
        """Get latest reading from each sensor"""
        latest = {}
        for reading in self.data_storage:
            latest[reading.sensor_id] = reading.__dict__
        return list(latest.values())

    def get_sensor_statistics(self) -> Dict:
        """Get statistics for all sensors"""
        if not self.data_storage:
            return {"error": "No data available"}
        
        stats = {}
        for sensor_id in self.sensors.keys():
            sensor_readings = [r for r in self.data_storage if r.sensor_id == sensor_id]
            if sensor_readings:
                aqi_values = [r.air_quality_index for r in sensor_readings]
                pm2_5_values = [r.pm2_5 for r in sensor_readings]
                
                stats[sensor_id] = {
                    "total_readings": len(sensor_readings),
                    "avg_aqi": round(sum(aqi_values) / len(aqi_values), 1),
                    "max_aqi": round(max(aqi_values), 1),
                    "min_aqi": round(min(aqi_values), 1),
                    "avg_pm2_5": round(sum(pm2_5_values) / len(pm2_5_values), 2),
                    "current_battery": sensor_readings[-1].battery_level,
                    "current_signal": sensor_readings[-1].signal_strength
                }
        
        return stats

    async def start_simulation(self):
        """Start the virtual sensor simulation"""
        print("🚀 Smart Virtual Air Quality Sensors Starting...")
        print("=" * 60)
        
        # Display sensor information
        for sensor_id, config in self.sensors.items():
            print(f"📡 {config['type']}: {sensor_id}")
            print(f"   Location: {config['location']}")
            print(f"   Category: {config['category'].value}")
            print(f"   Update Interval: {config['update_interval']}s")
            print(f"   Environmental Factors: {', '.join(config['environmental_factors'])}")
            print()
        
        print("🌬️  Starting all sensors...")
        print("Press Ctrl+C to stop all sensors")
        print("=" * 60)
        
        self.running = True
        
        # Start all sensors concurrently
        tasks = [
            asyncio.create_task(self._run_sensor(sensor_id, config))
            for sensor_id, config in self.sensors.items()
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down smart virtual sensors...")
            self.running = False
            print("✅ All sensor tasks stopped")
            
            # Save data before exiting
            self.save_data_to_csv()
            
            # Print final statistics
            stats = self.get_sensor_statistics()
            print("\n📊 Final Statistics:")
            for sensor_id, stat in stats.items():
                print(f"   {sensor_id}: {stat['total_readings']} readings, "
                      f"Avg AQI: {stat['avg_aqi']}, Battery: {stat['current_battery']}%")

async def main():
    """Main function to start the smart virtual sensor system"""
    sensor_system = SmartVirtualSensors()
    await sensor_system.start_simulation()

if __name__ == "__main__":
    asyncio.run(main())
