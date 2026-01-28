# 🚀 Быстрый старт: Следующие шаги

## ✅ Что уже готово

- Инфраструктура для Web и Mobile тестов
- Базовые драйверы и фикстуры
- Утилиты для тестовых данных
- Примеры тестов и Page Objects
- Документация

## 📋 Следующие шаги (по порядку)

### Шаг 1: Установка зависимостей (5 минут)

```bash
# Установить Python пакеты
pip install -r requirements.txt

# Установить браузеры для Playwright
playwright install chromium
```

### Шаг 2: Настройка конфигурации (5 минут)

Откройте `src/config/app_config.py` и укажите:

```python
# Для веб-тестов
WEB_BASE_URL = "https://ваш-сайт.com"  # ← Замените на реальный URL

# Для мобильных тестов (если нужны)
MOBILE_APP_PATH = "/путь/к/приложению.apk"  # ← Укажите путь к .apk/.ipa
MOBILE_DEVICE_NAME = "emulator-5554"  # ← Имя вашего эмулятора/устройства
```

### Шаг 3: Создать первый Page Object (15-30 минут)

1. Откройте `src/pages/web/example_web_page.py`
2. Замените примеры селекторов на реальные селекторы вашего приложения
3. Или создайте новый файл, например `src/pages/web/login_page.py`:

```python
from playwright.sync_api import Page
from src.pages.web.base_web_page import BaseWebPage

class LoginPage(BaseWebPage):
    # Замените на реальные селекторы вашего приложения
    USERNAME_INPUT = "input#username"  # или "input[name='username']"
    PASSWORD_INPUT = "input#password"
    LOGIN_BUTTON = "button.login"
    
    def __init__(self, page: Page):
        super().__init__(page)
    
    def is_loaded(self) -> bool:
        return self.is_visible(self.LOGIN_BUTTON)
    
    def login(self, username: str, password: str):
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
```

### Шаг 4: Написать первый тест (10 минут)

Откройте `tests/web/test_login_example.py` и:

1. Замените `ExampleWebPage` на ваш реальный Page Object
2. Обновите тестовые данные в `src/utils/test_data.py`
3. Запустите тест:

```bash
pytest tests/web/test_login_example.py -v -s
```

### Шаг 5: Проверить работу (5 минут)

```bash
# Запустить все web тесты
pytest -m web -v

# Запустить только smoke тесты
pytest -m "web and smoke" -v

# Запустить с выводом в консоль
pytest -m web -v -s
```

## 🎯 Что делать дальше?

1. **Создайте Page Objects для ключевых страниц:**
   - Главная страница
   - Профиль пользователя
   - Формы создания/редактирования
   - И т.д.

2. **Напишите тесты для критичных сценариев:**
   - Вход в систему
   - Создание пользователя
   - Основные бизнес-процессы

3. **Интегрируйте с Backend:**
   - Используйте существующие репозитории для проверки данных
   - Комбинируйте UI действия с проверками в MongoDB

4. **Организуйте тесты:**
   - Переместите существующие backend тесты в `tests/backend/`
   - Добавьте маркеры для категоризации

## 📚 Полезные ссылки

- [Полный план тестирования](docs/testing_roadmap.md)
- [Настройка UI тестирования](docs/ui_testing_setup.md)
- [Примеры Page Objects](src/pages/web/example_web_page.py)

## ❓ Частые вопросы

**Q: Как найти селекторы элементов?**
A: Используйте DevTools браузера (F12) → Elements → Inspect элемент → Copy selector

**Q: Как запустить тесты в headless режиме?**
A: В `tests/conftest.py` измените `headless=False` на `headless=True`

**Q: Как добавить скриншоты при ошибках?**
A: Используйте `take_screenshot()` из `src/utils/ui_helpers.py` в блоке `except`

**Q: Как комбинировать UI и Backend тесты?**
A: См. примеры в `tests/integration/test_ui_backend_integration_example.py`

