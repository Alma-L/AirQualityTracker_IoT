const API_BASE = "http://localhost:5000/api";

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
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
      el.className = "tile";
      el.innerHTML = `
        <h3>${row.sensor_id}</h3>
        <p><strong>PM2.5:</strong> ${row.pm2_5}</p>
        <p><strong>PM10:</strong> ${row.pm10}</p>
        <p><strong>Temp:</strong> ${row.temperature} °C</p>
        <p><strong>Humidity:</strong> ${row.humidity} %</p>
        <p><small>${d.toLocaleString()}</small></p>
      `;
      container.appendChild(el);
    });
    if (data.length === 0) container.innerHTML = "<em>No data yet. Start the producer.</em>";
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

loadLatest();
loadRecent("sensor-1", 20);
