import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.router import api_router
from db.db_utils import init_db
from msg.msg_log_server import mqtt_listener
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    global mqtt_task
    print("🚀 FastAPI starting, initializing MQTT...")
    mqtt_task = asyncio.create_task(mqtt_listener())
    yield

app = FastAPI(
    title="jo exercise",
    version="0.1.0",
    description="A robust backend API using FastAPI.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Welcome to the jo-exercise!"}
