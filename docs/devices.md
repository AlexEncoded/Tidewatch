# Physical buoy devices

Each buoy can register one physical unit for channel `A` and one for channel
`B`. Apply database migration `0046_devices` before using the registry.

Register a unit with `POST /api/v1/buoys/{buoy_id}/devices`:

```json
{
  "device_id": "buoy-01-unit-a",
  "sensor_channel": "A",
  "firmware_version": "3.0.0"
}
```

The response is `201` and includes the buoy ID, registration timestamp and
initial status `active`. Firmware is optional. Device IDs are globally unique;
channels are unique within a buoy. Duplicate IDs or occupied channels return
`409`, including conflicts that occur between validation and insertion.

`GET /api/v1/buoys/{buoy_id}/devices` lists registered units in channel order.
An existing buoy with no registered devices returns an empty list.

Telemetry batches may include the optional `device_id` field. When present,
the API verifies that the unit belongs to the buoy and records its latest
communication time. A device from another buoy or an unknown device returns
`404`. Batches without `device_id` remain supported for legacy senders.

Use `PATCH /api/v1/buoys/{buoy_id}/devices/{device_id}/status` with
`{"status": "maintenance"}` to update a unit. Allowed states are `active`,
`maintenance` and `inactive`. Invalid states return `422`; unknown buoys,
unknown devices and devices belonging to another buoy return `404`.

The registry currently records administrative identity and status. Changing
a device's status does not change the buoy's status or filter telemetry.
Batch GNSS positions and IMU readings now retain their originating
`device_id`; other sensor families will be associated incrementally.
