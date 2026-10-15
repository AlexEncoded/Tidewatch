const test = require("node:test");
const assert = require("node:assert/strict");

const { escapeHtml, formatReading } = require("../sensor-format.js");

test("formats a sensor value with its precision and unit", () => {
  assert.equal(
    formatReading({ dissolved_oxygen_mg_l: 8.126 }, "dissolved_oxygen_mg_l", 2, "mg/L"),
    "8.13 mg/L",
  );
});

test("preserves valid zero values", () => {
  assert.equal(formatReading({ ph: 0 }, "ph", 1, "pH"), "0.0 pH");
});

test("formats wind and current directions in degrees", () => {
  assert.equal(formatReading({ direction: 128.56 }, "direction", 1, "°"), "128.6 °");
});

test("shows a stable placeholder for missing sensor data", () => {
  assert.equal(formatReading(null, "turbidity_ntu", 1, "NTU"), "No reading");
  assert.equal(formatReading({}, "turbidity_ntu", 1, "NTU"), "No reading");
});

test("does not render non-finite telemetry values", () => {
  assert.equal(formatReading({ depth_meters: Infinity }, "depth_meters", 2, "m"), "No reading");
});

test("escapes markup and quotes in buoy-controlled text", () => {
  assert.equal(
    escapeHtml(`<img src=x onerror='alert("x")'>&`),
    "&lt;img src=x onerror=&#39;alert(&quot;x&quot;)&#39;&gt;&amp;",
  );
});
