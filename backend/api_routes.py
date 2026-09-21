from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from bus_service import (
    build_journey_plan,
    geocode_address,
    next_bus_times_for_location,
    uk_local_now,
)

router = APIRouter()


class GeoLookupRequest(BaseModel):
    address: str = Field(..., description="Address, postcode, or place name to geocode")


class NearbyBusesRequest(BaseModel):
    latitude: float
    longitude: float
    time: Optional[str] = None
    limit: int = 4
    within_minutes: int = 60


class JourneyRequest(BaseModel):
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    origin_latitude: Optional[float] = None
    origin_longitude: Optional[float] = None
    destination_latitude: Optional[float] = None
    destination_longitude: Optional[float] = None
    time: Optional[str] = None


@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.post("/geocode")
def geocode_endpoint(payload: GeoLookupRequest) -> Dict[str, Any]:
    try:
        return geocode_address(payload.address)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/nearby-buses")
def nearby_buses(payload: NearbyBusesRequest) -> Dict[str, Any]:
    try:
        dt = uk_local_now() if payload.time is None else datetime.fromisoformat(payload.time)
        return next_bus_times_for_location(
            latitude=payload.latitude,
            longitude=payload.longitude,
            now=dt,
            limit=payload.limit,
            within_minutes=payload.within_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {exc}") from exc


@router.post("/journey")
def journey_endpoint(payload: JourneyRequest) -> Dict[str, Any]:
    try:
        dt = uk_local_now() if payload.time is None else datetime.fromisoformat(payload.time)
        return build_journey_plan(
            origin_latitude=payload.origin_latitude,
            origin_longitude=payload.origin_longitude,
            destination_latitude=payload.destination_latitude,
            destination_longitude=payload.destination_longitude,
            origin_address=payload.origin_address,
            destination_address=payload.destination_address,
            now=dt,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
