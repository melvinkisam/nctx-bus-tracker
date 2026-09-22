from sqlalchemy import Column, Integer, String, Float
from database.database import Base


class Stop(Base):
    __tablename__ = "bus_stops"
    id = Column(Integer, primary_key=True, index=True)
    stop_id = Column(String, index=True)
    stop_name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)


class Route(Base):
    __tablename__ = "routes"
    route_id = Column(String, primary_key=True, index=True)
    agency_id = Column(String, index=True)
    route_short_name = Column(String, index=True)
    route_long_name = Column(String, index=True)
    route_desc = Column(String, nullable=True)
    route_type = Column(Integer, nullable=True)
    route_url = Column(String, nullable=True)
    route_color = Column(String, nullable=True)
    route_text_color = Column(String, nullable=True)


class ServiceCalendar(Base):
    __tablename__ = "calendar"
    service_id = Column(String, primary_key=True, index=True)
    monday = Column(Integer, default=0)
    tuesday = Column(Integer, default=0)
    wednesday = Column(Integer, default=0)
    thursday = Column(Integer, default=0)
    friday = Column(Integer, default=0)
    saturday = Column(Integer, default=0)
    sunday = Column(Integer, default=0)
    start_date = Column(String)
    end_date = Column(String)


class Trip(Base):
    __tablename__ = "trips"
    trip_id = Column(String, primary_key=True, index=True)
    route_id = Column(String, index=True)
    service_id = Column(String, index=True)
    trip_headsign = Column(String, nullable=True)
    trip_short_name = Column(String, nullable=True)
    direction_id = Column(Integer, nullable=True)
    block_id = Column(String, nullable=True)
    shape_id = Column(String, nullable=True)
    wheelchair_accessible = Column(Integer, nullable=True)
    bikes_allowed = Column(Integer, nullable=True)


class StopTime(Base):
    __tablename__ = "stop_times"
    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(String, index=True)
    arrival_time = Column(String, nullable=True)
    departure_time = Column(String, nullable=True)
    stop_id = Column(String, index=True)
    stop_sequence = Column(Integer, nullable=True)
    stop_headsign = Column(String, nullable=True)
    pickup_type = Column(Integer, nullable=True)
    drop_off_type = Column(Integer, nullable=True)
    timepoint = Column(Integer, nullable=True)


class Shape(Base):
    __tablename__ = "shapes"
    id = Column(Integer, primary_key=True, index=True)
    shape_id = Column(String, index=True)
    shape_pt_lat = Column(Float)
    shape_pt_lon = Column(Float)
    shape_pt_sequence = Column(Integer)
    shape_dist_traveled = Column(Float, nullable=True)