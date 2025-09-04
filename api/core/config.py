from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALLOWED_ORIGINS: str
    MONGO_ATLAS_CONNECTION_URI: str
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str
    UPSTASH_REDIS_TCP_URL: str
    RATE_LIMIT_BYPASS_KEY: str

    BROWSER_POOL_SIZE: int = 3
    MAX_CONCURRENT_TASKS: int = 5
    RATE_LIMIT_AGENT_REQUESTS: int = 1
    RATE_LIMIT_AGENT_REQUESTS_TIME: int = 60

    class Config:
        env_file = ".env"

settings = Settings()