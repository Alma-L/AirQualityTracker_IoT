const API_BASE = "http://localhost:3001/api";

let ws = null;
let isConnected = false;
let sparkRunning = false;

// WebSocket connection
function connectWebSocket() {
  try {
    ws = new WebSocket(`ws://localhost:3001`);

    ws.onopen = function () {
      console.log("🔌 WebSocket connected to Spark server");
      isConnected = true;
      updateConnectionStatus("Connected", "success");
    };

    ws.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);

        if (data.type === "realtime_update") {
          updateRealTimeData(data.data);
        } else if (data.type === "alerts_update") {
          updateAlerts(data.alerts);
        }

        updateConnectionStatus("Connected", "success");
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.onclose = function () {
      console.log("🔌 WebSocket disconnected");
      isConnected = false;
      updateConnectionStatus("Disconnected", "error");
      setTimeout(connectWebSocket, 5000);
    };

    ws.onerror = function (error) {
      console.error("WebSocket error:", error);
      updateConnectionStatus("Error", "error");
    };
  } catch (error) {
    console.error("WebSocket connection failed:", error);
    updateConnectionStatus("WebSocket Error", "error");
  }
}

// Update connection status
function updateConnectionStatus(status, type) {
  const statusElement = document.getElementById("connectionStatus");
  if (statusElement) {
    statusElement.textContent = status;
    statusElement.className = `status ${type}`;
  }
}

// Update real-time data display
function updateRealTimeData(data) {
  console.log("Updating real-time data:", data);
  
  // Update latest readings grid
  const grid = document.getElementById("latestGrid");
  if (grid) {
    // This would update the grid with new data
    // Implementation depends on your HTML structure
  }
  
  // Update statistics
  loadStats();
}

// Load main statistics
async function loadStats() {
  try {
    const data = await fetchJSON(`${API_BASE}/stats`);
    
    // Update main stats
    document.getElementById("activeSensors").textContent = data.sensorCount || 0;
    document.getElementById("totalReadings").textContent = data.totalRecords || 0;
    document.getElementById("activeAlerts").textContent = data.activeAlerts || 0;
    
    const uptimeHours = Math.floor((data.uptimeSeconds || 0) / 3600);
    const uptimeMinutes = Math.floor(((data.uptimeSeconds || 0) % 3600) / 60);
    document.getElementById("uptime").textContent = `${uptimeHours}h ${uptimeMinutes}m`;
    
    // Update average AQI
    document.getElementById("averageAQI").textContent = 
      data.averageAQI !== undefined ? data.averageAQI.toFixed(1) : "N/A";
    
    // Update Spark status
    const sparkStatus = document.getElementById("sparkStatus");
    if (sparkStatus) {
      sparkStatus.textContent = data.spark_running ? "Running" : "Stopped";
      sparkStatus.className = `status ${data.spark_running ? "success" : "error"}`;
    }
    
  } catch (err) {
    console.error("Error loading stats:", err);
    document.getElementById("activeSensors").textContent = "Error";
    document.getElementById("totalReadings").textContent = "Error";
    document.getElementById("activeAlerts").textContent = "Error";
    document.getElementById("uptime").textContent = "Error";
    document.getElementById("averageAQI").textContent = "Error";
  }
}

// Load sensors
async function loadSensors() {
  try {
    const res = await fetch(`${API_BASE}/sensors`);
    if (!res.ok) throw new Error("Failed to load sensors");
    
    let sensors = await res.json();
    
    if (sensors.sensors) {
      sensors = sensors.sensors;
    }
    
    const sensorSelect = document.getElementById("sensor-id");
    if (sensorSelect) {
      sensorSelect.innerHTML = "";
      
      sensors.forEach((sensor) => {
        const sensorId = typeof sensor === "string" ? sensor : sensor.id;
        const option = document.createElement("option");
        option.value = sensorId;
        option.textContent = sensorId;
        sensorSelect.appendChild(option);
      });
      
      if (sensors.length > 0) {
        const firstSensorId = typeof sensors[0] === "string" ? sensors[0] : sensors[0].id;
        loadRecent(firstSensorId, 20);
        loadAnalytics(firstSensorId, 24);
      }
    }
  } catch (err) {
    console.error("Error loading sensors:", err);
  }
}

