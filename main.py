from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from api.routers.agent import router as agent_router
from contextlib import asynccontextmanager
from api.core.config import settings
from api.utils.cold_start import wait_for_browser
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio, time, requests
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
    # 'https://playwright-browser-instance-1.onrender.com/'
]

@app.get("/")
async def root():
    results = {}
    for url in BROWSER_INSTANCE_URLS:
        print(f"Waking up {url}...")
        for _ in range(5): 
            try:
                resp = requests.get(url, timeout=300.0)
                if resp.text.strip() == "Running":
                    results[url] = "Running"
                    break
                else:
                    results[url] = f"Not running. Response: {resp.text}"
            except Exception as e:
                results[url] = f"Error: {str(e)}"
            
            time.sleep(5)
        else:
            results[url] = "Failed after retries"
    return {"status": "ok", "browser_instances": results}
    # try:
    #     print("Waking up browser instances...")
    #     tasks = [wait_for_browser(url) for url in BROWSER_INSTANCE_URLS]
    #     results_list = await asyncio.gather(*tasks)
    #     results = dict(zip(BROWSER_INSTANCE_URLS, results_list))
    #     print("Browser instances woken up.")
    #     return {"status": "ok", "browser_instances": results}
    # except Exception as e:
    #     print(f"Error waking up browser instances: {e}")
    #     return {"status": "error", "message": str(e)}

    # results = {}

    # with ThreadPoolExecutor(max_workers=len(BROWSER_INSTANCE_URLS)) as executor:
    #     future_to_url = {executor.submit(wait_for_browser, url): url for url in BROWSER_INSTANCE_URLS}
    #     for future in as_completed(future_to_url):
    #         url = future_to_url[future]
    #         print(f"Waking up the browser instance at {url}...")
    #         results[url] = future.result()
    
    # return { "status": "ok", "browser_instances": results }
