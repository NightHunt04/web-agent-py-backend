import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers.agent import router as agent_router
from contextlib import asynccontextmanager
from api.core.config import settings
from api.db.mongo import db
from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.connect()
    print("Database connected")
    yield
    print("Database disconnected")

app = FastAPI(
    title = "Dumb Web Agent - Browser Autonomous AI Agent Backend",
    version = "1.0.0",
    lifespan = lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.ALLOWED_ORIGINS.split(","),
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

app.include_router(agent_router)

@app.get("/")
def root():
    return { "status": "ok" }