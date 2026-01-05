"""
Конфигурация фикстур для mobile тестов.
Mobile тесты используют STAGE окружение.
"""

import pytest
import pymongo
from src.config.db_config import MONGO_URI_STAGE, DB_NAME


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB STAGE.
    Используется для всех mobile тестов.
    """
    print("\n🔌 Connecting to MongoDB STAGE...")
    client = pymongo.MongoClient(MONGO_URI_STAGE)
    db = client[DB_NAME]
    yield db
    print("\n🧹 Closing Mongo STAGE connection.")
    client.close()

