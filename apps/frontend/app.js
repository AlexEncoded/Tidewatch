const grid = document.querySelector("#buoy-grid");
const errorMessage = document.querySelector("#error");
const refreshButton = document.querySelector("#refresh");

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

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "Never";
}

function renderBuoys(buoys, analyses) {
  document.querySelector("#total-buoys").textContent = buoys.length;
  document.querySelector("#active-buoys").textContent = buoys.filter(
    ({ buoy }) => buoy.status === "active",
  ).length;
  document.querySelector("#last-refresh").textContent = new Date().toLocaleTimeString();

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
