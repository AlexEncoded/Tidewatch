"""HTTP routes for buoy device management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..application.device_registration import register_device as register_device_use_case
from ..application.device_status import update_device_status as update_device_status_use_case
from ..database import get_db
from ..domain.devices import DeviceOwnershipError, DeviceRegistrationConflict
from ..entities import DeviceEntity
from ..models import Device, DeviceCreate, DeviceStatusUpdate
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
        return register_device_use_case(repository, buoy_id, payload)
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
    return repository.list_devices(buoy_id)


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
        return update_device_status_use_case(repository, buoy_id, device_id, payload)
    except DeviceOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from None
