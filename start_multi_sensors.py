#!/usr/bin/env python3
"""
Air Quality Tracker IoT - Multi-Sensor Startup Script
This script starts the backend server and multi-sensor simulator
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_backend():
    """Start the backend server"""
    project_root = Path(__file__).parent
    web_interface_dir = project_root / "backend" / "web-interface"
    
    if not web_interface_dir.exists():
        print(f"❌ Web interface directory not found: {web_interface_dir}")
        return False
    
    print("🚀 Starting Backend Server...")
    print(f"📁 Working directory: {web_interface_dir}")
    
    # Use start command on Windows to open new terminal
    if os.name == 'nt':  # Windows
        cmd = f'start "Backend Server" cmd /k "cd /d {web_interface_dir} && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"'
        subprocess.run(cmd, shell=True)
    else:  # Unix/Linux/Mac
        cmd = f'gnome-terminal -- bash -c "cd {web_interface_dir} && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload; exec bash"'
        subprocess.run(cmd, shell=True)
    
    return True

def start_multi_sensors():
    """Start the multi-sensor simulator"""
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    print("🚀 Starting Multi-Sensor Simulator...")
    print(f"📁 Working directory: {backend_dir}")
    
    # Use start command on Windows to open new terminal
    if os.name == 'nt':  # Windows
        cmd = f'start "Multi-Sensor Simulator" cmd /k "cd /d {backend_dir} && python multi_sensor_simulator.py"'
        subprocess.run(cmd, shell=True)
    else:  # Unix/Linux/Mac
        cmd = f'gnome-terminal -- bash -c "cd {backend_dir} && python multi_sensor_simulator.py; exec bash"'
        subprocess.run(cmd, shell=True)
    
    return True

def main():
    print("🌬️  Air Quality Tracker IoT - Multi-Sensor Startup")
    print("=" * 60)
    
    # Check Python
    try:
        import uvicorn
        import fastapi
        import requests
        print("✅ Required packages are available")
    except ImportError:
        print("📦 Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Start services
    if start_backend():
        print("✅ Backend server started in new terminal")
        time.sleep(3)  # Wait for backend to start
    
    if start_multi_sensors():
        print("✅ Multi-sensor simulator started in new terminal")
    
    print("\n🎉 All services started!")
    print("🌐 Frontend: http://localhost:8000")
    print("🔌 API: http://localhost:8000/api")
    print("\n📡 Active Sensors:")
    print("   🏙️  Urban Sensor (sensor-urban-1) - City Center")
    print("   🏭 Industrial Sensor (sensor-industrial-1) - Factory Zone")
    print("   🏘️  Residential Sensor (sensor-residential-1) - Suburban Area")
    print("\n💡 Each service is running in its own terminal window")
    print("💡 Close the terminal windows to stop individual services")
    print("💡 Or use Ctrl+C in each terminal to stop them")

if __name__ == "__main__":
    main()