// Load analytics
async function loadAnalytics(sensorId, hours = 24) {
  try {
    const response = await fetch(`${API_BASE}/analytics/${sensorId}?hours=${hours}`);
    
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`HTTP ${response.status} ${response.statusText}: ${text}`);
    }
    
    const analytics = await response.json();
    updateAnalyticsDisplay(analytics);
  } catch (err) {
    console.error("Error loading analytics:", err);
    const analyticsElement = document.getElementById("analytics");
    if (analyticsElement) {
      analyticsElement.innerHTML = `<p class="error">Error loading analytics: ${err.message}</p>`;
    }
  }
}

// Update analytics display
function updateAnalyticsDisplay(analytics) {
  const analyticsContent = document.getElementById("analyticsContent");
  if (!analyticsContent) return;
  
  if (analytics.error) {
    analyticsContent.innerHTML = `<p class="error">${analytics.error}</p>`;
    return;
  }
  
  analyticsContent.innerHTML = `
    <div class="analytics-grid">
      <div class="analytics-card">
        <h4>PM2.5 Statistics</h4>
        <div class="stat-row"><span>Min:</span> <span class="value">${analytics.pm25.min}</span></div>
        <div class="stat-row"><span>Max:</span> <span class="value">${analytics.pm25.max}</span></div>
        <div class="stat-row"><span>Average:</span> <span class="value">${analytics.pm25.average}</span></div>
      </div>
      <div class="analytics-card">
        <h4>PM10 Statistics</h4>
        <div class="stat-row"><span>Min:</span> <span class="value">${analytics.pm10.min}</span></div>
        <div class="stat-row"><span>Max:</span> <span class="value">${analytics.pm10.max}</span></div>
        <div class="stat-row"><span>Average:</span> <span class="value">${analytics.pm10.average}</span></div>
      </div>
      <div class="analytics-card">
        <h4>AQI Statistics</h4>
        <div class="stat-row"><span>Min:</span> <span class="value">${analytics.aqi.min}</span></div>
        <div class="stat-row"><span>Max:</span> <span class="value">${analytics.aqi.max}</span></div>
        <div class="stat-row"><span>Average:</span> <span class="value">${analytics.aqi.average}</span></div>
      </div>
    </div>
    <div class="analytics-summary">
      <p><strong>Period:</strong> Last ${analytics.time_period_hours} hours</p>
      <p><strong>Readings:</strong> ${analytics.readings_count} data points</p>
      <p><strong>Trend:</strong> ${analytics.trend}</p>
    </div>
  `;
}

