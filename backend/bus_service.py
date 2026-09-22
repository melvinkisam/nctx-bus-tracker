from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import text

from database.database import session_local
from models.models import Stop

try:
    from geopy.geocoders import Nominatim
except ImportError:  # pragma: no cover - only used when optional dependency is absent
    Nominatim = None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two latitude/longitude points."""
    radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


def find_nearest_stops(
    latitude: float,
    longitude: float,
    limit: int = 4,
    session=None,
) -> List[Dict[str, Any]]:
    """Find the nearest stops around a coordinate from the SQLite bus_stops table."""
    db = session or session_local()
    try:
        rows = db.query(Stop).all()
        stops = []
        for stop in rows:
            distance_km = haversine_km(latitude, longitude, stop.latitude, stop.longitude)
            stops.append(
                {
                    "stop_id": stop.stop_id,
                    "stop_name": stop.stop_name,
                    "latitude": stop.latitude,
                    "longitude": stop.longitude,
                    "distance_km": round(distance_km, 3),
                }
            )

        return sorted(stops, key=lambda item: item["distance_km"])[:limit]
    finally:
        if session is None:
            db.close()


def geocode_address(address: str, user_agent: str = "nctx-bus-tracker") -> Dict[str, Any]:
    """Convert a human-readable address or place name into latitude/longitude using Nominatim."""
    if Nominatim is None:
        raise RuntimeError(
            "geopy is not installed. Install it with: pip install geopy"
        )

    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(address, exactly_one=True, timeout=10)

    if location is None:
        raise ValueError(f"Could not geocode address: {address}")

    return {
        "address": address,
        "latitude": float(location.latitude),
        "longitude": float(location.longitude),
        "display_name": location.address,
    }


def uk_local_now() -> datetime:
    return datetime.now(ZoneInfo("Europe/London"))


def parse_gtfs_time(value: str) -> int:
    """Convert a GTFS time string like 07:45:00 into seconds since midnight."""
    hour_str, minute_str, second_str = value.split(":")
    return int(hour_str) * 3600 + int(minute_str) * 60 + int(second_str)


def database_has_table(table_name: str) -> bool:
    db = session_local()
    try:
        row = db.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
            {"table_name": table_name},
        ).fetchone()
        return row is not None
    finally:
        db.close()


def get_next_buses_for_stop(
    stop_id: str,
    now: Optional[datetime] = None,
    within_minutes: int = 60,
) -> List[Dict[str, Any]]:
    """Return upcoming departures for a stop from the GTFS stop_times table if it exists."""
    if not database_has_table("stop_times"):
        return []

    now_dt = now or uk_local_now()
    current_seconds = now_dt.hour * 3600 + now_dt.minute * 60 + now_dt.second
    end_seconds = current_seconds + (within_minutes * 60)

    db = session_local()
    try:
        rows = db.execute(
            text("SELECT departure_time, trip_id FROM stop_times WHERE stop_id = :stop_id"),
            {"stop_id": stop_id},
        ).fetchall()
    finally:
        db.close()

    upcoming = []
    for departure_time, trip_id in rows:
        try:
            departure_seconds = parse_gtfs_time(departure_time)
        except ValueError:
            continue

        if departure_seconds < current_seconds:
            continue
        if departure_seconds > end_seconds:
            continue

        upcoming.append(
            {
                "trip_id": trip_id,
                "departure_time": departure_time,
                "departure_datetime": (now_dt.date().strftime("%Y-%m-%d") + " " + departure_time),
            }
        )

    return sorted(upcoming, key=lambda item: item["departure_time"])[:10]


def next_bus_times_for_location(
    latitude: float,
    longitude: float,
    now: Optional[datetime] = None,
    limit: int = 4,
    within_minutes: int = 60,
) -> Dict[str, Any]:
    """Return the four nearest stops and their upcoming departures within the next hour."""
    nearest_stops = find_nearest_stops(latitude, longitude, limit=limit)
    result = {
        "location": {"latitude": latitude, "longitude": longitude},
        "search_time": (now or uk_local_now()).isoformat(),
        "nearest_stops": nearest_stops,
        "next_buses": [],
        "status": "ok",
    }

    if not database_has_table("stop_times"):
        result["status"] = "unavailable"
        result["message"] = (
            "The database contains stop locations but not the GTFS stop_times schedule. "
            "Add the GTFS stop_times table or import the timetable feed to enable next-bus lookups."
        )
        return result

    for stop in nearest_stops:
        stop_id = stop["stop_id"]
        buses = get_next_buses_for_stop(stop_id, now=now, within_minutes=within_minutes)
        result["next_buses"].append(
            {
                "stop_id": stop_id,
                "stop_name": stop["stop_name"],
                "distance_km": stop["distance_km"],
                "upcoming_departures": buses,
            }
        )

    return result


def build_journey_plan(
    origin_latitude: Optional[float] = None,
    origin_longitude: Optional[float] = None,
    destination_latitude: Optional[float] = None,
    destination_longitude: Optional[float] = None,
    origin_address: Optional[str] = None,
    destination_address: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Best-effort journey planning wrapper. The database currently does not contain enough route data for a full trip planner."""
    if origin_address and (origin_latitude is None or origin_longitude is None):
        geocoded_origin = geocode_address(origin_address)
        origin_latitude = geocoded_origin["latitude"]
        origin_longitude = geocoded_origin["longitude"]

    if destination_address and (destination_latitude is None or destination_longitude is None):
        geocoded_destination = geocode_address(destination_address)
        destination_latitude = geocoded_destination["latitude"]
        destination_longitude = geocoded_destination["longitude"]

    if origin_latitude is None or origin_longitude is None or destination_latitude is None or destination_longitude is None:
        raise ValueError("Origin and destination coordinates or addresses are required.")

    origin_stop = find_nearest_stops(origin_latitude, origin_longitude, limit=1)[0]
    destination_stop = find_nearest_stops(destination_latitude, destination_longitude, limit=1)[0]

    if not database_has_table("stop_times") or not database_has_table("trips"):
        return {
            "status": "unavailable",
            "message": (
                "A full journey planner is not possible yet because the database only holds stop coordinates. "
                "To support route planning, import the GTFS trip, route and stop_times tables into SQLite and then connect the stop sequence logic to each trip."
            ),
            "origin_stop": origin_stop,
            "destination_stop": destination_stop,
            "search_time": (now or uk_local_now()).isoformat(),
        }

    return {
        "status": "best_effort",
        "message": (
            "The current data model can identify the nearest origin and destination stops, but a complete route planner still requires GTFS trip-to-stop sequencing and route matching."
        ),
        "origin_stop": origin_stop,
        "destination_stop": destination_stop,
        "search_time": (now or uk_local_now()).isoformat(),
    }
