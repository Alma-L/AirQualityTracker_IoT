#!/usr/bin/env python3
"""
Air Quality Tracker IoT - Simple Startup Script
Clean and simple way to start the air quality monitoring system
"""

import subprocess
import sys
import os
import time

def print_banner():
    print("=" * 60)
    print("🌬️  Air Quality Tracker IoT - Kosovo Monitoring")
    print("=" * 60)
    print("Starting the air quality monitoring system...")
    print()

def check_requirements():
    """Check if required packages are installed"""
    try:
        import requests
        print("✅ Required packages found")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def start_backend():
    """Start the backend server"""
    print("🚀 Starting backend server...")
    os.chdir("backend")
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

def main():
    print_banner()
    
    if not check_requirements():
        return
    
    print("📋 Available options:")
    print("1. Start Backend Server")
    print("2. Start Smart Virtual Sensors")
    print("3. Start Both")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        start_backend()
    elif choice == "2":
        print("🤖 Starting Smart Virtual Sensors...")
        os.chdir("backend")
        subprocess.run([sys.executable, "smart_virtual_sensors.py"])
    elif choice == "3":
        print("🚀 Starting both backend and sensors...")
        # Start backend in background
        backend_process = subprocess.Popen([sys.executable, "app.py"], cwd="backend")
        time.sleep(3)  # Wait for backend to start
        # Start sensors
        subprocess.run([sys.executable, "smart_virtual_sensors.py"], cwd="backend")
    else:
        print("❌ Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()
