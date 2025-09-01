#!/usr/bin/env python3
"""
Test script for Multi-Sensor Air Quality Tracker IoT
Verifies that all 3 sensors are working and generating data
"""

import requests
import time
import json

API_BASE = "http://localhost:8000/api"

def test_health():
    """Test backend health"""
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Health: {data['status']}")
            print(f"   Version: {data['version']}")
            print(f"   Uptime: {data['uptime']}")
            return True
        else:
            print(f"❌ Backend Health Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Health Error: {e}")
        return False

def test_stats():
    """Test system statistics"""
    try:
        response = requests.get(f"{API_BASE}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 System Statistics:")
            print(f"   Active Sensors: {data['sensor_count']}")
            print(f"   Total Readings: {data['total_readings']}")
            print(f"   Active Alerts: {data['active_alerts']}")
            print(f"   Average AQI: {data['average_aqi']}")
            print(f"   Active Sensors: {', '.join(data['sensors'])}")
            return True
        else:
            print(f"❌ Stats Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats Error: {e}")
        return False

def test_sensor_data():
    """Test sensor data for each sensor"""
    sensors = ["sensor-urban-1", "sensor-industrial-1", "sensor-residential-1"]
    
    print(f"\n📡 Testing Sensor Data:")
    
    for sensor_id in sensors:
        try:
            # Test recent data
            response = requests.get(f"{API_BASE}/sensors/{sensor_id}/recent?limit=5")
            if response.status_code == 200:
                data = response.json()
                if data:
                    latest = data[0]
                    print(f"   ✅ {sensor_id}: {len(data)} readings")
                    print(f"      Latest: PM2.5={latest['pm2_5']}, PM10={latest['pm10']}, "
                          f"Temp={latest['temperature']}°C, Humidity={latest['humidity']}%")
                    if 'aqi' in latest:
                        print(f"      AQI: {latest['aqi']} ({latest.get('aqi_category', 'Unknown')})")
                    if 'sensor_type' in latest:
                        print(f"      Type: {latest['sensor_type']} - {latest.get('location', 'Unknown')}")
                else:
                    print(f"   ⚠️  {sensor_id}: No data yet")
            else:
                print(f"   ❌ {sensor_id}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {sensor_id}: Error - {e}")

def test_alerts():
    """Test alerts endpoint"""
    try:
        response = requests.get(f"{API_BASE}/alerts?limit=5")
        if response.status_code == 200:
            alerts = response.json()
            print(f"\n🚨 Alerts: {len(alerts)} recent alerts")
            for alert in alerts[:3]:  # Show first 3
                print(f"   • {alert['type']} ({alert['severity']}): {alert['message']}")
        else:
            print(f"❌ Alerts Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Alerts Error: {e}")

def test_analytics():
    """Test analytics for urban sensor"""
    try:
        response = requests.get(f"{API_BASE}/analytics/sensor-urban-1?hours=24")
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data:
                print(f"\n📈 Analytics for sensor-urban-1:")
                print(f"   PM2.5: Min={data['pm25']['min']}, Max={data['pm25']['max']}, Avg={data['pm25']['average']}")
                print(f"   PM10: Min={data['pm10']['min']}, Max={data['pm10']['max']}, Avg={data['pm10']['average']}")
                print(f"   AQI: Min={data['aqi']['min']}, Max={data['aqi']['max']}, Avg={data['aqi']['average']}")
                print(f"   Period: {data['time_period_hours']} hours, {data['readings_count']} readings")
            else:
                print(f"⚠️  Analytics: {data['error']}")
        else:
            print(f"❌ Analytics Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Analytics Error: {e}")

def main():
    print("🧪 Multi-Sensor Air Quality Tracker IoT - System Test")
    print("=" * 60)
    
    # Wait for system to start
    print("⏳ Waiting for system to start up...")
    time.sleep(5)
    
    # Run tests
    if test_health():
        test_stats()
        test_sensor_data()
        test_alerts()
        test_analytics()
        
        print(f"\n🎉 System Test Complete!")
        print(f"🌐 Frontend: http://localhost:8000")
        print(f"💡 Check the web interface to see all 3 sensors in action!")
    else:
        print("❌ System not ready. Please wait and try again.")

if __name__ == "__main__":
    main()
