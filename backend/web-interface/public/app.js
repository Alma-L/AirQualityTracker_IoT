const API_BASE = "http://localhost:8000/api";  // Backend server URL

// WebSocket connection for real-time updates
let ws = null;
let isConnected = false;

// Connect to WebSocket
function connectWebSocket() {
    try {
        ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = function() {
            console.log('🔌 WebSocket connected');
            isConnected = true;
            updateConnectionStatus('Connected', 'success');
        };
        
        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data);
                
                if (data.type === 'realtime_update') {
                    updateRealTimeData(data.data);
                } else if (data.type === 'alerts_update') {
                    updateAlerts(data.alerts);
                }
                
                updateConnectionStatus('Connected', 'success');
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        ws.onclose = function() {
            console.log('🔌 WebSocket disconnected');
            isConnected = false;
            updateConnectionStatus('Disconnected', 'error');
            // Try to reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };
        
        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
            updateConnectionStatus('Error', 'error');
        };
    } catch (error) {
        console.error('WebSocket connection failed:', error);
        updateConnectionStatus('WebSocket Error', 'error');
    }
}

// Update connection status display
function updateConnectionStatus(status, type) {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        statusElement.textContent = status;
        statusElement.className = `status-${type}`;
    }
}

// Get AQI color class
function getAQIClass(aqi) {
    if (aqi <= 50) return 'aqi-good';
    if (aqi <= 100) return 'aqi-moderate';
    if (aqi <= 150) return 'aqi-unhealthy-sensitive';
    if (aqi <= 200) return 'aqi-unhealthy';
    if (aqi <= 300) return 'aqi-very-unhealthy';
    return 'aqi-hazardous';
}

// Get sensor icon based on type
function getSensorIcon(sensorType) {
    switch(sensorType) {
        case 'Urban': return '🏙️';
        case 'Industrial': return '🏭';
        case 'Residential': return '🏘️';
        default: return '📡';
    }
}

// Get sensor color based on type
function getSensorColor(sensorType) {
    switch(sensorType) {
        case 'Urban': return 'urban-sensor';
        case 'Industrial': return 'industrial-sensor';
        case 'Residential': return 'residential-sensor';
        default: return 'default-sensor';
    }
}

// Load main statistics
async function loadStats() {
    try {
        const data = await fetchJSON(`${API_BASE}/stats`);
        
        // Update basic stats
        document.getElementById("activeSensors").textContent = data.sensor_count || 0;
        document.getElementById("totalReadings").textContent = data.total_readings || 0;
        document.getElementById("activeAlerts").textContent = data.active_alerts || 0;
        
        // Update uptime
        const uptimeHours = Math.floor((data.uptime_seconds || 0) / 3600);
        const uptimeMinutes = Math.floor(((data.uptime_seconds || 0) % 3600) / 60);
        document.getElementById("uptime").textContent = `${uptimeHours}h ${uptimeMinutes}m`;
        
        // Update average AQI if available
        if (data.average_aqi) {
            const aqiElement = document.getElementById("averageAQI");
            if (aqiElement) {
                aqiElement.textContent = data.average_aqi;
                aqiElement.className = `aqi-value ${getAQIClass(data.average_aqi)}`;
            }
        }
        
        // Update sensor list if available
        if (data.sensors && data.sensors.length > 0) {
            updateSensorList(data.sensors);
        }
        
    } catch (err) {
        console.error('Error loading stats:', err);
        document.getElementById("activeSensors").textContent = "Error";
        document.getElementById("totalReadings").textContent = "Error";
        document.getElementById("activeAlerts").textContent = "Error";
        document.getElementById("uptime").textContent = "Error";
    }
}

// Update sensor list display
function updateSensorList(sensors) {
    const sensorListElement = document.getElementById('sensorList');
    if (!sensorListElement) return;
    
    sensorListElement.innerHTML = '';
    sensors.forEach(sensorId => {
        const sensorElement = document.createElement('div');
        sensorElement.className = 'sensor-item';
        
        // Determine sensor type from ID
        let sensorType = 'Unknown';
        let location = 'Unknown';
        if (sensorId.includes('urban')) {
            sensorType = 'Urban';
            location = 'City Center';
        } else if (sensorId.includes('industrial')) {
            sensorType = 'Industrial';
            location = 'Factory Zone';
        } else if (sensorId.includes('residential')) {
            sensorType = 'Residential';
            location = 'Suburban Area';
        }
        
        sensorElement.innerHTML = `
            <span class="sensor-icon">${getSensorIcon(sensorType)}</span>
            <div class="sensor-info">
                <span class="sensor-id">${sensorId}</span>
                <span class="sensor-type">${sensorType}</span>
                <span class="sensor-location">${location}</span>
            </div>
        `;
        sensorListElement.appendChild(sensorElement);
    });
}

