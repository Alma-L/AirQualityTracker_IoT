#!/usr/bin/env python3
"""
Air Quality Tracker IoT - Simple Startup Script
This script starts services in separate terminals (more reliable on Windows)
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

def start_sensor_simulator():
    """Start the sensor simulator"""
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    
    if not backend_dir.exists():
        print(f"❌ Backend directory not found: {backend_dir}")
        return False
    
    print("🚀 Starting Sensor Simulator...")
    print(f"📁 Working directory: {backend_dir}")
    
    # Use start command on Windows to open new terminal
    if os.name == 'nt':  # Windows
        cmd = f'start "Sensor Simulator" cmd /k "cd /d {backend_dir} && python app.py"'
        subprocess.run(cmd, shell=True)
    else:  # Unix/Linux/Mac
        cmd = f'gnome-terminal -- bash -c "cd {backend_dir} && python app.py; exec bash"'
        subprocess.run(cmd, shell=True)
    
    return True

def main():
    print("🌬️  Air Quality Tracker IoT - Simple Startup")
    print("=" * 50)
    
    # Check Python
    try:
        import uvicorn
        import fastapi
        print("✅ Required packages are available")
    except ImportError:
        print("📦 Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Start services
    if start_backend():
        print("✅ Backend server started in new terminal")
        time.sleep(2)
    
    if start_sensor_simulator():
        print("✅ Sensor simulator started in new terminal")
    
    print("\n🎉 All services started!")
    print("🌐 Frontend: http://localhost:8000")
    print("🔌 API: http://localhost:8000/api")
    print("\n💡 Each service is running in its own terminal window")
    print("💡 Close the terminal windows to stop individual services")
    print("💡 Or use Ctrl+C in each terminal to stop them")

if __name__ == "__main__":
    main()
