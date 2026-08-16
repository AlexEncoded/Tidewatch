const grid = document.querySelector("#buoy-grid");
const errorMessage = document.querySelector("#error");
const refreshButton = document.querySelector("#refresh");
let fleetMap;
let buoyMarkers;
let buoyTracks;

function formatTemperature(reading) {
  return reading ? `${reading.temperature_celsius.toFixed(1)} °C` : "No reading";
}

function formatPressure(reading) {
  return reading ? `${reading.pressure_kpa.toFixed(2)} kPa` : "No reading";
}

function formatSalinity(reading) {
  return reading ? `${reading.salinity_psu.toFixed(2)} PSU` : "No reading";
}

function formatBattery(reading) {
  return reading ? `${reading.battery_percent.toFixed(1)}%` : "No reading";
}

function formatBatteryHealth(health) {
  if (!health || health.status === "insufficient_data") {
    return '<span class="battery-health battery-health-unknown">Insufficient data</span>';
  }
  const delta = health.delta_percent.toFixed(1);
  const details = `A ${health.device_a_percent.toFixed(1)}% · B ${health.device_b_percent.toFixed(1)}% · Δ ${delta}%`;
  return `<span class="battery-health battery-health-${health.status}">${details}</span>`;
}

function formatBatteryAutonomy(analysis) {
  if (!analysis || analysis.estimated_hours_remaining == null) {
    return "Insufficient data";
  }
  return `${analysis.estimated_hours_remaining.toFixed(1)} h`;
}

function formatWave(analysis) {
  return analysis?.estimated_wave_height_m == null
    ? "Insufficient data"
    : `${analysis.estimated_wave_height_m.toFixed(2)} m`;
}

function formatMovement(analysis) {
  if (!analysis || analysis.average_speed_mps == null) return "Insufficient data";
  return `${analysis.average_speed_mps.toFixed(3)} m/s`;
}

