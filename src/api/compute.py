from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from db import db_utils
from schemas.base import Place
from schemas.request import ComputeRequest

router = APIRouter(
    prefix="/compute",
    tags=["compute"],
)

@router.post("/")
async def compute_closest_place(
        body: ComputeRequest.ClosestPlaceRequestModel,
    ) -> Place:

    if body.sport and body.sport not in await db_utils.get_sports():
        raise HTTPException(status_code=400, detail="Invalid sport type")

    allowed_pairs = await db_utils.get_allowed_pairs_grouped()

    def check_place_allowed(place: dict, sport: str) -> bool:
        if sport is None:
            return True

        for pair in allowed_pairs:
            if pair.get("sport") == sport:
                return place.get("name") in pair.get("centers", [])

        return False

    place_list = await db_utils.get_centers()
    distance_list = [
        (
            place,
            (
                (place.get("latitude") - body.user_location.latitude) ** 2 + \
                (place.get("longitude") - body.user_location.longitude) ** 2
            ) ** 0.5,
        )
        for place in place_list
        if check_place_allowed(place, body.sport)
    ]

    # print(distance_list)

    if not distance_list:
        raise HTTPException(status_code=404, detail="No available place found")

    closest_place = min(distance_list, key=lambda x: x[1])[0]
    return Place(
        place_id=closest_place.get("id"),
        name=closest_place.get("name"),
    )
