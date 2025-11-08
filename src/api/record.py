from uuid import UUID
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from core import dependencies
from db import db_utils
from schemas.base import Record, Place
from schemas.request import RecordRequest
from schemas.response import RecordResponse

router = APIRouter(
    prefix="/record",
    tags=["record"],
)

@router.get("/get/{user_id}")
async def get_user_records(
        user_id: UUID,
        token: str = Depends(dependencies.auth),
    ) -> RecordResponse.GetUserRecordsResponseModel:

    user_records = await db_utils.get_user_active_events(user_uid=user_id)
    records_list = [
        Record(
            record_id=record.get("uid"),
            sport=record.get("sport"),
            place=Place(
                place_id=record.get("center_id"),
                name=record.get("center_name"),
            ),
            start_time=record.get("start_time"),
            end_time=record.get("end_time"),
            capacity=record.get("capacity"),
            status=record.get("status"),
            organizer_id=record.get("organizer_uid"),
        ) for record in user_records
    ]
    return RecordResponse.GetUserRecordsResponseModel(records=records_list)

@router.post("/")
async def create_record(
        record_data: RecordRequest.CreateRecordRequestModel,
        token: str = Depends(dependencies.auth),
    ) -> RecordResponse.CreateRecordResponseModel:

    # Validate place ID
    find = False
    for center in await db_utils.get_centers():
        if center.get("id") == record_data.place_id:
            find = True
            break
    if not find:
        raise HTTPException(status_code=400, detail="Invalid place ID")

    # Validate sport type
    if record_data.sport not in await db_utils.get_sports():
        raise HTTPException(status_code=400, detail="Invalid sport type")

    # Validate time
    if record_data.start_time >= record_data.end_time:
        raise HTTPException(status_code=400, detail="End time must be later than start time")

    # Validate capacity
    if record_data.capacity < 2:
        raise HTTPException(status_code=400, detail="Capacity must be at least 2")

    try:
        result = await db_utils.create_event(
            user_uid=record_data.user_id,
            sport=record_data.sport,
            center_id=record_data.place_id,
            start_time=record_data.start_time,
            end_time=record_data.end_time,
            capacity=record_data.capacity,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    new_record_id = result.get("uid")

    return RecordResponse.CreateRecordResponseModel(record_id=new_record_id)

@router.post("/join/{record_id}")
async def join_records(
        record_id: UUID,
        user_id: UUID,
        token: str = Depends(dependencies.auth),
    ) -> None:

    result = await db_utils.join_event(
        user_uid=user_id,
        event_uid=record_id,
    )
    message = result.get("status")
    match message:
        case "already_joined":
            raise HTTPException(status_code=400, detail="User has already joined the event")
        case "full":
            raise HTTPException(status_code=400, detail="Event is full")
        case "not_found":
            raise HTTPException(status_code=404, detail="Event not found")

@router.delete("/leave/{record_id}")
async def leave_record(
        record_id: UUID,
        user_id: UUID,
        token: str = Depends(dependencies.auth),
    ) -> None:

    result = await db_utils.leave_event(
        user_uid=user_id,
        event_uid=record_id,
    )
    if not result:
        raise HTTPException(status_code=400, detail="Failed to leave the event")

@router.delete("/delete/{record_id}")
async def delete_record(
        record_id: UUID,
        token: str = Depends(dependencies.auth),
    ) -> None:

    await db_utils.cancel_event(
        event_uid=record_id,
    )
