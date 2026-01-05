# Invictus Test Automation Framework

Автоматизированная система тестирования для веб и мобильного приложения.

## 🎯 Возможности

- **Backend тесты** - тестирование MongoDB, валидация данных
- **Web тесты** - автоматизация веб-сайта с Playwright
- **Mobile тесты** - автоматизация мобильного приложения с Appium
- **Интеграционные тесты** - комбинация UI и Backend проверок

## 📁 Структура проекта

```
├── src/
│   ├── config/          # Конфигурация (БД, приложение)
│   ├── drivers/         # Драйверы (Playwright, Appium)
│   ├── pages/           # Page Objects (web, mobile)
│   ├── repositories/    # Работа с MongoDB
│   ├── utils/           # Утилиты (тестовые данные, UI хелперы)
│   └── validators/      # Валидаторы данных
├── tests/
│   ├── backend/         # Backend тесты
│   ├── web/            # Web тесты
│   ├── mobile/         # Mobile тесты
│   └── integration/    # Интеграционные тесты
└── docs/               # Документация
```

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Настройка конфигурации

Отредактируйте `src/config/app_config.py`:
- Укажите `WEB_BASE_URL` для веб-тестов
- Настройте параметры Appium для мобильных тестов

### 3. Запуск тестов

```bash
# Все тесты
pytest

# Только backend
pytest -m backend

# Только web
pytest -m web

# Только mobile
pytest -m mobile

# Smoke тесты
pytest -m smoke
```

## 📚 Документация

- [Настройка UI тестирования](docs/ui_testing_setup.md)
- [План тестирования](docs/testing_roadmap.md)
- [Руководство по кошельку тренера](docs/coach_wallet_testing_guide.md)

## 🏗️ Архитектура

Проект следует принципам **Page Object Model (POM)**:
- Разделение логики тестов и взаимодействия со страницами
- Переиспользование кода
- Легкая поддержка и расширение

## 📝 Примеры

### Web тест

```python
@pytest.mark.web
def test_login(web_page: Page):
    login_page = LoginPage(web_page)
    login_page.login("username", "password")
    assert login_page.is_logged_in()
```

### Интеграционный тест

```python
@pytest.mark.web
def test_user_creation(web_page: Page, db):
    # UI действие
    registration_page = RegistrationPage(web_page)
    registration_page.create_user("test@example.com")
    
    # Проверка в БД
    user = find_user_by_email(db, "test@example.com")
    assert user is not None
```

## 🔧 Технологии

- **Python 3.x**
- **Pytest** - фреймворк тестирования
- **Playwright** - автоматизация веб-браузеров
- **Appium** - автоматизация мобильных приложений
- **MongoDB** - база данных
- **PyMongo** - работа с MongoDB

## 📋 Следующие шаги

См. [План тестирования](docs/testing_roadmap.md) для детального руководства по началу работы.