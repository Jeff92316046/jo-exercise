from typing import Optional
from fastapi import APIRouter

from schemas.response import ListResponse

router = APIRouter(
    prefix="/list",
    tags=["list"],
)

@router.get("/sports")
async def get_sports_list_by_place(
        place: Optional[str] = None,
    ) -> ListResponse.SportsListResponseModel:

    """目前用不到"""
    sport_list = None
    return ListResponse.SportsListResponseModel(sports=sport_list)

@router.get("/places")
async def get_places_list_by_sport(
        sport: Optional[str] = None,
    ) -> ListResponse.PlacesListResponseModel:

    place_list = None
    return ListResponse.PlacesListResponseModel(places=place_list)
