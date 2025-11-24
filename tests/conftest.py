import pytest
import pymongo
from src.config.db_config import MONGO_URI, DB_NAME

@pytest.fixture(scope="session")
def db():
    print("\n🔌 Connecting to MongoDB...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    yield db
    print("\n🧹 Closing Mongo connection.")
    client.close()
