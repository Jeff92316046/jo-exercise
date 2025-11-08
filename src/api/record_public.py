from typing import Optional
from datetime import datetime
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from db import db_utils
from schemas.base import Record, Place
from schemas.response import RecordResponse

router = APIRouter(
    prefix="/record",
    tags=["record"],
)

@router.get("/all")
async def get_all_records(
        place: Optional[str] = None,
        sport: Optional[str] = None,
        start_time: Optional[datetime] = None,
    ) -> RecordResponse.GetAllRecordsResponseModel:

    if place:
        find = False
        for center in await db_utils.get_centers():
            if center.get("name") == place:
                find = True
                break
        if not find:
            raise HTTPException(status_code=400, detail="Invalid place ID")

    if sport and sport not in await db_utils.get_sports():
            raise HTTPException(status_code=400, detail="Invalid sport type")

    all_records = await db_utils.get_all_active_events()
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
        ) for record in all_records if (
            (place is None or record.get("center_name") == place) and
            (sport is None or record.get("sport") == sport) and
            (start_time is None or record.get("start_time") >= start_time)
        )
    ]
    return RecordResponse.GetAllRecordsResponseModel(records=records_list)
