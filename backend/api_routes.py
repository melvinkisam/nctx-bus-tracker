from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import the business logic functions from bus_service.py.
# These functions do the actual calculations and database lookups.
from bus_service import (
    build_journey_plan,
    geocode_address,
    next_bus_times_for_location,
    uk_local_now,
)

# This creates the router object that FastAPI will include in the app.
# Think of it like a "collection of API endpoints".
router = APIRouter()


# A request model defines what JSON data the endpoint expects.
# Pydantic will automatically validate the incoming request body.
class GeoLookupRequest(BaseModel):
    # This is the input for the geocoding endpoint.
    address: str = Field(..., description="Address, postcode, or place name to geocode")


class NearbyBusesRequest(BaseModel):
    # Either use coordinates directly OR send a free-text address.
    # We will geocode the address if latitude/longitude are missing.
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None

    # Optional time when the user wants to search.
    # If omitted, we use the current time in London.
    time: Optional[str] = None

    # How many nearby stops to check and how far ahead to look.
    limit: int = 4
    within_minutes: int = 60


class JourneyRequest(BaseModel):
    # A journey can start from either an address or raw coordinates.
    # The fields are optional because the user may provide either method.
    origin_address: Optional[str] = None
    destination_address: Optional[str] = None
    origin_latitude: Optional[float] = None
    origin_longitude: Optional[float] = None
    destination_latitude: Optional[float] = None
    destination_longitude: Optional[float] = None
    time: Optional[str] = None


# A simple health check endpoint for monitoring the service.
@router.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


# This endpoint converts a human-readable address into latitude/longitude.
# Example: "Victoria Centre, Nottingham" -> map coordinates.
@router.post("/geocode")
def geocode_endpoint(payload: GeoLookupRequest) -> Dict[str, Any]:
    try:
        # Run the geocoding function from bus_service.py.
        return geocode_address(payload.address)
    except ValueError as exc:
        # If the address cannot be found, return a 404 error.
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        # If a dependency is missing, return a 500 error.
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# This endpoint finds the nearest stops to a point and shows upcoming bus times.
@router.post("/nearby-buses")
def nearby_buses(payload: NearbyBusesRequest) -> Dict[str, Any]:
    try:
        # If no time is supplied, use the current date/time in London.
        dt = uk_local_now() if payload.time is None else datetime.fromisoformat(payload.time)

        # If the user supplied an address instead of coordinates, convert it first.
        if payload.address and (payload.latitude is None or payload.longitude is None):
            geocoded = geocode_address(payload.address)
            latitude = geocoded["latitude"]
            longitude = geocoded["longitude"]
        elif payload.latitude is not None and payload.longitude is not None:
            latitude = payload.latitude
            longitude = payload.longitude
        else:
            raise ValueError("Provide either latitude/longitude or an address.")

        # Send the final coordinates to the service logic.
        return next_bus_times_for_location(
            latitude=latitude,
            longitude=longitude,
            now=dt,
            limit=payload.limit,
            within_minutes=payload.within_minutes,
        )
    except ValueError as exc:
        # This catches bad time strings or missing address/coordinate data.
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# This endpoint tries to plan a journey based on a start and destination.
# It accepts either addresses or coordinates.
@router.post("/journey")
def journey_endpoint(payload: JourneyRequest) -> Dict[str, Any]:
    try:
        # Convert the time string to a datetime object if one was given.
        dt = uk_local_now() if payload.time is None else datetime.fromisoformat(payload.time)

        # Pass all the request fields into the journey-building logic.
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
        # This catches bad time strings or missing required coordinate data.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
