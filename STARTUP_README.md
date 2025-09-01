# 🚀 Air Quality Tracker IoT - Quick Start

## ✅ **CURRENT STATUS: ALL ISSUES FIXED!**
The backend connection issues have been resolved. All the "undefined" values, disconnected status, and empty data tables have been fixed.

## 🔧 **Issues That Were Fixed:**

1. **✅ Status: Disconnected** → Now shows "Connected" when backend is running
2. **✅ Statistics showing "undefined"** → Now displays actual sensor counts and readings
3. **✅ Historic data table empty** → Now shows real sensor data
4. **✅ Data structure mismatch** → Frontend and backend now use compatible data formats
5. **✅ Missing HTML elements** → All required elements now have proper IDs
6. **✅ Table column mismatch** → Table headers now match the actual data

## Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

## 🎯 One-Command Startup

### Option 1: Windows Batch File (Recommended for Windows)
```bash
start_project.bat
```

### Option 2: PowerShell Script
```powershell
.\start_project.ps1
```

### Option 3: Simple Python Script (Most Reliable)
```bash
python start_simple.py
```

### Option 4: Advanced Python Script (Single Terminal)
```bash
python start_project.py
```

## 🔧 Manual Startup (if needed)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Backend Server
```bash
cd backend/web-interface
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start Sensor Simulator (in new terminal)
```bash
cd backend
python app.py
```

## 🌐 Access Your Application

- **Frontend**: http://localhost:8000
- **API**: http://localhost:8000/api
- **Health Check**: http://localhost:8000/api/health
- **Test Page**: test_frontend.html (for debugging)

## 📊 What Happens When You Start

1. ✅ **Backend Server** starts on port 8000
2. ✅ **Frontend** is served from the backend
3. ✅ **Sensor Simulator** generates air quality data every 30 seconds
4. ✅ **Real-time updates** in the web interface
5. ✅ **Statistics display** actual sensor counts and readings
6. ✅ **Data tables** show real sensor data

## 🧪 Testing Your Setup

### **Quick Test (Recommended)**
After starting the services, open this test page:
```
test_frontend.html
```

This will verify all API connections are working.

### **Backend Test**
```bash
python test_backend.py
```

### **Manual API Test**
```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/stats
curl http://localhost:8000/api/sensors/latest
```

## 🚀 Startup Script Differences

### `start_simple.py` (Recommended)
- **Opens separate terminal windows** for each service
- **More reliable** on Windows systems
- **Easier to debug** - each service has its own window
- **Easier to stop** - just close the terminal windows

### `start_project.py` (Advanced)
- **Single terminal** for all services
- **Integrated output** from all services
- **Single Ctrl+C** stops everything
- **May have encoding issues** on some Windows systems

## 🛑 Stopping the Application

### With Simple Startup Script:
- **Close the terminal windows** for individual services
- **Or use Ctrl+C** in each terminal window

### With Advanced Startup Script:
- **Press Ctrl+C** in the main terminal

## 🔍 Troubleshooting

### ✅ **All Previous Issues Are Now Fixed:**
- **Status shows "Connected"** when backend is running
- **Statistics display real numbers** instead of "undefined"
- **Data tables show actual sensor readings**
- **Frontend properly connects to backend**

### Port 8000 already in use?
```bash
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

### Python not found?
- Make sure Python is installed and added to PATH
- Try using `python3` instead of `python`

### Package installation fails?
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Then install requirements
pip install -r requirements.txt
```

### Still seeing issues?
1. **Check if backend is running**: `curl http://localhost:8000/api/health`
2. **Test frontend**: Open `test_frontend.html` in your browser
3. **Check browser console** for JavaScript errors
4. **Verify sensor simulator** is running and generating data

## 📁 Project Structure

```
AirQualityTracker_IoT/
├── frontend/                 # Frontend files (HTML, CSS, JS)
├── backend/
│   ├── web-interface/       # FastAPI backend server
│   │   ├── main.py         # ✅ FastAPI application (FIXED!)
│   │   └── public/         # Frontend files served by backend
│   ├── app.py              # Sensor simulator
│   └── requirements.txt    # Backend dependencies
├── start_simple.py         # Simple startup script (recommended)
├── start_project.py        # Advanced startup script
├── start_project.bat       # Windows batch file
├── start_project.ps1       # PowerShell script
├── test_backend.py         # 🧪 Test script for verification
├── test_frontend.html      # 🧪 Frontend test page
└── requirements.txt        # Main project dependencies
```

## 🎉 You're Ready!

After starting the application, you'll see:
- ✅ **Real-time air quality data** from virtual sensors
- ✅ **Interactive web interface** with live updates
- ✅ **API endpoints** for data access
- ✅ **Automatic data generation** every 30 seconds
- ✅ **Proper statistics display** showing actual numbers
- ✅ **Connected status** when backend is running
- ✅ **Populated data tables** with real sensor readings

The frontend will automatically connect to the backend and display live sensor data!

## 💡 Pro Tips

1. **Start with `start_simple.py`** - it's the most reliable option
2. **Each service gets its own terminal** - easier to monitor and debug
3. **Close terminal windows** to stop individual services
4. **Use the batch file** for the easiest Windows experience
5. **Test with `test_frontend.html`** to verify everything is working
6. **Check the terminal outputs** for any error messages
7. **Refresh the page** if you don't see data immediately

## 🔧 Recent Fixes Applied

- ✅ **Recreated missing `main.py`** file in `backend/web-interface/`
- ✅ **Updated frontend connection** to use correct backend URL
- ✅ **Fixed API endpoint mapping** between frontend and backend
- ✅ **Added comprehensive error handling** in frontend
- ✅ **Created test script** for backend verification
- ✅ **Fixed data structure mismatch** between frontend and backend
- ✅ **Corrected HTML element IDs** for proper JavaScript functionality
- ✅ **Fixed table column structure** to match actual data
- ✅ **Added proper statistics display** with real-time updates
- ✅ **Created frontend test page** for debugging
