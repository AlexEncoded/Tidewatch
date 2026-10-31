# Domain layer

The domain package contains Tidewatch business rules that do not require a
database, HTTP framework, metrics client, or persistence entity. Its services
operate on simple values or small domain inputs and return immutable estimates
or decisions.

Current rules include:

- redundant sensor channel decisions and completeness;
- missing-channel evaluation handles omitted A/B keys and rejects unknown
  physical channels;
- sensor health delta calculations, thresholds, and aggregate status. The
  `SENSOR_DEGRADATION_THRESHOLDS` map is the explicit margin contract for each
  domain delta; deltas must be finite, non-negative, and use a registered
  sensor name;
- device heartbeat freshness and operational health summaries;
- redundant battery health with finite, non-negative thresholds and bounded
  battery percentages; health snapshots are immutable and validate the status,
  delta, and lower-charge device together;
- historical battery discharge estimation orders samples by measurement time
  and rejects percentages outside the physical range;
- usable telemetry selection and reading quality classification;
- durable queue retry timing and bounds;
- maintenance issue classification from buoy, sensor and device snapshots;
- buoy silence and drift classification with finite, positive thresholds and
  physically valid speed inputs;
- scalar, vector, and circular direction differences;
- movement, pressure, temperature, battery, and wave estimates.

Adapters in the application layer map these results to API response models.
Domain code should remain deterministic and independently testable.
