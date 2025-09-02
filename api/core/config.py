from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    ALLOWED_ORIGINS: str
    MONGO_ATLAS_CONNECTION_URI: str
    BROWSER_POOL_SIZE: int = 3
    RATE_LIMIT_REQUESTS: int = 10
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str

    class Config:
        env_file = ".env"

settings = Settings()