from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class Location(BaseModel):
    latitude: float
    longitude: float

class Place(BaseModel):
    place_id: int
    name: str

class Record(BaseModel):
    record_id: UUID
    place: Place
    sport: str
    start_time: datetime
    end_time: datetime
    capacity: int
    status: str
    organizer_id: UUID
