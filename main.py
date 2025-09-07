from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from api.routers.agent import router as agent_router
from contextlib import asynccontextmanager
from api.core.config import settings
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from dotenv import load_dotenv
load_dotenv()

@asynccontextmanager
async def lifespan(_app: FastAPI):
    redis_connection = redis.from_url(settings.UPSTASH_REDIS_TCP_URL)
    await FastAPILimiter.init(redis_connection)
    print("Redis connected for rate limiter")
    
    yield
    
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
    dependencies = [Depends(RateLimiter(
        times = settings.RATE_LIMIT_AGENT_REQUESTS, 
        seconds = settings.RATE_LIMIT_AGENT_REQUESTS_TIME
    ))]
)

BROWSER_INSTANCE_URLS = [
    'https://playwright-browser-instance.onrender.com/',
    'https://playwright-browser-instance-1.onrender.com/'
]

@app.get("/")
def root():
    results = {}

    with ThreadPoolExecutor(max_workers=len(BROWSER_INSTANCE_URLS)) as executor:
        future_to_url = {executor.submit(requests.get, url, timeout=200.0): url for url in BROWSER_INSTANCE_URLS}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            print(f"Waking up the browser instance at {url}...")
            try:
                resp = future.result()
                if resp.text.strip() == "Running":
                    results[url] = "Running"
                else:
                    results[url] = f"Not running. Response: {resp.text}"
            except Exception as e:
                results[url] = f"Error: {str(e)}"

    return { "status": "ok", "browser_instances": results }
