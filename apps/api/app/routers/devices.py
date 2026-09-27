"""HTTP routes for buoy device management."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..adapter_dependencies import (
    get_device_health_reader,
    get_device_listing_reader,
    get_device_registry,
    get_device_status_registry,
)
from ..application.device_registration import register_device as register_device_use_case
from ..application.device_listing import list_devices_for_buoy
from ..application.device_status import update_device_status as update_device_status_use_case
from ..domain.devices import (
    DeviceOwnershipError,
    DeviceRegistrationCommand,
    DeviceRegistrationConflict,
    DeviceStatusCommand,
)
from ..application.device_health import summarize_device_health_for_buoy
from ..models import Device, DeviceCreate, DeviceHealth, DeviceStatusUpdate
from ..application.ports import DeviceHealthReader
from ..application.device_listing import DeviceListingReader
from ..application.device_registration import DeviceRegistry
from ..application.device_status import DeviceStatusRegistry


router = APIRouter()


@router.post(
    "/api/v1/buoys/{buoy_id}/devices",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
    tags=["devices"],
)
def register_device(
    buoy_id: str,
    payload: DeviceCreate,
    registry: DeviceRegistry = Depends(get_device_registry),
) -> Device:
    if not registry.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    try:
        command = DeviceRegistrationCommand(
            device_id=payload.device_id,
            sensor_channel=payload.sensor_channel,
            firmware_version=payload.firmware_version,
        )
        result = register_device_use_case(registry, buoy_id, command)
        return Device.model_validate(result, from_attributes=True)
    except DeviceRegistrationConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None


@router.get(
    "/api/v1/buoys/{buoy_id}/devices",
    response_model=list[Device],
    tags=["devices"],
)
def list_devices(
    buoy_id: str,
    reader: DeviceListingReader = Depends(get_device_listing_reader),
) -> list[Device]:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    snapshots = list_devices_for_buoy(reader, buoy_id)
    return [Device.model_validate(snapshot, from_attributes=True) for snapshot in snapshots]


@router.get(
    "/api/v1/buoys/{buoy_id}/devices/health",
    response_model=list[DeviceHealth],
    tags=["devices"],
)
def device_health(
    buoy_id: str,
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    reader: DeviceHealthReader = Depends(get_device_health_reader),
) -> list[DeviceHealth]:
    if not reader.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    snapshots = summarize_device_health_for_buoy(
        reader, buoy_id, datetime.now(timezone.utc), max_age_minutes * 60
    )
    return [DeviceHealth.model_validate(snapshot, from_attributes=True) for snapshot in snapshots]


@router.patch(
    "/api/v1/buoys/{buoy_id}/devices/{device_id}/status",
    response_model=Device,
    tags=["devices"],
)
def update_device_status(
    buoy_id: str,
    device_id: str,
    payload: DeviceStatusUpdate,
    registry: DeviceStatusRegistry = Depends(get_device_status_registry),
) -> Device:
    if not registry.buoy_exists(buoy_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    try:
        result = update_device_status_use_case(
            registry,
            buoy_id,
            device_id,
            DeviceStatusCommand(status=payload.status),
        )
        return Device.model_validate(result, from_attributes=True)
    except DeviceOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
