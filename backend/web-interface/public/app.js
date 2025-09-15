const API_BASE = "http://localhost:8000/api";

let ws = null;
let isConnected = false;

// Missing functions that are called by WebSocket
function updateConnectionStatus(status, type) {
  const wsStatusElement = document.getElementById("wsStatus");
  if (wsStatusElement) {
    wsStatusElement.textContent = status;
    wsStatusElement.className = `health-value ${type === 'success' ? 'success' : 'error'}`;
  }
}

function updateRealTimeData(data) {
  console.log("Updating real-time data:", data);
  // This function would update the real-time data display
  // For now, just log the data
}

function updateAlerts(alerts) {
  console.log("Updating alerts:", alerts);
  // This function would update the alerts display
  // For now, just log the alerts
}

function connectWebSocket() {
  try {
    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = function () {
      console.log("🔌 WebSocket connected");
      isConnected = true;
      updateConnectionStatus("Connected", "success");
    };

    ws.onmessage = function (event) {
      try {
        // Check if the message is valid JSON
        let data;
        try {
          data = JSON.parse(event.data);
        } catch (jsonError) {
          console.log("Non-JSON WebSocket message:", event.data);
          return; // Skip non-JSON messages
        }
        
        console.log("WebSocket message received:", data);

        if (data.type === "realtime_update") {
          updateRealTimeData(data.data);
        } else if (data.type === "alerts_update") {
          updateAlerts(data.alerts);
        }

        updateConnectionStatus("Connected", "success");
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
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

// Get AQI color class
function getAQIClass(aqi) {
  if (aqi <= 50) return "aqi-good";
  if (aqi <= 100) return "aqi-moderate";
  if (aqi <= 150) return "aqi-unhealthy-sensitive";
  if (aqi <= 200) return "aqi-unhealthy";
  if (aqi <= 300) return "aqi-very-unhealthy";
  return "aqi-hazardous";
}

function getSensorIcon(sensorType) {
  const type = sensorType.toLowerCase();
  if (type.includes("urban")) return "🏙️";
  if (type.includes("industrial")) return "🏭";
  if (type.includes("residential")) return "🏘️";
  if (type.includes("mobile")) return "🚌";
  if (type.includes("wearable")) return "🚶‍♂️";
  if (type.includes("drone")) return "🚁";
  return "📡";
}

function getSensorColor(sensorType) {
  switch (sensorType.toLowerCase()) {
    case "urban":
      return "urban-sensor";
    case "industrial":
      return "industrial-sensor";
    case "residential":
      return "residential-sensor";
    case "mobile":
      return "mobile-sensor";
    case "wearable":
      return "wearable-sensor";
    case "drone":
      return "drone-sensor";
    default:
      return "default-sensor";
  }
}

// Load main statistics
async function loadStats() {
  try {
    const data = await fetchJSON(`${API_BASE}/stats`);

    // Update basic stats
    document.getElementById("activeSensors").textContent =
      data.sensor_count || 0;
    document.getElementById("totalReadings").textContent =
      data.total_readings || 0;
    document.getElementById("activeAlerts").textContent =
      data.active_alerts || 0;

    // Update uptime
    const uptimeHours = Math.floor((data.uptime_seconds || 0) / 3600);
    const uptimeMinutes = Math.floor(((data.uptime_seconds || 0) % 3600) / 60);
    document.getElementById(
      "uptime"
    ).textContent = `${uptimeHours}h ${uptimeMinutes}m`;

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
    console.error("Error loading stats:", err);
    document.getElementById("activeSensors").textContent = "Error";
    document.getElementById("totalReadings").textContent = "Error";
    document.getElementById("activeAlerts").textContent = "Error";
    document.getElementById("uptime").textContent = "Error";
  }
}

// Update sensor list display
function updateSensorList(sensors) {
  const sensorListElement = document.getElementById("sensorList");
  if (!sensorListElement) return;

  sensorListElement.innerHTML = "";
  sensors.forEach((sensorId) => {
    const sensorElement = document.createElement("div");
    sensorElement.className = "sensor-item";

    // Determine sensor type from ID
    let sensorType = "Unknown";
    let location = "Unknown";
    if (sensorId.includes("urban")) {
      sensorType = "Urban";
      location = "City Center";
    } else if (sensorId.includes("industrial")) {
      sensorType = "Industrial";
      location = "Factory Zone";
    } else if (sensorId.includes("residential")) {
      sensorType = "Residential";
      location = "Suburban Area";
    } else if (sensorId.includes("bus")) {
      sensorType = "Mobile";
      location = "City Bus Route";
    } else if (sensorId.includes("wearable")) {
      sensorType = "Wearable";
      location = "Cyclist / Pedestrian";
    } else if (sensorId.includes("drone")) {
      sensorType = "Drone";
      location = "Aerial / City Monitoring";
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

async function loadSensors() {
  try {
    const res = await fetch(`${API_BASE}/sensors`);
    if (!res.ok) throw new Error("Failed to load sensors");

    let sensors = await res.json();

    if (sensors.sensors) {
      sensors = sensors.sensors;
    }

    const sensorSelect = document.getElementById("sensor-id");
    sensorSelect.innerHTML = "";

    sensors.forEach((sensor) => {
      const sensorId = typeof sensor === "string" ? sensor : sensor.id;
      const option = document.createElement("option");
      option.value = sensorId;
      option.textContent = sensorId;
      sensorSelect.appendChild(option);
    });

    if (sensors.length > 0) {
      const firstSensorId =
        typeof sensors[0] === "string" ? sensors[0] : sensors[0].id;
      loadRecent(firstSensorId, 20);
      loadAnalytics(firstSensorId, 24);
    }
  } catch (err) {
    console.error("Error loading sensors:", err);
  }
}

// Load alerts
async function loadAlerts() {
  try {
    const alerts = await fetchJSON(`${API_BASE}/alerts?limit=10`);
    updateAlerts(alerts);
  } catch (err) {
    console.error("Error loading alerts:", err);
  }
}

function updateAlerts(alerts) {
  const alertsContainer = document.getElementById("alertsContainer");
  if (!alertsContainer) return;

  // Update Active Alerts count
  const activeAlertsElement = document.getElementById("activeAlerts");
  if (activeAlertsElement) {
    activeAlertsElement.textContent = alerts.length; // ✅ now only active alerts
  }

  if (alerts.length === 0) {
    alertsContainer.innerHTML = '<p class="no-alerts">No active alerts</p>';
    return;
  }

  alertsContainer.innerHTML = "";
  alerts.forEach((alert) => {
    const alertElement = document.createElement("div");
    alertElement.className = `alert alert-${alert.severity}`;
    alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-type">${alert.type}</span>
                <span class="alert-severity ${alert.severity}">${
      alert.severity
    }</span>
            </div>
            <p class="alert-message">${alert.message}</p>
            <div class="alert-details">
                <small>Sensor: ${alert.sensor_id} | ${new Date(
      alert.timestamp
    ).toLocaleString()}</small>
            </div>
        `;
    alertsContainer.appendChild(alertElement);
  });
}

// Load analytics for a sensor
async function loadAnalytics(sensorId, hours = 24) {
  try {
    const analytics = await fetchJSON(
      `${API_BASE}/analytics/${sensorId}?hours=${hours}`
    );
    updateAnalyticsDisplay(analytics);
  } catch (err) {
    console.error("Error loading analytics:", err);
    document.getElementById("analytics").innerHTML =
      '<p class="error">Error loading analytics</p>';
  }
}

//update analytics display
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

async function loadLatest() {
  const grid = document.getElementById("latestGrid");
  grid.innerHTML = "Loading...";
  try {
    const data = await fetchJSON(`${API_BASE}/sensors/latest`);
    grid.innerHTML = "";
    data.forEach((row) => {
      const el = document.createElement("div"); // <-- define el
      el.className = "latest-sensor-card"; // optional: for styling
      el.innerHTML = `
    <div class="sensor-header">
      <span class="sensor-icon-large">${getSensorIcon(
        row.sensor_type || "Unknown"
      )}</span>
      <h3>${row.sensor_id}</h3>
      <span class="sensor-type-badge">${row.sensor_type || "Unknown"}</span>
    </div>
    <div class="sensor-location">📍 ${row.location || "Unknown"}</div>
    <div class="aqi-display">
      <span class="aqi-value ${row.aqi ? getAQIClass(row.aqi) : ""}">AQI: ${
        row.aqi || "N/A"
      }</span>
      <span class="aqi-category">${row.aqi_category || "Unknown"}</span>
    </div>
    <div class="sensor-readings">
      <p style="color:white"><strong>PM2.5:</strong> ${row.pm2_5}</p>
       <p style="color:white"><strong>PM10:</strong> ${row.pm10}</p>
      <p style="color:white"><strong>Temp:</strong> ${row.temperature} °C</p>
      <p style="color:white"><strong>Humidity:</strong> ${row.humidity} %</p>
    </div>
    <p class="health-message">${row.health_message || ""}</p>
    <p class="timestamp"><small>${new Date(
      row.timestamp
    ).toLocaleString()}</small></p>
  `;
      grid.appendChild(el);
    });

    if (data.length === 0) {
      grid.innerHTML = "<em>No data yet. Start the sensors.</em>";
    }
  } catch (err) {
    grid.innerHTML = `<span style="color:#fca5a5">Error: ${err.message}</span>`;
  }
}

async function loadRecent(sensorId, limit) {
  const tbody = document.querySelector("#recent-table tbody");
  tbody.innerHTML = "<tr><td colspan='6'>Loading...</td></tr>";
  try {
    const data = await fetchJSON(
      `${API_BASE}/sensors/${encodeURIComponent(
        sensorId
      )}/recent?limit=${limit}`
    );
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

async function loadAllSensors() {
  try {
    const res = await fetch(`${API_BASE}/sensors`);
    if (!res.ok) throw new Error("Failed to load sensors");

    const data = await res.json();
    const sensors = data.sensors || [];

    const sensorsGrid = document.getElementById("sensorsGrid");
    sensorsGrid.innerHTML = "";

    sensors.forEach((sensor) => {
      const card = document.createElement("div");
      card.className = "sensor-card";
      card.innerHTML = `
        <img src="${sensor.img}" alt="${sensor.type} Sensor">
        <h3>${sensor.id}</h3>
        <p class="sensor-type">Type: ${sensor.type}</p>
        <p class="sensor-location">Location: ${sensor.location}</p>
      `;
      sensorsGrid.appendChild(card);
    });

    if (sensors.length === 0) {
      sensorsGrid.innerHTML = "<p>No sensors found.</p>";
    }
  } catch (err) {
    console.error("Error loading sensors:", err);
    document.getElementById(
      "sensorsGrid"
    ).innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
  }
}

const mlButton = document.getElementById("run-ml");
const mlResults = document.getElementById("mlResults");
let mlChart = null;

mlButton.addEventListener("click", async () => {
  const sensorId = document.getElementById("ml-sensor").value;
  const algorithm = document.getElementById("ml-algorithm").value;
  const hours = document.getElementById("ml-hours").value;

  mlResults.innerHTML = "<p>Running analysis...</p>";

  try {
    const res = await fetch(
      `${API_BASE}/ml-analysis?sensor=${sensorId}&algorithm=${algorithm}&hours=${hours}`
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.error) {
      mlResults.innerHTML = `<p style="color:red;">${data.error}</p>`;
      return;
    }

    // Display anomalies if available
    if (data.anomalies && data.anomalies.length > 0) {
      mlResults.innerHTML = `<h3>Detected Anomalies (${data.anomalies.length})</h3>`;
      const list = document.createElement("ul");
      data.anomalies.forEach((a) => {
        const item = document.createElement("li");
        item.textContent = `Timestamp: ${a.timestamp}, PM2.5: ${
          a.pm2_5
        }, PM10: ${a.pm10}, Score: ${a.score || "N/A"}`;
        list.appendChild(item);
      });
      mlResults.appendChild(list);
    } else {
      mlResults.innerHTML =
        "<p>No anomalies detected in the selected time period.</p>";
    }

    // Setup Chart.js data
    const ctx = document.getElementById("mlChart").getContext("2d");
    if (mlChart) mlChart.destroy();

    const datasets = [
      { label: "PM2.5", data: data.pm25, borderColor: "red", fill: false },
      { label: "PM10", data: data.pm10, borderColor: "blue", fill: false },
    ];

    console.log("ML Data:", data);

    // Only add anomaly score if it exists
    if (data.scores) {
      datasets.push({
        label: "Anomaly Score",
        data: data.scores,
        borderColor: "orange",
        fill: false,
        yAxisID: "y1",
      });
    }

    mlChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.timestamps,
        datasets: datasets,
      },
      options: {
        scales: {
          y: {
            type: "linear",
            position: "left",
            title: { display: true, text: "PM (µg/m³)" },
          },
          y1: {
            type: "linear",
            position: "right",
            title: { display: true, text: "Anomaly Score" },
            min: 0,
            max: 1,
            display: data.scores ? true : false,
          },
          x: { title: { display: true, text: "Time" } },
        },
      },
    });
  } catch (err) {
    mlResults.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
  }
});

document.getElementById("sensor-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const id = document.getElementById("sensor-id").value;
  const limit = parseInt(document.getElementById("limit").value || "20", 10);

  loadRecent(id, limit);
  loadAnalytics(id, 24);
});

document.getElementById("analyticsContent").innerHTML =
  '<p class="error">Error loading analytics</p>';

  document.getElementById("exportCSV").addEventListener("click", () => {
  const grid = document.getElementById("latestGrid");
  const cards = grid.querySelectorAll(".latest-sensor-card");

  if (cards.length === 0) {
    alert("No data to export.");
    return;
  }

  // Prepare CSV headers
  const headers = [
    "Sensor ID",
    "Type",
    "Location",
    "AQI",
    "AQI Category",
    "PM2.5",
    "PM10",
    "Temperature",
    "Humidity",
    "Health Message",
    "Timestamp",
  ];

  const rows = [headers.join(",")];

  cards.forEach((card) => {
    const sensorId = card.querySelector("h3")?.textContent || "";
    const type = card.querySelector(".sensor-type-badge")?.textContent || "";
    const location = card.querySelector(".sensor-location")?.textContent.replace("📍 ", "") || "";
    const aqi = card.querySelector(".aqi-value")?.textContent.replace("AQI: ", "") || "";
    const aqiCategory = card.querySelector(".aqi-category")?.textContent || "";
    const pm25 = card.querySelector(".sensor-readings p:nth-child(1)")?.textContent.replace("PM2.5: ", "") || "";
    const pm10 = card.querySelector(".sensor-readings p:nth-child(2)")?.textContent.replace("PM10: ", "") || "";
    const temp = card.querySelector(".sensor-readings p:nth-child(3)")?.textContent.replace("Temp: ", "") || "";
    const humidity = card.querySelector(".sensor-readings p:nth-child(4)")?.textContent.replace("Humidity: ", "") || "";
    const health = card.querySelector(".health-message")?.textContent || "";
    const timestamp = card.querySelector(".timestamp")?.textContent || "";

    const row = [
      sensorId, type, location, aqi, aqiCategory, pm25, pm10, temp, humidity, health, timestamp
    ];

    rows.push(row.join(","));
  });

  // Create CSV blob and download
  const csvContent = rows.join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `latest_readings_${new Date().toISOString().slice(0,19).replace(/:/g,"-")}.csv`;
  link.click();
});


document.getElementById("refresh").addEventListener("click", () => {
  const refreshBtn = document.getElementById("refresh");
  refreshBtn.disabled = true; // optional: prevent multiple clicks
  refreshBtn.textContent = "⏳ Refreshing...";

  loadLatest()
    .then(() => {
      refreshBtn.textContent = "🔄 Refresh";
      refreshBtn.disabled = false;
    })
    .catch((err) => {
      console.error("Error refreshing latest readings:", err);
      refreshBtn.textContent = "🔄 Refresh";
      refreshBtn.disabled = false;
    });
});


// Analytics controls
document.getElementById("load-analytics").addEventListener("click", () => {
  const sensorId =
    document.getElementById("analytics-sensor").value || "sensor-urban-1";
  const hours = parseInt(
    document.getElementById("analytics-hours").value || "24",
    10
  );
  loadAnalytics(sensorId, hours);
});
document.getElementById("analytics-sensor").addEventListener("change", () => {
  const sensorId = document.getElementById("analytics-sensor").value;
  const hours = parseInt(
    document.getElementById("analytics-hours").value || "24",
    10
  );
  loadAnalytics(sensorId, hours);
});

document.getElementById("analytics-hours").addEventListener("change", () => {
  const sensorId = document.getElementById("analytics-sensor").value;
  const hours = parseInt(
    document.getElementById("analytics-hours").value || "24",
    10
  );
  loadAnalytics(sensorId, hours);
});

const sensorsGrid = document.getElementById("sensorsGrid");

// Initialize the application
document.addEventListener("DOMContentLoaded", function () {
  // Connect to WebSocket
  connectWebSocket();

  // Load initial data
  loadAllSensors();
  loadLatest();
  loadSensors();
  loadStats();
  loadAlerts();

  // Initialize smart sensors
  initializeSmartSensors();

  setInterval(loadLatest, 10000);
  setInterval(loadStats, 10000);
  setInterval(loadAlerts, 15000);

  setInterval(() => {
    const uptimeElement = document.getElementById("uptime");
    if (uptimeElement && uptimeElement.textContent !== "Error") {
      const currentText = uptimeElement.textContent;
      const [hours, minutes] = currentText.split("h ");
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

// Smart Virtual Sensors functionality
let smartSensorsData = {};
let smartAutoRefreshInterval = null;
let isSmartAutoRefresh = false;

// Kosovo Smart Virtual Sensors Data - Based on Real Kosovo Map
const sampleSmartData = {
  "smart-prishtina-001": {
    sensor_id: "smart-prishtina-001",
    sensor_type: "Capital City Monitor",
    location: "Prishtina City Center",
    category: "urban",
    city: "Prishtina",
    coordinates: { x: 50, y: 40 },
    air_quality_index: 45,
    pm2_5: 18.5,
    pm10: 28.2,
    temperature: 22.3,
    humidity: 65.1,
    pressure: 1013.2,
    wind_speed: 3.2,
    wind_direction: 180,
    battery_level: 87.5,
    signal_strength: 85.2,
    timestamp: new Date().toISOString()
  },
  "smart-peja-002": {
    sensor_id: "smart-peja-002",
    sensor_type: "Industrial Monitor",
    location: "Peja Industrial Zone",
    category: "industrial",
    city: "Peja",
    coordinates: { x: 20, y: 25 },
    air_quality_index: 65,
    pm2_5: 28.7,
    pm10: 45.1,
    temperature: 25.1,
    humidity: 55.3,
    pressure: 1012.8,
    wind_speed: 5.1,
    wind_direction: 225,
    battery_level: 92.1,
    signal_strength: 90.5,
    timestamp: new Date().toISOString()
  },
  "smart-prizren-003": {
    sensor_id: "smart-prizren-003",
    sensor_type: "Historic City Monitor",
    location: "Prizren Historic District",
    category: "residential",
    city: "Prizren",
    coordinates: { x: 30, y: 80 },
    air_quality_index: 35,
    pm2_5: 15.2,
    pm10: 25.6,
    temperature: 20.1,
    humidity: 70.4,
    pressure: 1000.3,
    wind_speed: 2.5,
    wind_direction: 315,
    battery_level: 95.3,
    signal_strength: 88.7,
    timestamp: new Date().toISOString()
  },
  "smart-gjakova-004": {
    sensor_id: "smart-gjakova-004",
    sensor_type: "Mobile Monitor",
    location: "Gjakova Bus Route",
    category: "mobile",
    city: "Gjakova",
    coordinates: { x: 15, y: 60 },
    air_quality_index: 55,
    pm2_5: 22.3,
    pm10: 35.8,
    temperature: 24.7,
    humidity: 60.2,
    pressure: 1013.5,
    wind_speed: 8.3,
    wind_direction: 270,
    battery_level: 78.9,
    signal_strength: 75.8,
    timestamp: new Date().toISOString()
  },
  "smart-mitrovica-005": {
    sensor_id: "smart-mitrovica-005",
    sensor_type: "Aerial Survey",
    location: "Mitrovica Airspace",
    category: "aerial",
    city: "Mitrovica",
    coordinates: { x: 40, y: 15 },
    air_quality_index: 40,
    pm2_5: 15.2,
    pm10: 25.6,
    temperature: 20.1,
    humidity: 70.4,
    pressure: 1000.3,
    wind_speed: 12.5,
    wind_direction: 315,
    battery_level: 65.3,
    signal_strength: 95.7,
    timestamp: new Date().toISOString()
  },
  "smart-ferizaj-006": {
    sensor_id: "smart-ferizaj-006",
    sensor_type: "Underground Monitor",
    location: "Ferizaj Underground Street",
    category: "underground",
    city: "Ferizaj",
    coordinates: { x: 60, y: 50 },
    air_quality_index: 75,
    pm2_5: 35.8,
    pm10: 55.2,
    temperature: 28.5,
    humidity: 80.1,
    pressure: 1020.7,
    wind_speed: 0,
    wind_direction: 0,
    battery_level: 95.2,
    signal_strength: 60.3,
    timestamp: new Date().toISOString()
  },
  "smart-gjilan-007": {
    sensor_id: "smart-gjilan-007",
    sensor_type: "Urban Monitor",
    location: "Gjilan City Center",
    category: "urban",
    city: "Gjilan",
    coordinates: { x: 70, y: 30 },
    air_quality_index: 50,
    pm2_5: 20.1,
    pm10: 32.4,
    temperature: 23.8,
    humidity: 65.7,
    pressure: 1014.1,
    wind_speed: 4.2,
    wind_direction: 200,
    battery_level: 82.6,
    signal_strength: 70.9,
    timestamp: new Date().toISOString()
  },
  "smart-vushtrri-008": {
    sensor_id: "smart-vushtrri-008",
    sensor_type: "Residential Monitor",
    location: "Vushtrri Residential Area",
    category: "residential",
    city: "Vushtrri",
    coordinates: { x: 35, y: 25 },
    air_quality_index: 42,
    pm2_5: 17.8,
    pm10: 29.1,
    temperature: 21.5,
    humidity: 68.2,
    pressure: 1012.5,
    wind_speed: 3.8,
    wind_direction: 190,
    battery_level: 89.3,
    signal_strength: 78.4,
    timestamp: new Date().toISOString()
  }
};

function getSmartAQIClass(aqi) {
  if (aqi <= 50) return 'aqi-good';
  if (aqi <= 100) return 'aqi-moderate';
  if (aqi <= 150) return 'aqi-unhealthy';
  return 'aqi-hazardous';
}

function getSmartBatteryClass(battery) {
  if (battery >= 70) return 'battery-high';
  if (battery >= 30) return 'battery-medium';
  return 'battery-low';
}

function updateSmartStats(data) {
  const stats = Object.values(data);
  const totalSensors = stats.length;
  const avgAQI = Math.round(stats.reduce((sum, s) => sum + s.air_quality_index, 0) / totalSensors);
  const totalReadings = stats.length; // This would be actual reading count in real implementation
  const onlineSensors = stats.filter(s => s.battery_level > 0).length;
  const avgBattery = Math.round(stats.reduce((sum, s) => sum + s.battery_level, 0) / totalSensors);
  
  const statsGrid = document.getElementById('smartStatsGrid');
  if (!statsGrid) return;
  
  statsGrid.innerHTML = `
    <div class="smart-stat-card">
      <div class="smart-stat-value">${totalSensors}</div>
      <div class="smart-stat-label">Total Sensors</div>
    </div>
    <div class="smart-stat-card">
      <div class="smart-stat-value">${avgAQI}</div>
      <div class="smart-stat-label">Average AQI</div>
    </div>
    <div class="smart-stat-card">
      <div class="smart-stat-value">${onlineSensors}</div>
      <div class="smart-stat-label">Online Sensors</div>
    </div>
    <div class="smart-stat-card">
      <div class="smart-stat-value">${avgBattery}%</div>
      <div class="smart-stat-label">Avg Battery</div>
    </div>
  `;
}


function updateSmartSensors(data) {
  const sensorsGrid = document.getElementById('smartSensorsGrid');
  if (!sensorsGrid) return;
  
  sensorsGrid.innerHTML = '';
  
  // Handle both array and object data formats
  const sensors = Array.isArray(data) ? data : Object.values(data);
  
  sensors.forEach(sensor => {
    const sensorCard = document.createElement('div');
    sensorCard.className = 'smart-sensor-card';
    
    // Extract city name from location or sensor_id
    const city = sensor.city || sensor.sensor_id?.split('-')[1] || 'Unknown';
    const location = sensor.location || 'Unknown Location';
    
    sensorCard.innerHTML = `
      <div class="smart-sensor-header">
        <div class="smart-sensor-type">${sensor.sensor_type || 'Smart Sensor'}</div>
        <div class="smart-sensor-category">${sensor.category || 'unknown'}</div>
      </div>
      <div class="smart-sensor-location">📍 ${city} - ${location}</div>
      <div class="smart-sensor-data">
        <div class="smart-data-item">
          <div class="smart-data-value">
            ${Math.round(sensor.air_quality_index || 0)}
            <span class="aqi-indicator ${getSmartAQIClass(sensor.air_quality_index || 0)}">AQI</span>
          </div>
          <div class="smart-data-label">Air Quality Index</div>
        </div>
        <div class="smart-data-item">
          <div class="smart-data-value">${(sensor.pm2_5 || 0).toFixed(1)} μg/m³</div>
          <div class="smart-data-label">PM2.5</div>
        </div>
        <div class="smart-data-item">
          <div class="smart-data-value">${(sensor.pm10 || 0).toFixed(1)} μg/m³</div>
          <div class="smart-data-label">PM10</div>
        </div>
        <div class="smart-data-item">
          <div class="smart-data-value">${(sensor.temperature || 0).toFixed(1)}°C</div>
          <div class="smart-data-label">Temperature</div>
        </div>
        <div class="smart-data-item">
          <div class="smart-data-value">${(sensor.humidity || 0).toFixed(1)}%</div>
          <div class="smart-data-label">Humidity</div>
        </div>
        <div class="smart-data-item">
          <div class="smart-data-value">
            ${(sensor.battery_level || 0).toFixed(1)}%
            <span class="battery-indicator ${getSmartBatteryClass(sensor.battery_level || 0)}">Battery</span>
          </div>
          <div class="smart-data-label">Battery Level</div>
        </div>
        <div class="smart-data-item">
          <div class="smart-data-value">${(sensor.pressure || 0).toFixed(1)} hPa</div>
          <div class="smart-data-label">Pressure</div>
        </div>
        <div class="smart-data-item">
          <div class="smart-data-value">${(sensor.wind_speed || 0).toFixed(1)} m/s</div>
          <div class="smart-data-label">Wind Speed</div>
        </div>
      </div>
      <div class="smart-sensor-timestamp">
        <small>Last updated: ${new Date(sensor.timestamp || Date.now()).toLocaleString()}</small>
      </div>
    `;
    sensorsGrid.appendChild(sensorCard);
  });
}

function refreshSmartData() {
  console.log('Refreshing smart sensor data...');
  
  // Simulate data refresh with random variations
  Object.keys(sampleSmartData).forEach(sensorId => {
    const sensor = sampleSmartData[sensorId];
    sensor.air_quality_index = Math.max(0, sensor.air_quality_index + (Math.random() - 0.5) * 10);
    sensor.pm2_5 = Math.max(0, sensor.pm2_5 + (Math.random() - 0.5) * 5);
    sensor.pm10 = Math.max(0, sensor.pm10 + (Math.random() - 0.5) * 8);
    sensor.temperature = sensor.temperature + (Math.random() - 0.5) * 2;
    sensor.humidity = Math.max(0, Math.min(100, sensor.humidity + (Math.random() - 0.5) * 5));
    sensor.battery_level = Math.max(0, sensor.battery_level - Math.random() * 0.5);
    sensor.signal_strength = Math.max(0, Math.min(100, sensor.signal_strength + (Math.random() - 0.5) * 5));
    sensor.timestamp = new Date().toISOString();
  });
  
  // Update UI elements
  const statsGrid = document.getElementById('smartStatsGrid');
  const sensorsGrid = document.getElementById('smartSensorsGrid');
  const lastUpdate = document.getElementById('smartLastUpdate');
  const statusIndicator = document.getElementById('smartStatusIndicator');
  
  if (statsGrid) {
    updateSmartStats(sampleSmartData);
  }
  
  if (sensorsGrid) {
    updateSmartSensors(sampleSmartData);
  }
  
  if (lastUpdate) {
    lastUpdate.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
  }
  
  if (statusIndicator) {
    statusIndicator.className = 'status-indicator status-online';
  }
  
  console.log('Smart sensor data refreshed successfully');
}

function exportSmartData() {
  const csvContent = "data:text/csv;charset=utf-8," + 
    "sensor_id,sensor_type,location,category,air_quality_index,pm2_5,pm10,temperature,humidity,pressure,wind_speed,wind_direction,battery_level,signal_strength,timestamp\n" +
    Object.values(sampleSmartData).map(sensor => 
      `${sensor.sensor_id},${sensor.sensor_type},${sensor.location},${sensor.category},${sensor.air_quality_index},${sensor.pm2_5},${sensor.pm10},${sensor.temperature},${sensor.humidity},${sensor.pressure},${sensor.wind_speed},${sensor.wind_direction},${sensor.battery_level},${sensor.signal_strength},${sensor.timestamp}`
    ).join("\n");
  
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", "smart_sensor_data.csv");
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function toggleSmartAutoRefresh() {
  isSmartAutoRefresh = !isSmartAutoRefresh;
  const status = document.getElementById('smartAutoRefreshStatus');
  
  if (isSmartAutoRefresh) {
    smartAutoRefreshInterval = setInterval(refreshSmartData, 5000); // Refresh every 5 seconds
    status.textContent = 'Auto refresh: ON (5s)';
  } else {
    clearInterval(smartAutoRefreshInterval);
    status.textContent = 'Auto refresh: OFF';
  }
}

// Simple sensor data with Kosovo city positions (all sensors positioned inside map borders)
const sensors = [
  { id: "smart-prishtina-001", city: "Prishtina", type: "urban", aqi: 45, x: 70, y: 35, pm2_5: 18.5, pm10: 28.2, temperature: 22.3, humidity: 65.1, battery: 87.5 },
  { id: "smart-peja-002", city: "Peja", type: "industrial", aqi: 65, x: 25, y: 40, pm2_5: 28.7, pm10: 45.1, temperature: 25.1, humidity: 55.3, battery: 92.1 },
  { id: "smart-prizren-003", city: "Prizren", type: "residential", aqi: 35, x: 45, y: 70, pm2_5: 15.2, pm10: 25.6, temperature: 20.1, humidity: 70.4, battery: 95.3 },
  { id: "smart-gjakova-004", city: "Gjakova", type: "mobile", aqi: 55, x: 30, y: 60, pm2_5: 22.3, pm10: 35.8, temperature: 24.7, humidity: 60.2, battery: 78.9 },
  { id: "smart-mitrovica-005", city: "Mitrovica", type: "aerial", aqi: 40, x: 60, y: 25, pm2_5: 15.2, pm10: 25.6, temperature: 20.1, humidity: 70.4, battery: 65.3 },
  { id: "smart-ferizaj-006", city: "Ferizaj", type: "underground", aqi: 75, x: 65, y: 55, pm2_5: 35.8, pm10: 55.2, temperature: 28.5, humidity: 80.1, battery: 95.2 },
  { id: "smart-gjilan-007", city: "Gjilan", type: "urban", aqi: 50, x: 80, y: 45, pm2_5: 20.1, pm10: 32.4, temperature: 23.8, humidity: 65.7, battery: 82.6 },
  { id: "smart-vushtrri-008", city: "Vushtrri", type: "residential", aqi: 42, x: 60, y: 35, pm2_5: 17.8, pm10: 29.1, temperature: 21.5, humidity: 68.2, battery: 89.3 }
];

function renderKosovoMap() {
  // The map image is already in the HTML, just render the markers
  renderMarkers();
  updateMapStatistics();
}

function renderMarkers() {
  const mapMarkers = document.getElementById("mapMarkers");
  if (!mapMarkers) return;
  
  mapMarkers.innerHTML = "";

  sensors.forEach(sensor => {
    const marker = document.createElement("div");
    marker.className = `marker ${sensor.type}`;
    marker.style.left = `${sensor.x}%`;
    marker.style.top = `${sensor.y}%`;
    marker.title = `${sensor.city} - AQI: ${sensor.aqi}`;
    
    // Add click event to show sensor details
    marker.addEventListener('click', () => {
      showSensorDetails(sensor);
    });
    
    mapMarkers.appendChild(marker);
  });
}


function showSensorDetails(sensor) {
  // Create a more detailed modal instead of alert
  const modal = document.createElement('div');
  modal.className = 'sensor-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <div class="modal-header">
        <h3>${sensor.id}</h3>
        <span class="close-modal">&times;</span>
      </div>
      <div class="modal-body">
        <div class="sensor-detail-section">
          <h4>📍 Location</h4>
          <p><strong>City:</strong> ${sensor.city}</p>
          <p><strong>Type:</strong> ${sensor.type}</p>
        </div>
        <div class="sensor-detail-section">
          <h4>🌡️ Air Quality</h4>
          <p><strong>AQI:</strong> <span class="aqi-value ${getSmartAQIClass(sensor.aqi)}">${sensor.aqi}</span></p>
          <p><strong>PM2.5:</strong> ${sensor.pm2_5} μg/m³</p>
          <p><strong>PM10:</strong> ${sensor.pm10} μg/m³</p>
        </div>
        <div class="sensor-detail-section">
          <h4>🌤️ Weather</h4>
          <p><strong>Temperature:</strong> ${sensor.temperature}°C</p>
          <p><strong>Humidity:</strong> ${sensor.humidity}%</p>
        </div>
        <div class="sensor-detail-section">
          <h4>🔧 Status</h4>
          <p><strong>Battery:</strong> <span class="battery-indicator ${getSmartBatteryClass(sensor.battery)}">${sensor.battery}%</span></p>
          <p><strong>Last Update:</strong> ${new Date().toLocaleString()}</p>
        </div>
      </div>
    </div>
  `;
  
  // Add modal styles
  const style = document.createElement('style');
  style.textContent = `
    .sensor-modal {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      justify-content: center;
      align-items: center;
      z-index: 1000;
    }
    .modal-content {
      background: white;
      border-radius: 12px;
      max-width: 500px;
      width: 90%;
      max-height: 80vh;
      overflow-y: auto;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.5rem;
      border-bottom: 1px solid #e1e5e9;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .modal-header h3 {
      margin: 0;
      font-size: 1.3rem;
    }
    .close-modal {
      font-size: 1.5rem;
      cursor: pointer;
      padding: 0.25rem;
    }
    .modal-body {
      padding: 1.5rem;
    }
    .sensor-detail-section {
      margin-bottom: 1.5rem;
      padding: 1rem;
      background: #f8f9fa;
      border-radius: 8px;
      border-left: 4px solid #667eea;
    }
    .sensor-detail-section h4 {
      margin: 0 0 0.75rem 0;
      color: #495057;
      font-size: 1rem;
    }
    .sensor-detail-section p {
      margin: 0.5rem 0;
      color: #666;
    }
  `;
  document.head.appendChild(style);
  document.body.appendChild(modal);
  
  // Close modal functionality
  modal.querySelector('.close-modal').addEventListener('click', () => {
    document.body.removeChild(modal);
    document.head.removeChild(style);
  });
  
  modal.addEventListener('click', (e) => {
    if (e.target === modal) {
      document.body.removeChild(modal);
      document.head.removeChild(style);
    }
  });
}

function updateMapStatistics() {
  const totalSensors = sensors.length;
  const avgAQI = Math.round(sensors.reduce((sum, s) => sum + s.aqi, 0) / totalSensors);
  const citiesCovered = new Set(sensors.map(s => s.city)).size;
  
  // Update statistics display
  const totalElement = document.getElementById('totalSensorsOnMap');
  const avgElement = document.getElementById('avgAQIOnMap');
  const citiesElement = document.getElementById('citiesCovered');
  
  if (totalElement) totalElement.textContent = totalSensors;
  if (avgElement) avgElement.textContent = avgAQI;
  if (citiesElement) citiesElement.textContent = citiesCovered;
}

function startSmartSimulation() {
  // This would start the actual smart sensor simulation
  alert('🚀 Smart Virtual Sensor Simulation Started!\n\nTo run the actual simulation, execute:\ncd backend && python smart_virtual_sensors.py');
  refreshSmartData();
}

// Smart sensors event listeners - moved to main DOMContentLoaded
function initializeSmartSensors() {
  console.log('Initializing smart sensors...');
  
  // Smart sensors controls
  const smartRefreshBtn = document.getElementById('smart-refresh');
  const smartExportBtn = document.getElementById('smart-export');
  const smartAutoRefreshBtn = document.getElementById('smart-auto-refresh');
  const smartStartBtn = document.getElementById('smart-start-simulation');
  
  console.log('Smart sensor buttons found:', {
    refresh: !!smartRefreshBtn,
    export: !!smartExportBtn,
    autoRefresh: !!smartAutoRefreshBtn,
    start: !!smartStartBtn
  });
  
  if (smartRefreshBtn) {
    smartRefreshBtn.addEventListener('click', refreshSmartData);
    console.log('Refresh button event listener added');
  }
  
  if (smartExportBtn) {
    smartExportBtn.addEventListener('click', exportSmartData);
    console.log('Export button event listener added');
  }
  
  if (smartAutoRefreshBtn) {
    smartAutoRefreshBtn.addEventListener('click', toggleSmartAutoRefresh);
    console.log('Auto refresh button event listener added');
  }
  
  if (smartStartBtn) {
    smartStartBtn.addEventListener('click', startSmartSimulation);
    console.log('Start simulation button event listener added');
  }
  
  // Initialize smart sensors data
  console.log('Calling refreshSmartData...');
  refreshSmartData();
  
  // Render Kosovo map
  console.log('Rendering Kosovo map...');
  renderKosovoMap();
  
  console.log('Smart sensors initialization complete');
}