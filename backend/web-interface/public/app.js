const API_BASE = "http://localhost:8000/api";

let ws = null;
let isConnected = false;

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
