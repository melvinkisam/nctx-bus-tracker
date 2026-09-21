from pydantic import BaseModel, ConfigDict


class StopBase(BaseModel):
    stop_id: str
    stop_name: str
    latitude: float
    longitude: float


class StopRead(StopBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class RouteSchema(BaseModel):
    route_id: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    agency_id: str | None = None
    model_config = ConfigDict(from_attributes=True)


class TripSchema(BaseModel):
    trip_id: str
    route_id: str | None = None
    service_id: str | None = None
    trip_headsign: str | None = None
    direction_id: int | None = None
    model_config = ConfigDict(from_attributes=True)


class StopTimeSchema(BaseModel):
    trip_id: str
    stop_id: str
    arrival_time: str | None = None
    departure_time: str | None = None
    stop_sequence: int | None = None
    model_config = ConfigDict(from_attributes=True)


class CalendarSchema(BaseModel):
    service_id: str
    monday: int | None = None
    tuesday: int | None = None
    wednesday: int | None = None
    thursday: int | None = None
    friday: int | None = None
    saturday: int | None = None
    sunday: int | None = None
    start_date: str | None = None
    end_date: str | None = None
    model_config = ConfigDict(from_attributes=True)