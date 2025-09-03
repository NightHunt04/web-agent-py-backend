from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from api.dependencies.bypass_rate_limit_test import rate_limiter_bypass
from api.routers.agent import router as agent_router
from contextlib import asynccontextmanager
from api.core.config import settings
from api.db.mongo import db
import redis.asyncio as redis
from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.connect()
    print("Mongo DB connected")
    redis_connection = redis.from_url(settings.UPSTASH_REDIS_TCP_URL)
    await FastAPILimiter.init(redis_connection)
    print("Redis connected for rate limiter")
    
    yield
    
    await db.disconnect()
    print("Mongo DB disconnected")
    await redis_connection.close()
    print("Redis disconnected")
    await FastAPILimiter.close()
    print("Rate limiter disconnected")

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

app.include_router(
    agent_router, 
    dependencies=[Depends(rate_limiter_bypass)]
    # dependencies = [Depends(RateLimiter(
    #     times = settings.RATE_LIMIT_AGENT_REQUESTS, 
    #     seconds = settings.RATE_LIMIT_AGENT_REQUESTS_TIME
    # ))]
)

@app.get("/")
def root():
    return { "status": "ok" }
