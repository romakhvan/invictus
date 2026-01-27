import pytest
import pymongo
import pytest_check as check
import allure
from src.validators.push_notifications.welcome_push_validator import check_welcome_push
from src.config.db_config import MONGO_URI_PROD, MONGO_URI_STAGE, DB_NAME


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


@allure.feature('Push Notifications')
@allure.story('Welcome Push')
@allure.title('Проверка пуша "Добро пожаловать"')
@allure.description('Проверяет пуш для новых пользователей без входов в клуб неделю после покупки')
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag('backend', 'notifications', 'mongodb')
@allure.link(name='MongoDB Query', url='mongodb://localhost:27017')
def test_welcome_push_with_new_subscriptions(db):
    """
    Проверяет пуш 'Добро пожаловать':
    - Заголовок и текст соответствуют шаблону;
    - Пользователи действительно купили абонемент в этот день;
    - Количество получателей совпадает с количеством покупок.
    """
    with allure.step("Запуск теста Welcome Push"):
        print("\n=== TEST: Welcome Push ===")
        allure.attach(
            "ENVIRONMENT: PROD\nTEST: Welcome Push Validation",
            name="Test Configuration",
            attachment_type=allure.attachment_type.TEXT
        )
    
    with allure.step("Выполнение проверки Welcome Push"):
        result = check_welcome_push(db)
        
        # Если тест упал, прикрепляем рекомендации
        if not result:
            allure.attach(
                "1. Проверьте ID пользователей в разделе 'Missing IDs' и 'Extra IDs'\n"
                "2. Найдите их в MongoDB: db.users.find({_id: ObjectId('...')})\n"
                "3. Проверьте подписки: db.usersubscriptions.find({user: ObjectId('...')})\n"
                "4. Проверьте входы: db.accesscontrols.find({user: ObjectId('...')})",
                name="How to Debug",
                attachment_type=allure.attachment_type.TEXT
            )
        
        assert result, "Push 'Добро пожаловать' не прошёл проверку"
