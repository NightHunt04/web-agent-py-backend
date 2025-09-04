from ..db.redis import redis

async def add_running_task(task_id: str):
    await redis.sadd("running-tasks", task_id)

async def remove_running_task(task_id: str):
    await redis.srem("running-tasks", task_id)
