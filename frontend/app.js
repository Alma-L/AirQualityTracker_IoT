const API_BASE = "http://localhost:8000/api";  // Backend server URL

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
  const container = document.getElementById("latestGrid"); // match HTML ID
  container.innerHTML = "Loading...";
  try {
    const data = await fetchJSON(`${API_BASE}/sensors/latest`);
    container.innerHTML = "";
    data.forEach(row => {
      const d = new Date(row.timestamp);
      const sensorType = row.sensor_type || 'Unknown';
      const el = document.createElement("div");
      el.className = `tile ${getSensorColor(sensorType)}`; // optional color
      el.innerHTML = `
        <div class="sensor-header">
          <span class="sensor-icon-large">${getSensorIcon(sensorType)}</span>
          <h3>${row.sensor_id}</h3>
          <span class="sensor-type-badge">${sensorType}</span>
        </div>
        <div class="sensor-location">📍 ${row.location || 'Unknown'}</div>
        <div class="aqi-display">
          <span class="aqi-value ${row.aqi ? getAQIClass(row.aqi) : ''}">AQI: ${row.aqi || 'N/A'}</span>
          <span class="aqi-category">${row.aqi_category || 'Unknown'}</span>
        </div>
        <div class="sensor-readings">
          <p><strong>PM2.5:</strong> ${row.pm2_5}</p>
          <p><strong>PM10:</strong> ${row.pm10}</p>
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
  tbody.innerHTML = "<tr><td colspan='5'>Loading...</td></tr>";
  try {
    const data = await fetchJSON(`${API_BASE}/sensors/${encodeURIComponent(sensorId)}/recent?limit=${limit}`);
    tbody.innerHTML = "";
    data.forEach(row => {
      const d = new Date(row.timestamp);
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${d.toLocaleString()}</td>
        <td>${row.pm2_5}</td>
        <td>${row.pm10}</td>
        <td>${row.temperature}</td>
        <td>${row.humidity}</td>
      `;
      tbody.appendChild(tr);
    });
    if (data.length === 0) {
      tbody.innerHTML = "<tr><td colspan='5'><em>No rows.</em></td></tr>";
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan='5' style="color:#fca5a5">Error: ${err.message}</td></tr>`;
  }
}

document.getElementById("refresh").addEventListener("click", loadLatest);
document.getElementById("sensor-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const id = document.getElementById("sensor-id").value || "sensor-1";
  const limit = parseInt(document.getElementById("limit").value || "20", 10);
  loadRecent(id, limit);
});
document.getElementById("save-csv").addEventListener("click", async () => {
  try {
    const response = await fetch("http://127.0.0.1:5000/save_csv");
    const data = await response.json();
    if (data.status === "ok") {
      alert(`CSV saved successfully: ${data.file}`);
    } else {
      alert("Failed to save CSV");
    }
  } catch (err) {
    console.error(err);
    alert("Error saving CSV");
  }
});


loadLatest();
loadRecent("sensor-1", 20);
