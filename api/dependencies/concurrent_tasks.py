from ..db.redis import redis
from ..core.config import settings

def check_traffic():
    running_tasks = redis.smembers("running-tasks")

    if len(running_tasks) >= settings.MAX_CONCURRENT_TASKS:
        return False
    return True