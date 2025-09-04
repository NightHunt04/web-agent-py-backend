from ..db.redis import redis

async def add_running_task(task_id: str):
    try:
        await redis.sadd("running-tasks", task_id)
    except Exception as e:
        print(f"Error adding task to running-tasks: {e}")

async def remove_running_task(task_id: str):
    try:
        await redis.srem("running-tasks", task_id)
    except Exception as e:
        print(f"Error removing task from running-tasks: {e}")
