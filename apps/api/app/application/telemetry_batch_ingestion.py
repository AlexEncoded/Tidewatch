"""Transport-independent orchestration for telemetry batch ingestion."""

from dataclasses import dataclass
from datetime import datetime, timezone

from .battery_ingestion import record_battery_reading
from .device_heartbeat import record_device_heartbeat
from .movement_analysis import analyze_movement_for_buoy
from .telemetry_batch import TelemetryBatchCommand
from .telemetry_ports import (
    TelemetryBatchUnitOfWork,
    TelemetryIngestionJobStore,
    TelemetryMetrics,
)
from .telemetry_ports import TelemetryIngestionGateway
from .telemetry_ingestion import (
    atomic_telemetry_batch,
    build_location_snapshot,
    build_battery_snapshot,
    build_underwater_acoustic_snapshot,
    build_acoustic_altimeter_snapshot,
    build_atmospheric_pressure_snapshot,
    build_air_temperature_snapshot,
    build_humidity_snapshot,
    build_rainfall_snapshot,
    build_chlorophyll_a_snapshot,
    build_conductivity_snapshot,
    build_ph_snapshot,
    build_dissolved_oxygen_snapshot,
    build_imu_snapshot,
    build_marine_current_snapshot,
    build_turbidity_snapshot,
    build_ambient_light_snapshot,
    build_wind_snapshot,
    build_pressure_snapshot,
    build_salinity_snapshot,
    build_temperature_snapshot,
    empty_accepted_reading_counts,
)
from ..domain.devices import DeviceOwnershipError


class TelemetryBuoyNotFound(LookupError):
    """Raised when a telemetry batch references an unknown buoy."""


class TelemetryDeviceNotFound(LookupError):
    """Raised when a batch references an unknown or foreign device."""


class TelemetryBatchInvalid(ValueError):
    """Raised when a telemetry batch violates a device or sensor rule."""


@dataclass(frozen=True)
class TelemetryIngestOutcome:
    buoy_id: str
    accepted_readings: int
    accepted_by_family: dict[str, int]


@dataclass(frozen=True)
class TelemetryQueuedOutcome:
    job_id: str
    status_url: str


def record_quality_metric(
    metrics: TelemetryMetrics,
    buoy_id: str,
    sensor_family: str,
    sensor_channel: str,
    quality: str,
) -> None:
    metrics.metric("reading_quality_total").labels(
        buoy_id=buoy_id,
        sensor_family=sensor_family,
        sensor_channel=sensor_channel,
        quality=quality,
    ).inc()


def _latest_measurement_time(payload: TelemetryBatchCommand) -> datetime | None:
    timestamps = [
        reading.get("measured_at")
        for family in payload.readings.values()
        for reading in family
        if isinstance(reading.get("measured_at"), datetime)
    ]
    if payload.location is not None:
        location_time = payload.location.get("measured_at")
        if isinstance(location_time, datetime):
            timestamps.append(location_time)
    if payload.device_runtime is not None:
        runtime_time = payload.device_runtime.get("measured_at")
        if isinstance(runtime_time, datetime):
            timestamps.append(runtime_time)
    if payload.device_communications is not None:
        communications_time = payload.device_communications.get("measured_at")
        if isinstance(communications_time, datetime):
            timestamps.append(communications_time)
    if not timestamps:
        return None
    normalized = [
        value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
        for value in timestamps
    ]
    return max(normalized, key=lambda value: value.timestamp())


