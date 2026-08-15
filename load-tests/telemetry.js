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

export default function () {
  const health = http.get(`${baseUrl}/health`);
  check(health, { "health is 200": (response) => response.status === 200 });

  const fleet = http.get(`${baseUrl}/api/v1/buoys`);
  check(fleet, { "fleet is 200": (response) => response.status === 200 });

  const issues = http.get(`${baseUrl}/api/v1/maintenance/issues`);
  check(issues, { "maintenance is 200": (response) => response.status === 200 });
  sleep(1);
}
