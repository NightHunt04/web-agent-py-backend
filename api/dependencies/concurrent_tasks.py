from ..db.redis import redis
from ..core.config import settings
from fastapi import Request, Header

def check_traffic(request: Request):
    running_sessions = redis.smembers("running-sessions")

    if running_sessions is None:
        return True

    if len(running_sessions) >= settings.MAX_CONCURRENT_TASKS:
        return False

    if (request.headers.get("X-Forwarded-For") or request.client.host) in running_sessions:
        return False
    return True