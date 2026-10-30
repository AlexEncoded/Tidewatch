# Domain layer

The domain package contains Tidewatch business rules that do not require a
database, HTTP framework, metrics client, or persistence entity. Its services
operate on simple values or small domain inputs and return immutable estimates
or decisions.

Current rules include:

- redundant sensor channel decisions and completeness;
- sensor health thresholds and aggregate status. The
  `SENSOR_DEGRADATION_THRESHOLDS` map is the explicit margin contract for
  every delta produced by the sensor-health application service;
- device heartbeat freshness and operational health summaries;
- redundant battery health with finite, non-negative thresholds and bounded
  battery percentages;
- usable telemetry selection and reading quality classification;
- durable queue retry timing and bounds;
- maintenance issue classification from buoy, sensor and device snapshots;
- scalar, vector, and circular direction differences;
- movement, pressure, temperature, battery, and wave estimates.

Adapters in the application layer map these results to API response models.
Domain code should remain deterministic and independently testable.
