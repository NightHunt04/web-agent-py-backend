from upstash_redis import Redis
from ..core.config import settings

def load_ws_endpoint():
    try:
        redis = Redis(url=settings.UPSTASH_REDIS_REST_URL, token=settings.UPSTASH_REDIS_REST_TOKEN)

        ws_map = redis.json.get("ws-endpoints", "$")
        ws_map = ws_map[0]

        MAX_CONNECTION_PER_BROWSER = settings.BROWSER_POOL_SIZE
        lowest_traffic_ws = None
        lowest_traffic = None

        for _key, val in ws_map.items():
            if val['traffic'] + 1 > MAX_CONNECTION_PER_BROWSER:
                continue

            if lowest_traffic is None and lowest_traffic_ws is None:
                lowest_traffic = val['traffic']
                lowest_traffic_ws = val['ws_endpoint']
            elif val['traffic'] < lowest_traffic and val['traffic'] >= 0:
                lowest_traffic = val['traffic']
                lowest_traffic_ws = val['ws_endpoint']
        
        return lowest_traffic_ws

    except Exception as e:
        print(f"Error loading ws-endpoints from Redis: {e}")
        return None