from uuid import UUID
from datetime import datetime

from pydantic import BaseModel

from schemas.base import Location

class ComputeRequest(BaseModel):
    class ClosestPlaceRequestModel(BaseModel):
        user_location: Location
        sport: str

class RecordRequest(BaseModel):
    class CreateRecordRequestModel(BaseModel):
        user_id: UUID
        place: str
        sport: str
        start_time: datetime
        end_time: datetime
