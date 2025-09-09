# 🌍 AirQualityTracker_IoT
Air_Monitoring_IoT  

---

## 🔗 Project Link  
Backend runs at: [http://127.0.0.1:5000](http://127.0.0.1:5000)  

---

## ▶️ Start the Project  

1. **Start Cassandra (database)**  
   ```bash
   docker compose up -d

2. **Backend startup** 
   ```bash
   uvicorn backend.app:app --reload --port 5000  

3. **Start Server** 
   ```bash
   cd backend\web-interface 
   npm install  
   node server.js

4. **For machine learning analysis**
   ```bash
   python backend/web-interface/ml_service.py