// Load recent readings
async function loadRecent(sensorId, limit) {
  const tbody = document.querySelector("#recent-table tbody");
  if (!tbody) return;
  
  tbody.innerHTML = "<tr><td colspan='6'>Loading...</td></tr>";
  
  try {
    const data = await fetchJSON(`${API_BASE}/sensors/${encodeURIComponent(sensorId)}/recent?limit=${limit}`);
    tbody.innerHTML = "";
    
    data.forEach((row) => {
      const d = new Date(row.timestamp);
      const tr = document.createElement("tr");
      const aqi = row.aqi || "N/A";
      const aqiClass = row.aqi ? getAQIClass(row.aqi) : "";
      
      tr.innerHTML = `
        <td>${row.pm2_5}</td>
        <td>${row.pm10}</td>
        <td class="${aqiClass}">${aqi}</td>
        <td>${row.temperature_celsius}</td>
        <td>${row.humidity_percent}</td>
        <td>${d.toLocaleString()}</td>
      `;
      tbody.appendChild(tr);
    });
    
    if (data.length === 0) {
      tbody.innerHTML = "<tr><td colspan='6'><em>No rows.</em></td></tr>";
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan='6' style="color:#fca5a5">Error: ${err.message}</td></tr>`;
  }
}

// Load latest readings
async function loadLatest() {
  const grid = document.getElementById("latestGrid");
  if (!grid) return;
  
  grid.innerHTML = "Loading...";
  
  try {
    const data = await fetchJSON(`${API_BASE}/sensors/latest`);
    grid.innerHTML = "";
    
    if (!data || data.length === 0) {
      grid.innerHTML = "<em>No data yet. Start the sensors and Spark streaming.</em>";
      return;
    }
    
    // Display latest readings
    data.forEach((row) => {
      const el = document.createElement("div");
      el.className = "latest-sensor-card";
      
      el.innerHTML = `
        <div class="sensor-header">
          <span class="sensor-icon-large">📡</span>
          <h3>${row.sensor_id}</h3>
          <span class="sensor-type-badge">${row.area_type || "Unknown"}</span>
        </div>
        <div class="sensor-location">📍 ${row.location_name || "Unknown"}</div>
        <div class="aqi-display">
          <span class="aqi-value ${row.aqi ? getAQIClass(row.aqi) : ""}">
            AQI: ${row.aqi ?? "N/A"}
          </span>
          <span class="aqi-category">${getAQICategory(row.aqi) || ""}</span>
        </div>
        <div class="sensor-readings">
          <p><strong>PM2.5:</strong> ${row.pm2_5 ?? "-"}</p>
          <p><strong>PM10:</strong> ${row.pm10 ?? "-"}</p>
          <p><strong>Temp:</strong> ${row.temperature_celsius ?? "-"} °C</p>
          <p><strong>Humidity:</strong> ${row.humidity_percent ?? "-"} %</p>
        </div>
        <p class="health-message">${row.health_risk || ""}</p>
        <p class="timestamp"><small>${new Date(row.timestamp).toLocaleString()}</small></p>
      `;
      
      grid.appendChild(el);
    });
  } catch (err) {
    grid.innerHTML = `<span style="color:#fca5a5">Error: ${err.message}</span>`;
  }
}

// Utility functions
async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (err) {
    console.error("Fetch error:", err);
    throw new Error(`Connection failed: ${err.message}`);
  }
}

function getAQIClass(aqi) {
  if (aqi <= 50) return "aqi-good";
  if (aqi <= 100) return "aqi-moderate";
  if (aqi <= 150) return "aqi-unhealthy-sensitive";
  if (aqi <= 200) return "aqi-unhealthy";
  if (aqi <= 300) return "aqi-very-unhealthy";
  return "aqi-hazardous";
}

function getAQICategory(aqi) {
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy for Sensitive Groups";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very Unhealthy";
  return "Hazardous";
}

// Spark control functions
async function startSpark() {
  try {
    const response = await fetch(`${API_BASE}/spark/start`, { method: 'POST' });
    const data = await response.json();
    console.log('Spark start response:', data);
    
    if (data.running) {
      sparkRunning = true;
      updateSparkStatus("Running", "success");
    }
  } catch (error) {
    console.error('Error starting Spark:', error);
    updateSparkStatus("Error", "error");
  }
}

async function stopSpark() {
  try {
    const response = await fetch(`${API_BASE}/spark/stop`, { method: 'POST' });
    const data = await response.json();
    console.log('Spark stop response:', data);
    
    if (!data.running) {
      sparkRunning = false;
      updateSparkStatus("Stopped", "error");
    }
  } catch (error) {
    console.error('Error stopping Spark:', error);
    updateSparkStatus("Error", "error");
  }
}

function updateSparkStatus(status, type) {
  const sparkStatusElement = document.getElementById("sparkStatus");
  if (sparkStatusElement) {
    sparkStatusElement.textContent = status;
    sparkStatusElement.className = `status ${type}`;
  }
}

// Event listeners
document.addEventListener("DOMContentLoaded", function () {
  console.log("🚀 Initializing Spark-enabled Air Quality Tracker...");
  
  // Connect to WebSocket
  connectWebSocket();
  
  // Load initial data
  loadSensors();
  loadLatest();
  loadStats();
  
  // Set up periodic updates
  setInterval(loadLatest, 10000);
  setInterval(loadStats, 10000);
  
  // Set up Spark control buttons
  const startSparkBtn = document.getElementById("startSpark");
  const stopSparkBtn = document.getElementById("stopSpark");
  
  if (startSparkBtn) {
    startSparkBtn.addEventListener("click", startSpark);
  }
  
  if (stopSparkBtn) {
    stopSparkBtn.addEventListener("click", stopSpark);
  }
  
  // Set up form submissions
  const sensorForm = document.getElementById("sensor-form");
  if (sensorForm) {
    sensorForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const id = document.getElementById("sensor-id").value;
      const limit = parseInt(document.getElementById("limit").value || "20", 10);
      
      loadRecent(id, limit);
      loadAnalytics(id, 24);
    });
  }
  
  // Set up analytics controls
  const loadAnalyticsBtn = document.getElementById("load-analytics");
  if (loadAnalyticsBtn) {
    loadAnalyticsBtn.addEventListener("click", () => {
      const sensorId = document.getElementById("analytics-sensor").value || "sensor-urban-1";
      const hours = parseInt(document.getElementById("analytics-hours").value || "24", 10);
      loadAnalytics(sensorId, hours);
    });
  }
  
  console.log("✅ Spark-enabled Air Quality Tracker initialized");
});

