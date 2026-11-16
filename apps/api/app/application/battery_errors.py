"""Application-level errors for battery use cases."""


class BatteryBuoyNotFound(LookupError):
    """Raised when a battery query targets a missing buoy."""


class BatteryDeviceNotFound(LookupError):
    """Raised when a battery operation references a foreign or unknown unit."""


class BatteryTelemetryInvalid(ValueError):
    """Raised when battery telemetry violates a device or channel rule."""
