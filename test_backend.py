#!/usr/bin/env python3
"""
Test script to verify the backend is working
"""

import requests
import json
import time

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Air Quality Tracker IoT Backend...")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/api/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Add sensor data
    test_data = {
        "sensor_id": "test-sensor-1",
        "timestamp": "2024-01-01T12:00:00",
        "pm2_5": 15.5,
        "pm10": 25.0,
        "temperature": 22.5,
        "humidity": 60.0
    }
    
    try:
        response = requests.post(f"{base_url}/api/sensors/test-sensor-1", json=test_data)
        print(f"✅ Add sensor data: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Add sensor data failed: {e}")
        return False
    
    # Test 3: Get latest readings
    try:
        response = requests.get(f"{base_url}/api/sensors/latest")
        print(f"✅ Get latest readings: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Get latest readings failed: {e}")
        return False
    
    # Test 4: Get recent readings for specific sensor
    try:
        response = requests.get(f"{base_url}/api/sensors/test-sensor-1/recent?limit=5")
        print(f"✅ Get recent readings: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Get recent readings failed: {e}")
        return False
    
    # Test 5: Get stats
    try:
        response = requests.get(f"{base_url}/api/stats")
        print(f"✅ Get stats: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Get stats failed: {e}")
        return False
    
    # Test 6: Frontend page
    try:
        response = requests.get(f"{base_url}/")
        print(f"✅ Frontend page: {response.status_code}")
        if response.status_code == 200:
            print("   Frontend is accessible")
        else:
            print("   Frontend not accessible")
    except Exception as e:
        print(f"❌ Frontend test failed: {e}")
    
    print("\n🎉 Backend tests completed!")
    return True

if __name__ == "__main__":
    print("Make sure the backend is running on http://localhost:8000")
    print("You can start it with: python start_simple.py")
    print()
    
    try:
        test_backend()
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
