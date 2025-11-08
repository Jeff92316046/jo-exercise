from uuid import UUID
from pydantic import BaseModel

class Location(BaseModel):
    latitude: float
    longitude: float

class Place(BaseModel):
    name: str
    location: Location

class Record(BaseModel):
    record_id: UUID
    place: Place
    sport: str
    start_time: str
    end_time: str
