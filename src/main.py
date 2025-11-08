from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.router import api_router
from db.session import init_db_pool
from msg.msg_log_server import mqtt_init

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db_pool()
    global mqtt_client
    print("🚀 FastAPI starting, initializing MQTT...")
    mqtt_client = mqtt_init()
    yield
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()


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
