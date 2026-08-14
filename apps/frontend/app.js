const grid = document.querySelector("#buoy-grid");
const errorMessage = document.querySelector("#error");
const refreshButton = document.querySelector("#refresh");
let fleetMap;
let buoyMarkers;

function formatTemperature(reading) {
  return reading ? `${reading.temperature_celsius.toFixed(1)} °C` : "No reading";
}

function formatPressure(reading) {
  return reading ? `${reading.pressure_kpa.toFixed(2)} kPa` : "No reading";
}

function formatSalinity(reading) {
  return reading ? `${reading.salinity_psu.toFixed(2)} PSU` : "No reading";
}

function formatWave(analysis) {
  return analysis?.estimated_wave_height_m == null
    ? "Insufficient data"
    : `${analysis.estimated_wave_height_m.toFixed(2)} m`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;",
  })[character]);
}

function renderMap(buoys) {
  if (typeof L === "undefined") return;

  const locatedBuoys = buoys.filter(
    ({ buoy }) => buoy.latitude != null && buoy.longitude != null,
  );

  if (!fleetMap) {
    fleetMap = L.map("fleet-map").setView([38.5, 1.5], 5);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(fleetMap);
    buoyMarkers = L.layerGroup().addTo(fleetMap);
  }

  buoyMarkers.clearLayers();
  locatedBuoys.forEach(({ buoy }) => {
    const marker = L.marker([buoy.latitude, buoy.longitude]);
    marker.bindPopup(
      `<strong>${escapeHtml(buoy.name)}</strong><br>Status: ${escapeHtml(buoy.status)}<br>${escapeHtml(buoy.id)}`,
    );
    marker.addTo(buoyMarkers);
  });

  if (locatedBuoys.length) {
    fleetMap.fitBounds(
      locatedBuoys.map(({ buoy }) => [buoy.latitude, buoy.longitude]),
      { padding: [24, 24], maxZoom: 9 },
    );
  }
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "Never";
}

function renderBuoys(buoys, analyses) {
  document.querySelector("#total-buoys").textContent = buoys.length;
  document.querySelector("#active-buoys").textContent = buoys.filter(
    ({ buoy }) => buoy.status === "active",
  ).length;
  document.querySelector("#last-refresh").textContent = new Date().toLocaleTimeString();
  renderMap(buoys);

  if (!buoys.length) {
    grid.innerHTML = '<p class="empty">No buoys registered yet.</p>';
    return;
  }

  grid.innerHTML = buoys
    .map(({ buoy, latest_temperature, latest_pressure, latest_salinity }, index) => {
      const status = buoy.status.toLowerCase();
      const analysis = analyses[index];
      const seaState = analysis?.sea_state ?? "unknown";
      return `
        <article class="card">
          <div class="card-top">
            <span class="status status-${status}">${status}</span>
            <span class="buoy-id">${buoy.id}</span>
          </div>
          <h3>${buoy.name}</h3>
          <p class="temperature">${formatTemperature(latest_temperature)}</p>
          <dl>
            <div><dt>Pressure</dt><dd>${formatPressure(latest_pressure)}</dd></div>
            <div><dt>Salinity</dt><dd>${formatSalinity(latest_salinity)}</dd></div>
            <div><dt>Wave estimate</dt><dd>${formatWave(analysis)}</dd></div>
            <div><dt>Sea state</dt><dd><span class="sea-state sea-state-${seaState}">${seaState}</span></dd></div>
            <div><dt>Last reading</dt><dd>${formatDate(buoy.last_seen_at)}</dd></div>
            <div><dt>Coordinates</dt><dd>${buoy.latitude ?? "—"}, ${buoy.longitude ?? "—"}</dd></div>
          </dl>
        </article>`;
    })
    .join("");
}

async function loadBuoys() {
  errorMessage.hidden = true;
  try {
    const response = await fetch("/api/v1/buoys");
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const buoys = await response.json();
    const analyses = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const analysisResponse = await fetch(
          `/api/v1/buoys/${buoy.id}/pressure-analysis`,
        );
        return analysisResponse.ok ? analysisResponse.json() : null;
      }),
    );
    renderBuoys(buoys, analyses);
  } catch (error) {
    errorMessage.textContent = `Unable to load fleet data: ${error.message}`;
    errorMessage.hidden = false;
  }
}

refreshButton.addEventListener("click", loadBuoys);
loadBuoys();
setInterval(loadBuoys, 15000);
