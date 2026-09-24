"""HTTP routes for buoy device management."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..application.device_registration import register_device as register_device_use_case
from ..application.device_listing import list_devices_for_buoy
from ..application.device_status import update_device_status as update_device_status_use_case
from ..database import get_db
from ..domain.devices import (
    DeviceOwnershipError,
    DeviceRegistrationCommand,
    DeviceRegistrationConflict,
    DeviceStatusCommand,
)
from ..entities import DeviceEntity
from ..application.device_health import summarize_device_health_for_buoy
from ..models import Device, DeviceCreate, DeviceHealth, DeviceStatusUpdate
from ..repository import BuoyRepository


router = APIRouter()


@router.post(
    "/api/v1/buoys/{buoy_id}/devices",
    response_model=Device,
    status_code=status.HTTP_201_CREATED,
    tags=["devices"],
)
def register_device(
    buoy_id: str, payload: DeviceCreate, db: Session = Depends(get_db)
) -> Device:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    try:
        command = DeviceRegistrationCommand(
            device_id=payload.device_id,
            sensor_channel=payload.sensor_channel,
            firmware_version=payload.firmware_version,
        )
        result = register_device_use_case(repository, buoy_id, command)
        return Device.model_validate(result, from_attributes=True)
    except DeviceRegistrationConflict as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except IntegrityError:
        db.rollback()
        if db.get(DeviceEntity, payload.device_id) is not None or any(
            device.sensor_channel == payload.sensor_channel
            for device in repository.list_devices(buoy_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Device or sensor channel already registered",
            ) from None
        raise


@router.get(
    "/api/v1/buoys/{buoy_id}/devices",
    response_model=list[Device],
    tags=["devices"],
)
def list_devices(buoy_id: str, db: Session = Depends(get_db)) -> list[Device]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    snapshots = list_devices_for_buoy(repository, buoy_id)
    return [Device.model_validate(snapshot, from_attributes=True) for snapshot in snapshots]


@router.get(
    "/api/v1/buoys/{buoy_id}/devices/health",
    response_model=list[DeviceHealth],
    tags=["devices"],
)
def device_health(
    buoy_id: str,
    max_age_minutes: float = Query(default=30, gt=0, le=10080),
    db: Session = Depends(get_db),
) -> list[DeviceHealth]:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    snapshots = summarize_device_health_for_buoy(
        repository, buoy_id, datetime.now(timezone.utc), max_age_minutes * 60
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
    db: Session = Depends(get_db),
) -> Device:
    repository = BuoyRepository(db)
    if repository.get_buoy(buoy_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buoy not found")
    try:
        result = update_device_status_use_case(
            repository,
            buoy_id,
            device_id,
            DeviceStatusCommand(status=payload.status),
        )
        return Device.model_validate(result, from_attributes=True)
    except DeviceOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
