"""
Тесты страницы авторизации invictus.kz/auth
"""

import pytest
from playwright.sync_api import Page
from src.pages.web.auth_page import AuthPage


@pytest.mark.web
@pytest.mark.smoke
def test_auth_page_loads(web_page: Page):
    """Страница авторизации загружается с полем ввода телефона."""
    page = AuthPage(web_page)
    page.open()
    assert page.is_loaded(), "Страница авторизации не загрузилась"


@pytest.mark.web
@pytest.mark.smoke
def test_auth_page_heading(web_page: Page):
    """Заголовок страницы авторизации содержит текст о вводе телефона."""
    page = AuthPage(web_page)
    page.open()
    heading = page.get_heading_text()
    assert "Телефон" in heading, f"Неожиданный заголовок: {heading}"


@pytest.mark.web
def test_country_code_is_plus_seven(web_page: Page):
    """Код страны по умолчанию — +7 (Казахстан)."""
    page = AuthPage(web_page)
    page.open()
    code = page.get_country_code()
    assert "+7" in code, f"Неожиданный код страны: {code}"


@pytest.mark.web
def test_submit_button_disabled_when_empty(web_page: Page):
    """Кнопка 'Келесі' недоступна при пустом поле телефона."""
    page = AuthPage(web_page)
    page.open()
    assert not page.is_submit_enabled(), "Кнопка отправки должна быть недоступна при пустом поле"


@pytest.mark.web
def test_submit_button_enabled_after_phone_input(web_page: Page):
    """Кнопка 'Келесі' становится активной после ввода номера телефона."""
    page = AuthPage(web_page)
    page.open()
    page.enter_phone("7771234567")
    assert page.is_submit_enabled(), "Кнопка отправки должна быть активна после ввода номера"


@pytest.mark.web
def test_back_button_present(web_page: Page):
    """Кнопка 'Артқа' (назад) присутствует на странице авторизации."""
    page = AuthPage(web_page)
    page.open()
    assert page.is_visible(page.BACK_BUTTON), "Кнопка 'Артқа' не найдена"


@pytest.mark.web
def test_back_button_navigates_to_home(web_page: Page):
    """Кнопка 'Артқа' возвращает на главную страницу."""
    page = AuthPage(web_page)
    page.open()
    page.go_back()
    page.page.wait_for_load_state("networkidle")
    current_url = page.get_current_url()
    assert current_url.rstrip("/") in ("https://invictus.kz", "https://invictus.kz/"), \
        f"После нажатия 'Артқа' ожидался переход на главную, получен URL: {current_url}"
