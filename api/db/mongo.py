from pymongo import AsyncMongoClient, MongoClient
from api.core.config import settings

class MongoAtlas:
    def __init__(self) -> None:
        self.client: AsyncMongoClient | None = None

    async def connect(self):
        try:
            self.client = MongoClient(settings.MONGO_ATLAS_CONNECTION_URI)
        except Exception as e:
            print(f"MongoAtlas connection error: {e}")
            raise

    async def disconnect(self):
        try:
            self.client.close()
        except Exception as e:
            print(f"MongoAtlas disconnection error: {e}")
            raise

    @property
    def db(self):
        if not self.client:
            raise Exception("MongoAtlas client not initialized. Did you forget to call connect()?")
        return self.client["dumb-web"]

db = MongoAtlas()
