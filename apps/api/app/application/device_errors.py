"""Application-level errors for physical-device use cases."""


class DeviceRegistrationConflictError(ValueError):
    """Raised when a device conflicts with the buoy's registrations."""


class DeviceNotFound(LookupError):
    """Raised when a device is unknown or belongs to another buoy."""