// Load alerts
async function loadAlerts() {
    try {
        const alerts = await fetchJSON(`${API_BASE}/alerts?limit=10`);
        updateAlerts(alerts);
    } catch (err) {
        console.error('Error loading alerts:', err);
    }
}

// Update alerts display
function updateAlerts(alerts) {
    const alertsContainer = document.getElementById('alerts');
    if (!alertsContainer) return;
    
    if (alerts.length === 0) {
        alertsContainer.innerHTML = '<p class="no-alerts">No active alerts</p>';
        return;
    }
    
    alertsContainer.innerHTML = '';
    alerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${alert.severity}`;
        alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-type">${alert.type}</span>
                <span class="alert-severity ${alert.severity}">${alert.severity}</span>
            </div>
            <p class="alert-message">${alert.message}</p>
            <div class="alert-details">
                <small>Sensor: ${alert.sensor_id} | ${new Date(alert.timestamp).toLocaleString()}</small>
            </div>
        `;
        alertsContainer.appendChild(alertElement);
    });
}

// Load analytics for a sensor
async function loadAnalytics(sensorId, hours = 24) {
    try {
        const analytics = await fetchJSON(`${API_BASE}/analytics/${sensorId}?hours=${hours}`);
        updateAnalyticsDisplay(analytics);
    } catch (err) {
        console.error('Error loading analytics:', err);
        document.getElementById('analytics').innerHTML = '<p class="error">Error loading analytics</p>';
    }
}

// Update analytics display
function updateAnalyticsDisplay(analytics) {
    const analyticsContainer = document.getElementById('analytics');
    if (!analyticsContainer) return;
    
    if (analytics.error) {
        analyticsContainer.innerHTML = `<p class="error">${analytics.error}</p>`;
        return;
    }
    
    analyticsContainer.innerHTML = `
        <div class="analytics-grid">
            <div class="analytics-card">
                <h4>PM2.5 Statistics</h4>
                <div class="stat-row">
                    <span>Min:</span> <span class="value">${analytics.pm25.min}</span>
                </div>
                <div class="stat-row">
                    <span>Max:</span> <span class="value">${analytics.pm25.max}</span>
                </div>
                <div class="stat-row">
                    <span>Average:</span> <span class="value">${analytics.pm25.average}</span>
                </div>
            </div>
            <div class="analytics-card">
                <h4>PM10 Statistics</h4>
                <div class="stat-row">
                    <span>Min:</span> <span class="value">${analytics.pm10.min}</span>
                </div>
                <div class="stat-row">
                    <span>Max:</span> <span class="value">${analytics.pm10.max}</span>
                </div>
                <div class="stat-row">
                    <span>Average:</span> <span class="value">${analytics.pm10.average}</span>
                </div>
            </div>
            <div class="analytics-card">
                <h4>AQI Statistics</h4>
                <div class="stat-row">
                    <span>Min:</span> <span class="value">${analytics.aqi.min}</span>
                </div>
                <div class="stat-row">
                    <span>Max:</span> <span class="value">${analytics.aqi.max}</span>
                </div>
                <div class="stat-row">
                    <span>Average:</span> <span class="value">${analytics.aqi.average}</span>
                </div>
            </div>
        </div>
        <div class="analytics-summary">
            <p><strong>Period:</strong> Last ${analytics.time_period_hours} hours</p>
            <p><strong>Readings:</strong> ${analytics.readings_count} data points</p>
            <p><strong>Trend:</strong> ${analytics.trend}</p>
        </div>
    `;
}

async function fetchJSON(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  } catch (err) {
    console.error('Fetch error:', err);
    throw new Error(`Connection failed: ${err.message}`);
  }
}

