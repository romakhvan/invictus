"""
Пример реального теста для страницы входа.
Замените селекторы и логику на реальные для вашего приложения.
"""

import pytest
from playwright.sync_api import Page
from src.pages.web.example_web_page import ExampleWebPage
from src.utils.test_data import TestUsers
from src.utils.ui_helpers import take_screenshot, log_action


@pytest.mark.web
@pytest.mark.smoke
def test_login_successful(web_page: Page):
    """
    Тест успешного входа в систему.
    
    ВАЖНО: Замените ExampleWebPage на реальный Page Object вашего приложения
    и обновите селекторы в src/pages/web/example_web_page.py
    """
    log_action("Начало теста: успешный вход")
    
    try:
        # Инициализация Page Object
        login_page = ExampleWebPage(web_page)
        
        # Проверка загрузки страницы
        assert login_page.is_loaded(), "Страница входа не загрузилась"
        log_action("Страница входа загружена")
        
        # Получение тестовых данных
        user = TestUsers.get_user("regular")
        log_action("Вход пользователя", f"username: {user['username']}")
        
        # Выполнение входа
        login_page.login(user["username"], user["password"])
        log_action("Форма входа отправлена")
        
        # Проверка успешного входа (замените на реальную проверку)
        # Например: проверка URL или наличие элемента на странице после входа
        # assert "dashboard" in login_page.get_current_url()
        
    except Exception as e:
        take_screenshot(web_page, "login_error.png")
        log_action("Ошибка при входе", str(e))
        raise


@pytest.mark.web
def test_login_invalid_credentials(web_page: Page):
    """
    Тест входа с неверными учетными данными.
    """
    log_action("Начало теста: вход с неверными данными")
    
    login_page = ExampleWebPage(web_page)
    assert login_page.is_loaded()
    
    # Попытка входа с неверными данными
    login_page.login("invalid_user", "wrong_password")
    
    # Проверка сообщения об ошибке (замените на реальную проверку)
    # error_message = login_page.get_error_message()
    # assert "неверные" in error_message.lower() or "invalid" in error_message.lower()


@pytest.mark.web
@pytest.mark.smoke
def test_page_loads(web_page: Page):
    """
    Простой тест загрузки страницы.
    """
    log_action("Проверка загрузки страницы")
    
    login_page = ExampleWebPage(web_page)
    assert login_page.is_loaded(), "Страница не загрузилась"
    log_action("Страница успешно загружена")

