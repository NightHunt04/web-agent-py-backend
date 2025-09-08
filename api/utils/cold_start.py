import asyncio, httpx

async def wait_for_browser(url: str, retries: int = 10, delay: int = 5):
    async with httpx.AsyncClient(timeout=10.0) as client:
        for attempt in range(retries):
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and resp.text.strip() == "Running":
                    return "Running"
            except Exception:
                pass
            await asyncio.sleep(delay)
    return "Failed to start"