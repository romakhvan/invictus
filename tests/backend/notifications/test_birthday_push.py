import pytest
import pymongo
import pytest_check as check
from src.validators.push_notifications.birthday_push_validator import check_birthday_push
from src.config.db_config import MONGO_URI_PROD, MONGO_URI_STAGE, DB_NAME
import allure


# ========== КОНФИГУРАЦИЯ ОКРУЖЕНИЯ ==========
# Выберите окружение базы данных: 'prod' или 'stage'
ENVIRONMENT = 'prod'  # 'prod' или 'stage'
# ============================================

@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB.
    Окружение определяется переменной ENVIRONMENT.
    """
    mongo_uri = MONGO_URI_PROD if ENVIRONMENT == 'prod' else MONGO_URI_STAGE
    env_name = ENVIRONMENT.upper()
    
    print(f"\nConnecting to MongoDB {env_name}...")
    client = pymongo.MongoClient(mongo_uri)
    db = client[DB_NAME]
    yield db
    print(f"\nClosing Mongo {env_name} connection.")
    client.close()


@allure.feature('Notifications')
@allure.story('Birthday Push')
@allure.title('Проверка пуша "С днём рождения"')
@allure.description('Проверяет, что пуш с поздравлением отправлен только пользователям с активной подпиской')
@allure.severity(allure.severity_level.MINOR)
@allure.tag('backend', 'notifications', 'mongodb')
@allure.link(name='MongoDB Query', url='mongodb://localhost:27017')
def test_birthday_push_with_active_users(db):
    """
    Тест проверяет, что пуш с поздравлением 'С днём рождения'
    отправлен только пользователям с активной подпиской.
    """
    with allure.step("Запуск теста Birthday Push"):
        print("=== TEST: Birthday Push ===")
        allure.attach(
            "ENVIRONMENT: PROD\nTEST: Birthday Push Validation",
            name="Test Configuration",
            attachment_type=allure.attachment_type.TEXT
        )
    
    with allure.step("Выполнение проверки Birthday Push"):
        result = check_birthday_push(db)
        
        # Если тест упал, прикрепляем рекомендации
        if not result:
            allure.attach(
                "1. Проверьте ID пользователей в разделе 'Missing IDs'\n"
                "2. Найдите их в MongoDB: db.users.find({_id: ObjectId('...')})\n"
                "3. Проверьте их подписки: db.usersubscriptions.find({user: ObjectId('...')})\n"
                "4. Проверьте birthDate и isActive статус",
                name="How to Debug",
                attachment_type=allure.attachment_type.TEXT
            )