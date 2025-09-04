from ..db.redis import redis
from ..core.config import settings
from fastapi import Request, Header

def check_traffic(request: Request):
    running_tasks = redis.smembers("running-tasks")

    if running_tasks is None:
        return True

    if len(running_tasks) >= settings.MAX_CONCURRENT_TASKS:
        return False

    if request.headers.get("X-Forwarded-For") in running_tasks:
        return False
    return True