function formatQuality(summary) {
  if (!summary || summary.total_readings === 0) {
    return '<span class="quality quality-unknown">No data</span>';
  }

  return `
    <span class="quality-summary">
      <span class="quality quality-good">${summary.good_readings} good</span>
      <span class="quality quality-suspect">${summary.suspect_readings} suspect</span>
      <span class="quality quality-invalid">${summary.invalid_readings} invalid</span>
    </span>`;
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

function renderMap(buoys, locationHistory) {
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
    buoyTracks = L.layerGroup().addTo(fleetMap);
  }

  buoyMarkers.clearLayers();
  buoyTracks.clearLayers();
  locatedBuoys.forEach(({ buoy }) => {
    const marker = L.marker([buoy.latitude, buoy.longitude]);
    marker.bindPopup(
      `<strong>${escapeHtml(buoy.name)}</strong><br>Status: ${escapeHtml(buoy.status)}<br>${escapeHtml(buoy.id)}`,
    );
    marker.addTo(buoyMarkers);
    const history = locationHistory[buoy.id] ?? [];
    if (history.length > 1) {
      L.polyline(
        history.slice().reverse().map(({ latitude, longitude }) => [latitude, longitude]),
        { color: "#66d9ef", weight: 2, opacity: 0.75, dashArray: "6 8" },
      ).addTo(buoyTracks);
    }
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

function renderBuoys(
  buoys,
  analyses,
  sensorHealth,
  qualitySummaries,
  movements,
  batteryHealth,
  batteryAnalyses,
  locationHistory,
) {
  document.querySelector("#total-buoys").textContent = buoys.length;
  document.querySelector("#active-buoys").textContent = buoys.filter(
    ({ buoy }) => buoy.status === "active",
  ).length;
  document.querySelector("#last-refresh").textContent = new Date().toLocaleTimeString();
  renderMap(buoys, locationHistory);

  if (!buoys.length) {
    grid.innerHTML = '<p class="empty">No buoys registered yet.</p>';
    return;
  }

  grid.innerHTML = buoys
    .map(({ buoy, latest_temperature, latest_pressure, latest_salinity, latest_battery }, index) => {
      const status = buoy.status.toLowerCase();
      const analysis = analyses[index];
      const health = sensorHealth[index];
      const quality = qualitySummaries[index];
      const movement = movements[index];
      const batteryStatus = batteryHealth[index];
      const batteryAnalysis = batteryAnalyses[index];
      const seaState = analysis?.sea_state ?? "unknown";
      const sensorStatus = health?.status ?? "unknown";
      const movementSpeed = movement?.average_speed_mps;
      const movementStatus = movementSpeed == null
        ? "unknown"
        : movementSpeed > 1 ? "drifting" : "stable";
      const degradedSensors = health?.degraded_sensors?.length
        ? ` (${health.degraded_sensors.join(", ")})`
        : "";
      return `
        <article class="card">
          <div class="card-top">
            <span class="status status-${status}">${status}</span>
            <span class="buoy-id">${buoy.id}</span>
          </div>
          <h3>${buoy.name}</h3>
          <p class="sensor-health sensor-health-${sensorStatus}">Sensors A/B: ${sensorStatus}${degradedSensors}</p>
          <p class="temperature">${formatTemperature(latest_temperature)}</p>
          <dl>
            <div><dt>Pressure</dt><dd>${formatPressure(latest_pressure)}</dd></div>
            <div><dt>Salinity</dt><dd>${formatSalinity(latest_salinity)}</dd></div>
            <div><dt>Battery</dt><dd>${formatBattery(latest_battery)}</dd></div>
            <div><dt>Battery A/B</dt><dd>${formatBatteryHealth(batteryStatus)}</dd></div>
            <div><dt>Autonomy A/B</dt><dd>${formatBatteryAutonomy(batteryAnalysis.A)} / ${formatBatteryAutonomy(batteryAnalysis.B)}</dd></div>
            <div><dt>Wave estimate</dt><dd>${formatWave(analysis)}</dd></div>
            <div><dt>Sea state</dt><dd><span class="sea-state sea-state-${seaState}">${seaState}</span></dd></div>
            <div><dt>Movement</dt><dd><span class="movement movement-${movementStatus}">${formatMovement(movement)}</span></dd></div>
            <div><dt>Distance tracked</dt><dd>${movement?.distance_travelled_m == null ? "Insufficient data" : `${movement.distance_travelled_m.toFixed(0)} m`}</dd></div>
            <div><dt>Data quality</dt><dd>${formatQuality(quality)}</dd></div>
            <div><dt>Last reading</dt><dd>${formatDate(buoy.last_seen_at)}</dd></div>
            <div><dt>Coordinates</dt><dd>${buoy.latitude ?? "—"}, ${buoy.longitude ?? "—"}</dd></div>
          </dl>
        </article>`;
    })
    .join("");
}

function renderMaintenanceIssues(issues) {
  const panel = document.querySelector("#maintenance-panel");
  const list = document.querySelector("#maintenance-list");
  panel.hidden = !issues.length;
  list.innerHTML = issues
    .map(
      (issue) => `
        <article class="maintenance-item">
          <div>
            <strong>${escapeHtml(issue.buoy_name)}</strong>
            <span class="buoy-id">${escapeHtml(issue.buoy_id)}</span>
          </div>
          <span class="severity severity-${escapeHtml(issue.severity)}">${escapeHtml(issue.severity)}</span>
          <p>${escapeHtml(issue.message)}</p>
        </article>`,
    )
    .join("");
}

async function loadBuoys() {
  errorMessage.hidden = true;
  try {
    const response = await fetch("/api/v1/buoys");
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const buoys = await response.json();
    const maintenanceResponse = await fetch("/api/v1/maintenance/issues");
    const maintenanceIssues = maintenanceResponse.ok
      ? await maintenanceResponse.json()
      : [];
    document.querySelector("#maintenance-issues").textContent = maintenanceIssues.length;
    renderMaintenanceIssues(maintenanceIssues);
    const analyses = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const analysisResponse = await fetch(
          `/api/v1/buoys/${buoy.id}/pressure-analysis`,
        );
        return analysisResponse.ok ? analysisResponse.json() : null;
      }),
    );
    const sensorHealth = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const healthResponse = await fetch(
          `/api/v1/buoys/${buoy.id}/sensor-health`,
        );
        return healthResponse.ok ? healthResponse.json() : null;
      }),
    );
    const qualitySummaries = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const qualityResponse = await fetch(
          `/api/v1/buoys/${buoy.id}/quality-summary`,
        );
        return qualityResponse.ok ? qualityResponse.json() : null;
      }),
    );
    const movements = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const movementResponse = await fetch(
          `/api/v1/buoys/${buoy.id}/movement-analysis`,
        );
        return movementResponse.ok ? movementResponse.json() : null;
      }),
    );
    const locationHistoryEntries = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const locationsResponse = await fetch(
          `/api/v1/buoys/${buoy.id}/locations?limit=50`,
        );
        return [
          buoy.id,
          locationsResponse.ok ? await locationsResponse.json() : [],
        ];
      }),
    );
    const batteryHealth = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const healthResponse = await fetch(
          `/api/v1/buoys/${buoy.id}/battery-health`,
        );
        return healthResponse.ok ? healthResponse.json() : null;
      }),
    );
    const batteryAnalyses = await Promise.all(
      buoys.map(async ({ buoy }) => {
        const [analysisA, analysisB] = await Promise.all(
          ["A", "B"].map(async (deviceId) => {
            const analysisResponse = await fetch(
              `/api/v1/buoys/${buoy.id}/battery-analysis?device_id=${deviceId}`,
            );
            return analysisResponse.ok ? analysisResponse.json() : null;
          }),
        );
        return { A: analysisA, B: analysisB };
      }),
    );
    renderBuoys(
      buoys,
      analyses,
      sensorHealth,
      qualitySummaries,
      movements,
      batteryHealth,
      batteryAnalyses,
      Object.fromEntries(locationHistoryEntries),
    );
  } catch (error) {
    errorMessage.textContent = `Unable to load fleet data: ${error.message}`;
    errorMessage.hidden = false;
  }
}

refreshButton.addEventListener("click", loadBuoys);
loadBuoys();
setInterval(loadBuoys, 15000);
