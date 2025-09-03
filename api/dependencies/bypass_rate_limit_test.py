from fastapi import Request
from api.core.config import settings
from fastapi_limiter.depends import RateLimiter

def rate_limiter_bypass(request: Request):
    if request.headers.get("X-Bypass-RateLimit-key") == settings.RATE_LIMIT_BYPASS_KEY:
        return
        
    return RateLimiter(
        times = settings.RATE_LIMIT_AGENT_REQUESTS,
        seconds = settings.RATE_LIMIT_AGENT_REQUESTS_TIME
    )(request)