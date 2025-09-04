from ..db.redis import redis

def add_session(ip: str):
    try:
        redis.sadd("running-sessions", ip)
    except Exception as e:
        print(f"Error adding ip to running-sessions: {e}")

def remove_session(ip: str):
    try:
        redis.srem("running-sessions", ip)
    except Exception as e:
        print(f"Error removing ip from running-sessions: {e}")