@atomic_telemetry_batch
def process_telemetry_batch(
    buoy_id: str,
    payload: TelemetryBatchCommand,
    *,
    gateway: TelemetryIngestionGateway,
    unit_of_work: TelemetryBatchUnitOfWork,
    metrics: TelemetryMetrics,
    jobs: TelemetryIngestionJobStore | None = None,
    idempotency_key: str | None = None,
    queued_mode: bool = False,
    clock_observation_at: datetime | None = None,
) -> TelemetryIngestOutcome | TelemetryQueuedOutcome:
    if not gateway.buoy_exists(buoy_id):
        raise TelemetryBuoyNotFound("Buoy not found")
    if payload.device_id is not None:
        try:
            sensor_channels = (
                reading["sensor_channel"]
                for family_name, family in payload.readings.items()
                if family_name != "battery"
                for reading in family
            )
            sensor_channels = (
                *sensor_channels,
                *(reading["device_id"] for reading in payload.readings["battery"]),
            )
            device, seen_at = record_device_heartbeat(
                gateway,
                buoy_id,
                payload.device_id,
                sensor_channels=sensor_channels,
            )
        except DeviceOwnershipError as exc:
            raise TelemetryDeviceNotFound(str(exc)) from None
        except ValueError as exc:
            raise TelemetryBatchInvalid(str(exc)) from None
        metrics.metric("device_last_seen_timestamp_seconds").labels(
            buoy_id=buoy_id,
            device_id=device.device_id,
            sensor_channel=device.sensor_channel,
        ).set(seen_at.timestamp())
        metrics.metric("buoy_last_seen_timestamp_seconds").labels(buoy_id=buoy_id).set(
            seen_at.timestamp()
        )
        if clock_observation_at is not None:
            latest_measurement = _latest_measurement_time(payload)
            if latest_measurement is not None:
                metrics.metric("device_clock_offset_seconds").labels(
                    buoy_id=buoy_id,
                    device_id=device.device_id,
                    sensor_channel=device.sensor_channel,
                ).set((latest_measurement - clock_observation_at).total_seconds())
            runtime_labels = {
                "buoy_id": buoy_id,
                "device_id": device.device_id,
                "sensor_channel": device.sensor_channel,
            }
            if payload.device_runtime is not None:
                metrics.metric("device_cpu_usage_percent").labels(
                    **runtime_labels
                ).set(payload.device_runtime["cpu_usage_percent"])
                metrics.metric("device_memory_usage_percent").labels(
                    **runtime_labels
                ).set(payload.device_runtime["memory_usage_percent"])
            if payload.device_communications is not None:
                communications = payload.device_communications
                if communications["packet_loss_percent"] is not None:
                    metrics.metric("device_packet_loss_percent").labels(
                        **runtime_labels
                    ).set(communications["packet_loss_percent"])
                if communications["round_trip_latency_ms"] is not None:
                    metrics.metric("device_round_trip_latency_ms").labels(
                        **runtime_labels
                    ).set(communications["round_trip_latency_ms"])
    else:
        seen_at = None

    if queued_mode and jobs is not None:
        if payload.device_id is None:
            seen_at = datetime.now(timezone.utc)
            gateway.mark_buoy_seen_by_id(buoy_id, seen_at)
            metrics.metric("buoy_last_seen_timestamp_seconds").labels(buoy_id=buoy_id).set(
                seen_at.timestamp()
            )
        job = jobs.enqueue(
            buoy_id,
            payload.as_json_mapping(),
            idempotency_key=idempotency_key,
        )
        status_url = f"/api/v1/telemetry/jobs/{job.job_id}"
        return TelemetryQueuedOutcome(job_id=job.job_id, status_url=status_url)

    if payload.location is not None:
        location = build_location_snapshot(
            buoy_id, dict(payload.location), payload.device_id
        )
        gateway.add_location(location)
        if location.altitude_meters is not None:
            metrics.metric("current_gnss_altitude_meters").labels(buoy_id=buoy_id).set(location.altitude_meters)
        if location.speed_mps is not None:
            metrics.metric("current_gnss_speed_mps").labels(buoy_id=buoy_id).set(location.speed_mps)
        if location.hdop is not None:
            metrics.metric("current_gnss_hdop").labels(buoy_id=buoy_id).set(location.hdop)
        if location.satellites is not None:
            metrics.metric("current_gnss_satellites").labels(buoy_id=buoy_id).set(location.satellites)
        movement = analyze_movement_for_buoy(gateway, buoy_id, 50)
        if movement.average_speed_mps is not None:
            metrics.metric("buoy_movement_speed_mps").labels(buoy_id=buoy_id).set(
                movement.average_speed_mps
            )

    accepted = 0
    accepted_by_family = empty_accepted_reading_counts()
    for reading_payload in payload.readings["temperatures"]:
        reading = build_temperature_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_temperature(reading)
        metrics.metric("temperature_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_temperature_celsius").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.temperature_celsius)
        record_quality_metric(metrics, buoy_id, "temperature", reading.sensor_channel, reading.quality)
        accepted_by_family["temperature"] += 1
        accepted += 1

    for reading_payload in payload.readings["pressures"]:
        reading = build_pressure_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_pressure(reading)
        metrics.metric("pressure_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_pressure_kpa").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.pressure_kpa)
        record_quality_metric(metrics, buoy_id, "pressure", reading.sensor_channel, reading.quality)
        accepted_by_family["pressure"] += 1
        accepted += 1

    for reading_payload in payload.readings["salinity"]:
        reading = build_salinity_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_salinity(reading)
        metrics.metric("salinity_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_salinity_psu").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.salinity_psu)
        record_quality_metric(metrics, buoy_id, "salinity", reading.sensor_channel, reading.quality)
        accepted_by_family["salinity"] += 1
        accepted += 1

    for reading_payload in payload.readings["imu"]:
        reading = build_imu_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_imu(reading)
        metrics.metric("imu_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        for axis, value in {
            "x": reading.acceleration_x_mps2,
            "y": reading.acceleration_y_mps2,
            "z": reading.acceleration_z_mps2,
        }.items():
            metrics.metric("current_imu_acceleration_mps2").labels(
                buoy_id=buoy_id, sensor_channel=reading.sensor_channel, axis=axis
            ).set(value)
        for axis, value in {
            "x": reading.angular_velocity_x_dps,
            "y": reading.angular_velocity_y_dps,
            "z": reading.angular_velocity_z_dps,
        }.items():
            metrics.metric("current_imu_angular_velocity_dps").labels(
                buoy_id=buoy_id, sensor_channel=reading.sensor_channel, axis=axis
            ).set(value)
        record_quality_metric(metrics, buoy_id, "imu", reading.sensor_channel, reading.quality)
        accepted_by_family["imu"] += 1
        accepted += 1

    for reading_payload in payload.readings["ambient_light"]:
        reading = build_ambient_light_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_ambient_light(reading)
        metrics.metric("ambient_light_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_ambient_light_lux").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.illuminance_lux)
        record_quality_metric(
            metrics,
            buoy_id, "ambient_light", reading.sensor_channel, reading.quality
        )
        accepted_by_family["ambient_light"] += 1
        accepted += 1

    for reading_payload in payload.readings["wind"]:
        reading = build_wind_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_wind(reading)
        metrics.metric("wind_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_wind_speed_mps").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.wind_speed_mps)
        metrics.metric("current_wind_direction_degrees").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.wind_direction_degrees)
        record_quality_metric(metrics, buoy_id, "wind", reading.sensor_channel, reading.quality)
        accepted_by_family["wind"] += 1
        accepted += 1

    for reading_payload in payload.readings["marine_current"]:
        reading = build_marine_current_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_marine_current(reading)
        metrics.metric("marine_current_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_marine_current_speed_mps").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.current_speed_mps)
        metrics.metric("current_marine_current_direction_degrees").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.current_direction_degrees)
        record_quality_metric(
            metrics,
            buoy_id, "marine_current", reading.sensor_channel, reading.quality
        )
        accepted_by_family["marine_current"] += 1
        accepted += 1

    for reading_payload in payload.readings["turbidity"]:
        reading = build_turbidity_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_turbidity(reading)
        metrics.metric("turbidity_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_turbidity_ntu").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.turbidity_ntu)
        record_quality_metric(
            metrics,
            buoy_id, "turbidity", reading.sensor_channel, reading.quality
        )
        accepted_by_family["turbidity"] += 1
        accepted += 1

    for reading_payload in payload.readings["dissolved_oxygen"]:
        reading = build_dissolved_oxygen_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_dissolved_oxygen(reading)
        metrics.metric("dissolved_oxygen_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_dissolved_oxygen_mg_l").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.dissolved_oxygen_mg_l)
        record_quality_metric(
            metrics,
            buoy_id, "dissolved_oxygen", reading.sensor_channel, reading.quality
        )
        accepted_by_family["dissolved_oxygen"] += 1
        accepted += 1

    for reading_payload in payload.readings["ph"]:
        reading = build_ph_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_ph(reading)
        metrics.metric("ph_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_ph").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.ph)
        record_quality_metric(metrics, buoy_id, "ph", reading.sensor_channel, reading.quality)
        accepted_by_family["ph"] += 1
        accepted += 1

    for reading_payload in payload.readings["conductivity"]:
        reading = build_conductivity_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_conductivity(reading)
        metrics.metric("conductivity_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_conductivity_us_cm").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.conductivity_us_cm)
        record_quality_metric(
            metrics,
            buoy_id, "conductivity", reading.sensor_channel, reading.quality
        )
        accepted_by_family["conductivity"] += 1
        accepted += 1

    for reading_payload in payload.readings["chlorophyll_a"]:
        reading = build_chlorophyll_a_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_chlorophyll_a(reading)
        metrics.metric("chlorophyll_a_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_chlorophyll_a_ug_l").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.chlorophyll_a_ug_l)
        record_quality_metric(
            metrics,
            buoy_id, "chlorophyll_a", reading.sensor_channel, reading.quality
        )
        accepted_by_family["chlorophyll_a"] += 1
        accepted += 1

    for reading_payload in payload.readings["rainfall"]:
        reading = build_rainfall_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_rainfall(reading)
        metrics.metric("rainfall_readings_total").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).inc()
        metrics.metric("current_rainfall_mm_h").labels(
            buoy_id=buoy_id, sensor_channel=reading.sensor_channel
        ).set(reading.rainfall_mm_h)
        record_quality_metric(metrics, buoy_id, "rainfall", reading.sensor_channel, reading.quality)
        accepted_by_family["rainfall"] += 1
        accepted += 1

    for reading_payload in payload.readings["humidity"]:
        reading = build_humidity_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_humidity(reading)
        metrics.metric("humidity_readings_total").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        metrics.metric("current_humidity_percent").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.humidity_percent)
        record_quality_metric(metrics, buoy_id, "humidity", reading.sensor_channel, reading.quality)
        accepted_by_family["humidity"] += 1
        accepted += 1

    for reading_payload in payload.readings["air_temperature"]:
        reading = build_air_temperature_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_air_temperature(reading)
        metrics.metric("air_temperature_readings_total").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        metrics.metric("current_air_temperature_celsius").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.air_temperature_celsius)
        record_quality_metric(metrics, buoy_id, "air_temperature", reading.sensor_channel, reading.quality)
        accepted_by_family["air_temperature"] += 1
        accepted += 1

    for reading_payload in payload.readings["atmospheric_pressure"]:
        reading = build_atmospheric_pressure_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_atmospheric_pressure(reading)
        metrics.metric("atmospheric_pressure_readings_total").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        metrics.metric("current_atmospheric_pressure_kpa").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.atmospheric_pressure_kpa)
        record_quality_metric(metrics, buoy_id, "atmospheric_pressure", reading.sensor_channel, reading.quality)
        accepted_by_family["atmospheric_pressure"] += 1
        accepted += 1

    for reading_payload in payload.readings["acoustic_altimeter"]:
        reading = build_acoustic_altimeter_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_acoustic_altimeter(reading)
        metrics.metric("acoustic_altimeter_readings_total").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        metrics.metric("current_acoustic_altimeter_depth_meters").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.depth_meters)
        record_quality_metric(metrics, buoy_id, "acoustic_altimeter", reading.sensor_channel, reading.quality)
        accepted_by_family["acoustic_altimeter"] += 1
        accepted += 1

    for reading_payload in payload.readings["underwater_acoustic"]:
        reading = build_underwater_acoustic_snapshot(
            buoy_id, dict(reading_payload), payload.device_id
        )
        gateway.add_underwater_acoustic(reading)
        metrics.metric("underwater_acoustic_readings_total").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).inc()
        metrics.metric("current_underwater_acoustic_echo_intensity_db").labels(buoy_id=buoy_id, sensor_channel=reading.sensor_channel).set(reading.echo_intensity_db)
        record_quality_metric(metrics, buoy_id, "underwater_acoustic", reading.sensor_channel, reading.quality)
        accepted_by_family["underwater_acoustic"] += 1
        accepted += 1

    for battery_payload in payload.readings["battery"]:
        battery_data = dict(battery_payload)
        if battery_data["physical_device_id"] is None:
            battery_data["physical_device_id"] = payload.device_id
        battery = build_battery_snapshot(buoy_id, battery_data)
        battery_received_at = seen_at or datetime.now(timezone.utc)
        try:
            saved_battery = record_battery_reading(
                gateway, battery, battery_received_at
            )
        except DeviceOwnershipError as exc:
            raise TelemetryDeviceNotFound(str(exc)) from None
        except ValueError as exc:
            raise TelemetryBatchInvalid(str(exc)) from None
        metrics.metric("battery_percent").labels(buoy_id=buoy_id).set(battery.battery_percent)
        metrics.metric("battery_device_percent").labels(
            buoy_id=buoy_id, device_id=battery.device_id
        ).set(battery.battery_percent)
        if saved_battery.physical_device_id is not None and payload.device_id is None:
            metrics.metric("device_last_seen_timestamp_seconds").labels(
                buoy_id=buoy_id,
                device_id=saved_battery.physical_device_id,
                sensor_channel=saved_battery.device_id,
            ).set(battery_received_at.timestamp())
        metrics.metric("buoy_last_seen_timestamp_seconds").labels(buoy_id=buoy_id).set(
            battery_received_at.timestamp()
        )
        accepted_by_family["battery"] += 1
        accepted += 1

    if payload.device_id is None and accepted:
        metrics.metric("buoy_last_seen_timestamp_seconds").labels(buoy_id=buoy_id).set(
            datetime.now(timezone.utc).timestamp()
        )

    return TelemetryIngestOutcome(
        buoy_id=buoy_id,
        accepted_readings=accepted,
        accepted_by_family=accepted_by_family,
    )

