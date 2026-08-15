import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 5,
  duration: "30s",
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
};

const baseUrl = __ENV.BASE_URL || "http://localhost:8000";

export function setup() {
  const response = http.post(
    `${baseUrl}/api/v1/buoys`,
    JSON.stringify({ name: `k6-load-${Date.now()}` }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(response, { "load-test buoy created": (result) => result.status === 201 });
  return { buoyId: response.json("id") };
}

export default function (data) {
  const health = http.get(`${baseUrl}/health`);
  check(health, { "health is 200": (response) => response.status === 200 });

  const temperature = 18 + Math.random() * 6;
  const pressure = 100.8 + Math.random() * 1.4;
  const salinity = 34.5 + Math.random() * 2;
  const telemetry = {
    temperatures: [
      { temperature_celsius: temperature, sensor_channel: "A" },
      { temperature_celsius: temperature + 0.03, sensor_channel: "B" },
    ],
    pressures: [
      { pressure_kpa: pressure, sensor_channel: "A" },
      { pressure_kpa: pressure + 0.02, sensor_channel: "B" },
    ],
    salinity: [
      { salinity_psu: salinity, sensor_channel: "A" },
      { salinity_psu: salinity + 0.01, sensor_channel: "B" },
    ],
    battery: { battery_percent: 80 + Math.random() * 15 },
  };
  const ingestion = http.post(
    `${baseUrl}/api/v1/buoys/${data.buoyId}/telemetry`,
    JSON.stringify(telemetry),
    { headers: { "Content-Type": "application/json" } },
  );
  check(ingestion, {
    "telemetry batch accepted": (response) => response.status === 202,
    "telemetry batch contains seven readings": (response) =>
      response.json("accepted_readings") === 7,
    "telemetry batch reports families": (response) =>
      response.json("accepted_by_family.temperature") === 2 &&
      response.json("accepted_by_family.pressure") === 2 &&
      response.json("accepted_by_family.salinity") === 2 &&
      response.json("accepted_by_family.battery") === 1,
  });

  const fleet = http.get(`${baseUrl}/api/v1/buoys`);
  check(fleet, { "fleet is 200": (response) => response.status === 200 });

  const issues = http.get(`${baseUrl}/api/v1/maintenance/issues`);
  check(issues, { "maintenance is 200": (response) => response.status === 200 });
  sleep(1);
}
