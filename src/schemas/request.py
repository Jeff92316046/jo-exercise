from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from schemas.base import Location

class ComputeRequest(BaseModel):
    class ClosestPlaceRequestModel(BaseModel):
        user_location: Location
        sport: Optional[str] = None

class RecordRequest(BaseModel):
    class CreateRecordRequestModel(BaseModel):
        user_id: UUID
        place_id: int
        sport: str
        start_time: datetime
        end_time: datetime
        capacity: int
