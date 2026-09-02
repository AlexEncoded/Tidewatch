# Domain layer

The domain package contains Tidewatch business rules that do not require a
database, HTTP framework, metrics client, or persistence entity. Its services
operate on simple values or small domain inputs and return immutable estimates
or decisions.

Current rules include:

- redundant sensor channel decisions and completeness;
- sensor health thresholds and aggregate status;
- usable telemetry selection and reading quality classification;
- scalar, vector, and circular direction differences;
- movement, pressure, temperature, battery, and wave estimates.

Adapters in the application layer map these results to API response models.
Domain code should remain deterministic and independently testable.
