from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.router import api_router
from db.db_utils import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="jo exercise",
    version="0.1.0",
    description="A robust backend API using FastAPI.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Welcome to the jo-exercise!"}
