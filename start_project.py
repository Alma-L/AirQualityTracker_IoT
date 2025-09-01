#!/usr/bin/env python3
"""
Air Quality Tracker IoT - Unified Startup Script
This script starts both the backend server and sensor simulator
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

def run_command(cmd, cwd=None, name="Command"):
    """Run a command and handle output"""
    try:
        print(f"🚀 Starting {name}...")
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start a thread to read output non-blocking
        def read_output():
            try:
                for line in process.stdout:
                    if line:
                        print(f"[{name}] {line.rstrip()}")
            except Exception as e:
                print(f"⚠️  Output reading error for {name}: {e}")
        
        output_thread = threading.Thread(target=read_output, daemon=True)
        output_thread.start()
        
        return process
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def main():
    print("🌬️  Air Quality Tracker IoT - Starting up...")
    print("=" * 50)
    
    # Get the project root directory
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    web_interface_dir = backend_dir / "web-interface"
    
    # Check if required directories exist
    if not web_interface_dir.exists():
        print(f"❌ Web interface directory not found: {web_interface_dir}")
        sys.exit(1)
    
    # Start the FastAPI backend server
    backend_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    backend_process = run_command(backend_cmd, cwd=web_interface_dir, name="Backend Server")
    
    if not backend_process:
        print("❌ Failed to start backend server")
        sys.exit(1)
    
    # Wait a bit for the backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(5)
    
    # Check if backend is running
    if backend_process.poll() is not None:
        print("❌ Backend server failed to start")
        sys.exit(1)
    
    # Start the sensor simulator
    sensor_cmd = [sys.executable, "app.py"]
    sensor_process = run_command(sensor_cmd, cwd=backend_dir, name="Sensor Simulator")
    
    if not sensor_process:
        print("❌ Failed to start sensor simulator")
        backend_process.terminate()
        sys.exit(1)
    
    print("\n✅ All services started successfully!")
    print("🌐 Frontend: http://localhost:8000")
    print("🔌 API: http://localhost:8000/api")
    print("📊 Sensor data will be generated every 30 seconds")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Keep the main thread alive and monitor processes
        while True:
            time.sleep(2)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend server stopped unexpectedly")
                break
            if sensor_process.poll() is not None:
                print("❌ Sensor simulator stopped unexpectedly")
                break
                
            # Print a heartbeat to show the script is still running
            print("💓 Services running... (Press Ctrl+C to stop)")
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
    finally:
        # Cleanup
        if backend_process and backend_process.poll() is None:
            backend_process.terminate()
            print("✅ Backend server stopped")
        if sensor_process and sensor_process.poll() is None:
            sensor_process.terminate()
            print("✅ Sensor simulator stopped")
        print("👋 All services stopped")

if __name__ == "__main__":
    main()
