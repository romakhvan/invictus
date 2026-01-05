# Настройка UI тестирования

## Структура проекта

Проект поддерживает три типа тестов:

1. **Backend тесты** (`tests/backend/`) - тестирование MongoDB
2. **Web тесты** (`tests/web/`) - тестирование веб-сайта с Playwright
3. **Mobile тесты** (`tests/mobile/`) - тестирование мобильного приложения с Appium

## Установка зависимостей

```bash
# Установка Python зависимостей
pip install -r requirements.txt

# Установка браузеров для Playwright
playwright install
```

## Настройка конфигурации

### Web тесты (Playwright)

Отредактируйте `src/config/app_config.py`:

```python
WEB_BASE_URL = "https://your-web-app.com"
WEB_TIMEOUT = 30000
```

### Mobile тесты (Appium)

1. Убедитесь, что Appium сервер запущен:
```bash
appium
```

2. Отредактируйте `src/config/app_config.py`:
```python
MOBILE_APP_PATH = "/path/to/your/app.apk"  # или bundle_id для iOS
MOBILE_PLATFORM = "Android"  # или "iOS"
MOBILE_DEVICE_NAME = "emulator-5554"
MOBILE_PLATFORM_VERSION = "13.0"
MOBILE_APPIUM_SERVER = "http://localhost:4723"
```

## Запуск тестов

### Все тесты
```bash
pytest
```

### Только Backend тесты
```bash
pytest -m backend
```

### Только Web тесты
```bash
pytest -m web
```

### Только Mobile тесты
```bash
pytest -m mobile
```

### Комбинации маркеров
```bash
# Smoke тесты для веба
pytest -m "web and smoke"

# Regression тесты для мобильного
pytest -m "mobile and regression"
```

## Структура Page Objects

### Web (Playwright)

```python
from src.pages.web.base_web_page import BaseWebPage
from playwright.sync_api import Page

class MyWebPage(BaseWebPage):
    BUTTON_SELECTOR = "button.submit"
    
    def __init__(self, page: Page):
        super().__init__(page)
    
    def click_button(self):
        self.click(self.BUTTON_SELECTOR)
```

### Mobile (Appium)

```python
from src.pages.mobile.base_mobile_page import BaseMobilePage
from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

class MyMobilePage(BaseMobilePage):
    BUTTON_SELECTOR = (AppiumBy.ID, "com.app:id/button")
    
    def __init__(self, driver: Remote):
        super().__init__(driver)
    
    def click_button(self):
        self.click(*self.BUTTON_SELECTOR)
```

## Использование в тестах

### Web тест

```python
import pytest
from playwright.sync_api import Page
from src.pages.web.example_web_page import ExampleWebPage

@pytest.mark.web
def test_login(web_page: Page):
    page = ExampleWebPage(web_page)
    page.login("username", "password")
    assert page.get_current_url() == "https://app.com/dashboard"
```

### Mobile тест

```python
import pytest
from appium.webdriver import Remote
from src.pages.mobile.example_mobile_page import ExampleMobilePage

@pytest.mark.mobile
def test_login(mobile_driver: Remote):
    page = ExampleMobilePage(mobile_driver)
    page.login("username", "password")
    assert page.is_visible(*page.DASHBOARD_ELEMENT)
```

## Интеграция с Backend

Вы можете комбинировать UI тесты с проверками в MongoDB:

```python
import pytest
from src.pages.web.example_web_page import ExampleWebPage

@pytest.mark.web
def test_user_creation_creates_db_record(web_page, db):
    # UI действие
    page = ExampleWebPage(web_page)
    page.create_user("test@example.com")
    
    # Проверка в БД
    from src.repositories.users_repository import find_user_by_email
    user = find_user_by_email(db, "test@example.com")
    assert user is not None
```

