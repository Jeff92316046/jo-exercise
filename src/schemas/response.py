from uuid import UUID
from pydantic import BaseModel

from schemas.base import Place, Record

class ComputeResponse(BaseModel):
    class ClosestPlaceResponseModel(BaseModel):
        place: str

class ListResponse(BaseModel):
    class SportsListResponseModel(BaseModel):
        sports: list[str]

    class PlacesListResponseModel(BaseModel):
        places: list[Place] | list[None]

class RecordResponse(BaseModel):
    class GetUserRecordsResponseModel(BaseModel):
        records: list[Record] | list[None]

    class GetAllRecordsResponseModel(BaseModel):
        records: list[Record] | list[None]

    class CreateRecordResponseModel(BaseModel):
        record_id: UUID
