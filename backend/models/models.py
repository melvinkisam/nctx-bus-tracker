from sqlalchemy import Column, Integer, String, Float
from database.database import Base

# Initializing a table named 'stores' in the db, inheriting from Base
class Stop(Base):
    __tablename__ = "bus_stops"
    id = Column(Integer, primary_key=True, index=True)
    stop_id = Column(String, index=True)
    stop_name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)