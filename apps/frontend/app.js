const grid = document.querySelector("#buoy-grid");
const errorMessage = document.querySelector("#error");
const refreshButton = document.querySelector("#refresh");

function formatTemperature(reading) {
  return reading ? `${reading.temperature_celsius.toFixed(1)} °C` : "No reading";
}

function formatDate(value) {
  return value ? new Date(value).toLocaleString() : "Never";
}

function renderBuoys(buoys) {
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
    .map(({ buoy, latest_temperature }) => {
      const status = buoy.status.toLowerCase();
      return `
        <article class="card">
          <div class="card-top">
            <span class="status status-${status}">${status}</span>
            <span class="buoy-id">${buoy.id}</span>
          </div>
          <h3>${buoy.name}</h3>
          <p class="temperature">${formatTemperature(latest_temperature)}</p>
          <dl>
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
    renderBuoys(await response.json());
  } catch (error) {
    errorMessage.textContent = `Unable to load fleet data: ${error.message}`;
    errorMessage.hidden = false;
  }
}

refreshButton.addEventListener("click", loadBuoys);
loadBuoys();
setInterval(loadBuoys, 15000);
