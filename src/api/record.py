from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends

from core.dependencies import auth
from schemas.request import RecordRequest
from schemas.response import RecordResponse

router = APIRouter(
    prefix="/record",
    tags=["record"],
)

@router.get("/{user_id}")
async def get_user_records(
        user_id: UUID,
        token: str = Depends(auth),
    ) -> RecordResponse.GetUserRecordsResponseModel:

    user_records = None
    return RecordResponse.GetUserRecordsResponseModel(records=user_records)

@router.get("/all")
async def get_all_records(
        place: Optional[str] = None,
        sport: Optional[str] = None,
        start_time: Optional[str] = None,
    ) -> RecordResponse.GetAllRecordsResponseModel:

    all_records = None
    return RecordResponse.GetAllRecordsResponseModel(records=all_records)

@router.post("/")
async def create_record(
        record_data: RecordRequest.CreateRecordRequestModel,
        token: str = Depends(auth),
    ) -> RecordResponse.CreateRecordResponseModel:

    new_record_id = UUID()

    return RecordResponse.CreateRecordResponseModel(record_id=new_record_id)

@router.post("/join/{record_id}")
async def join_records(
        record_id: UUID,
        user_id: UUID,
        token: str = Depends(auth),
    ) -> None:
    return

@router.delete("/leave/{record_id}")
async def leave_record(
        record_id: UUID,
        user_id: UUID,
        token: str = Depends(auth),
    ) -> None:
    return

@router.delete("/delete/{record_id}")
async def delete_record(
        record_id: UUID,
        token: str = Depends(auth),
    ) -> None:
    return
