"""
Пример интеграционного теста: UI действие + проверка в БД.

Этот тест демонстрирует, как можно комбинировать UI тесты
с проверками в MongoDB для полной валидации функциональности.
"""

import pytest
from playwright.sync_api import Page
from src.pages.web.example_web_page import ExampleWebPage
from src.utils.test_data import TestDataGenerator, TestUsers


@pytest.mark.web
def test_user_creation_creates_db_record(web_page: Page, db):
    """
    Пример: создание пользователя через UI и проверка записи в БД.
    
    ВАЖНО: Это пример. Замените на реальную логику вашего приложения.
    """
    # Генерация уникальных тестовых данных
    test_email = TestDataGenerator.random_email()
    test_username = f"test_{TestDataGenerator.random_string(6)}"
    
    # UI действие: создание пользователя
    # (замените на реальный Page Object и методы)
    # registration_page = RegistrationPage(web_page)
    # registration_page.create_user(test_username, test_email, "password123")
    
    # Проверка в БД (пример)
    # from src.repositories.users_repository import find_user_by_email
    # user = find_user_by_email(db, test_email)
    # assert user is not None, "Пользователь не создан в БД"
    # assert user["username"] == test_username
    # assert user["email"] == test_email
    
    pass


@pytest.mark.web
def test_data_sync_ui_to_db(web_page: Page, db):
    """
    Пример: изменение данных в UI и проверка синхронизации с БД.
    """
    # Вход в систему
    # login_page = ExampleWebPage(web_page)
    # user = TestUsers.get_user("regular")
    # login_page.login(user["username"], user["password"])
    
    # Изменение данных в UI
    # profile_page = ProfilePage(web_page)
    # new_name = f"Updated_{TestDataGenerator.random_string(5)}"
    # profile_page.update_name(new_name)
    
    # Проверка в БД
    # from src.repositories.users_repository import get_user_by_id
    # db_user = get_user_by_id(db, user_id)
    # assert db_user["name"] == new_name, "Данные не синхронизированы с БД"
    
    pass

