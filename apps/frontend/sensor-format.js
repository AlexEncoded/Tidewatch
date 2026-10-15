(function exposeSensorFormatting(root, factory) {
  const formatting = factory();
  if (typeof module === "object" && module.exports) {
    module.exports = formatting;
  } else {
    root.TidewatchSensorFormatting = formatting;
  }
})(globalThis, function createSensorFormatting() {
  function formatReading(reading, property, digits, unit) {
    const value = reading?.[property];
    if (typeof value !== "number" || !Number.isFinite(value)) {
      return "No reading";
    }
    return `${value.toFixed(digits)} ${unit}`;
  }

  return { formatReading };
});
