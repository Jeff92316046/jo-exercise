from typing import Optional
from fastapi import APIRouter

from db import db_utils
from schemas.base import Place
from schemas.response import ListResponse

router = APIRouter(
    prefix="/list",
    tags=["list"],
)

@router.get("/sports")
async def get_sports_list_by_place(
        place: Optional[str] = None,
    ) -> ListResponse.SportsListResponseModel:

    sport_list = await db_utils.get_sports()
    return ListResponse.SportsListResponseModel(sports=sport_list)

@router.get("/places")
async def get_places_list_by_sport(
        sport: Optional[str] = None,
    ) -> ListResponse.PlacesListResponseModel:

    places_data_list = await db_utils.get_centers()
    allowed_pairs = await db_utils.get_allowed_pairs_grouped()

    place_set = set()
    for pair in allowed_pairs:
        if sport is None or pair.get("sport") == sport:
            for place in pair.get("centers", []):
                place_set.add(place)

    place_list = []
    for place in places_data_list:
        if place.get("name") in place_set:
            place_list.append(
                Place(
                    place_id=place.get("id"),
                    name=place.get("name"),
                )
            )
    return ListResponse.PlacesListResponseModel(places=place_list)
