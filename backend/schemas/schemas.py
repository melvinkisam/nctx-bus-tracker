from pydantic import BaseModel

# Define the base model format
class StopBase(BaseModel):
    stop_id: str
    stop_name: str
    latitude: float
    longitude: float

# Define a model to retrieve stop data including the id
class StopRead(StopBase):
    id: int
    
    class Config:
        orm_mode = True