async function loadLatest() {
  const container = document.getElementById("latest");
  container.innerHTML = "Loading...";
  try {
    const data = await fetchJSON(`${API_BASE}/sensors/latest`);
    container.innerHTML = "";
    data.forEach(row => {
      const d = new Date(row.timestamp);
      const el = document.createElement("div");
      el.className = `tile ${getSensorColor(row.sensor_type || 'Unknown')}`;
      el.setAttribute('data-sensor-id', row.sensor_id);
      
      // Enhanced display with AQI and sensor info
      const aqi = row.aqi || 'N/A';
      const aqiClass = row.aqi ? getAQIClass(row.aqi) : '';
      const aqiCategory = row.aqi_category || 'Unknown';
      const sensorType = row.sensor_type || 'Unknown';
      const location = row.location || 'Unknown';
      
      el.innerHTML = `
        <div class="sensor-header">
          <span class="sensor-icon-large">${getSensorIcon(sensorType)}</span>
          <h3>${row.sensor_id}</h3>
          <span class="sensor-type-badge">${sensorType}</span>
        </div>
        <div class="sensor-location">📍 ${location}</div>
        <div class="aqi-display">
          <span class="aqi-value ${aqiClass}">AQI: ${aqi}</span>
          <span class="aqi-category">${aqiCategory}</span>
        </div>
        <div class="sensor-readings">
          <p><strong>PM2.5:</strong> <span class="pm25-value">${row.pm2_5}</span></p>
          <p><strong>PM10:</strong> <span class="pm10-value">${row.pm10}</span></p>
          <p><strong>Temp:</strong> ${row.temperature} °C</p>
          <p><strong>Humidity:</strong> ${row.humidity} %</p>
        </div>
        <p class="health-message">${row.health_message || ''}</p>
        <p class="timestamp"><small>${d.toLocaleString()}</small></p>
      `;
      container.appendChild(el);
    });
    if (data.length === 0) container.innerHTML = "<em>No data yet. Start the sensors.</em>";
  } catch (err) {
    container.innerHTML = `<span style="color:#fca5a5">Error: ${err.message}</span>`;
  }
}

async function loadRecent(sensorId, limit) {
  const tbody = document.querySelector("#recent-table tbody");
  tbody.innerHTML = "<tr><td colspan='6'>Loading...</td></tr>";
  try {
    const data = await fetchJSON(`${API_BASE}/sensors/${encodeURIComponent(sensorId)}/recent?limit=${limit}`);
    tbody.innerHTML = "";
    data.forEach(row => {
      const d = new Date(row.timestamp);
      const tr = document.createElement("tr");
      const aqi = row.aqi || 'N/A';
      const aqiClass = row.aqi ? getAQIClass(row.aqi) : '';
      
      tr.innerHTML = `
        <td>${row.pm2_5}</td>
        <td>${row.pm10}</td>
        <td class="${aqiClass}">${aqi}</td>
        <td>${row.temperature}</td>
        <td>${row.humidity}</td>
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

// Event listeners
document.getElementById("refresh").addEventListener("click", loadLatest);
document.getElementById("sensor-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const id = document.getElementById("sensor-id").value || "sensor-urban-1";
  const limit = parseInt(document.getElementById("limit").value || "20", 10);
  loadRecent(id, limit);
  
  // Also load analytics for this sensor
  loadAnalytics(id, 24);
});

// Analytics controls
document.getElementById("load-analytics").addEventListener("click", () => {
  const sensorId = document.getElementById("analytics-sensor").value || "sensor-urban-1";
  const hours = parseInt(document.getElementById("analytics-hours").value || "24", 10);
  loadAnalytics(sensorId, hours);
});

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Connect to WebSocket
    connectWebSocket();
    
    // Load initial data
    loadLatest();
    loadRecent("sensor-urban-1", 20);
    loadStats();
    loadAlerts();
    loadAnalytics("sensor-urban-1", 24);
    
    // Auto-refresh data every 10 seconds
    setInterval(loadLatest, 10000);
    setInterval(loadStats, 10000);
    setInterval(loadAlerts, 15000);
    
    // Update uptime every minute
    setInterval(() => {
        const uptimeElement = document.getElementById("uptime");
        if (uptimeElement && uptimeElement.textContent !== "Error") {
            const currentText = uptimeElement.textContent;
            const [hours, minutes] = currentText.split('h ');
            const newMinutes = parseInt(minutes) + 1;
            if (newMinutes >= 60) {
                const newHours = parseInt(hours) + 1;
                uptimeElement.textContent = `${newHours}h 0m`;
            } else {
                uptimeElement.textContent = `${hours}h ${newMinutes}m`;
            }
        }
    }, 60000);
});
