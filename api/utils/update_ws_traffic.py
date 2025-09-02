from ..core.config import settings
from ..db.redis import redis

def update_ws_traffic(ws_endpoint: str, increment: bool = False, decrement: bool = False) -> bool:
    try:
        ws_map = redis.json.get("ws-endpoints", "$")
        ws_map = ws_map[0]

        MAX_CONNECTION_PER_BROWSER = settings.BROWSER_POOL_SIZE

        for _key, val in ws_map.items():
            if val['ws_endpoint'] == ws_endpoint and (increment and val['traffic'] + 1 <= MAX_CONNECTION_PER_BROWSER or decrement and val['traffic'] - 1 >= 0):
                if increment:
                    val['traffic'] += 1
                else:
                    val['traffic'] -= 1
                redis.json.set("ws-endpoints", f"$.{_key}", val)
                return True
        
        return False

    except Exception as e:
        print(f"Error updating ws-endpoints in Redis: {e}")
        return False
    