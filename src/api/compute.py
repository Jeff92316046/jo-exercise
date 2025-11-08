from fastapi import APIRouter

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
    
    closest_place = None
    return closest_place
