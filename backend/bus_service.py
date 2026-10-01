from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import text

# Import the database session and the Stop model so we can query bus stops.
from database.database import session_local
from models.models import Stop

# geopy is optional: if it is not installed, we still want the code to load
# and fail only when the geocode endpoint is actually used.
try:
    from geopy.geocoders import Nominatim
except ImportError:  # pragma: no cover - only used when optional dependency is absent
    Nominatim = None


# ------------------------------------------------------------
# 1. Basic maths helper
# ------------------------------------------------------------
# This function calculates the distance between two points on Earth.
# We use it to find the closest bus stops to a user's chosen location.
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return the great-circle distance in kilometres between two latitude/longitude points."""
    radius_km = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # The Haversine formula is a common way to calculate a distance
    # between two lat/lon coordinates on a sphere.
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius_km * c


# ------------------------------------------------------------
# 2. Finding nearby stops
# ------------------------------------------------------------
# This function checks every stop in the database and returns the closest ones.
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
            # For each stop, calculate how far the user is away.
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

        # Sort by nearest first, then keep only the requested number.
        return sorted(stops, key=lambda item: item["distance_km"])[:limit]
    finally:
        if session is None:
            db.close()


# ------------------------------------------------------------
# 3. Geocoding helper
# ------------------------------------------------------------
# Geocoding means turning a text address like "Nottingham city centre"
# into a latitude/longitude pair so we can compare it with bus stops.
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


# ------------------------------------------------------------
# 4. Time helpers
# ------------------------------------------------------------
# We need the local UK time because bus timetables are based on local time.
def uk_local_now() -> datetime:
    return datetime.now(ZoneInfo("Europe/London"))


# GTFS times are stored in a string format like "07:45:00".
# This helper converts that into seconds since midnight so it is easier to compare.
def parse_gtfs_time(value: str) -> int:
    """Convert a GTFS time string like 07:45:00 into seconds since midnight."""
    hour_str, minute_str, second_str = value.split(":")
    return int(hour_str) * 3600 + int(minute_str) * 60 + int(second_str)


# ------------------------------------------------------------
# 5. Database checks
# ------------------------------------------------------------
# This checks whether a GTFS table exists in the SQLite database.
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


# ------------------------------------------------------------
# 6. Finding the next buses from a stop
# ------------------------------------------------------------
# Once we know the nearest stop, we look at the timetable for that stop.
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
            # Some GTFS rows may be blank or malformed; skip them.
            continue

        # Only keep departures after the current time and within the requested window.
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


# ------------------------------------------------------------
# 7. All-in-one nearby-bus lookup
# ------------------------------------------------------------
# This combines the stop-finding logic and timetable logic.
def next_bus_times_for_location(
    latitude: float,
    longitude: float,
    now: Optional[datetime] = None,
    limit: int = 4,
    within_minutes: int = 60,
) -> Dict[str, Any]:
    """Return the four nearest stops and their upcoming departures within the next hour."""
    # Get the closest stops first.
    nearest_stops = find_nearest_stops(latitude, longitude, limit=limit)
    result = {
        "location": {"latitude": latitude, "longitude": longitude},
        "search_time": (now or uk_local_now()).isoformat(),
        "nearest_stops": nearest_stops,
        "next_buses": [],
        "status": "ok",
    }

    # If GTFS stop_times data is missing, say so clearly instead of crashing.
    if not database_has_table("stop_times"):
        result["status"] = "unavailable"
        result["message"] = (
            "The database contains stop locations but not the GTFS stop_times schedule. "
            "Add the GTFS stop_times table or import the timetable feed to enable next-bus lookups."
        )
        return result

    # For each nearest stop, fetch the upcoming buses.
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


# ------------------------------------------------------------
# 8. Journey planning
# ------------------------------------------------------------
# This is a best-effort planner. It does not yet do full route logic.
# Instead, it finds the nearest stop to the origin and destination, then checks
# whether timetable data exists.
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
    # If the user supplied an address instead of coordinates, geocode it first.
    if origin_address and (origin_latitude is None or origin_longitude is None):
        geocoded_origin = geocode_address(origin_address)
        origin_latitude = geocoded_origin["latitude"]
        origin_longitude = geocoded_origin["longitude"]

    if destination_address and (destination_latitude is None or destination_longitude is None):
        geocoded_destination = geocode_address(destination_address)
        destination_latitude = geocoded_destination["latitude"]
        destination_longitude = geocoded_destination["longitude"]

    # If we still do not have both origin and destination points, stop early.
    if origin_latitude is None or origin_longitude is None or destination_latitude is None or destination_longitude is None:
        raise ValueError("Origin and destination coordinates or addresses are required.")

    # Find the nearest stop to where the user starts and where they want to end.
    origin_stop = find_nearest_stops(origin_latitude, origin_longitude, limit=1)[0]
    destination_stop = find_nearest_stops(destination_latitude, destination_longitude, limit=1)[0]

    # A true route planner needs more than coordinates.
    # It needs trip-to-stop sequencing and route matching from GTFS data.
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
