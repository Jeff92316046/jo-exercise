from fastapi import APIRouter

from api.record_public import router as record_public_router
from api.record import router as record_router
from api.list import router as list_router
from api.compute import router as compute_router

api_router = APIRouter()

api_router.include_router(record_public_router)
api_router.include_router(record_router)
api_router.include_router(list_router)
api_router.include_router(compute_router)
