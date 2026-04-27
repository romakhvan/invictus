# Invictus Test Automation Framework

Автоматизированные тесты для backend, web и mobile-направлений Invictus.

## Документация

Основная точка входа:

- [QA Docs](docs/qa/README.md)

Быстрые страницы:

- [Quick Start](docs/QUICK_START.md)
- [Run tests](docs/qa/onboarding/run-tests.md)
- [Backend tests](docs/qa/platforms/backend.md)
- [Web tests](docs/qa/platforms/web.md)
- [Mobile tests](docs/qa/platforms/mobile.md)
- [Allure reporting](docs/qa/architecture/reporting-allure.md)
- [Legacy docs index](docs/qa/legacy/legacy-docs-index.md)

## Возможности

- Backend checks для MongoDB/PostgreSQL и бизнес-правил
- Web UI tests через Playwright
- Mobile UI tests через Appium
- Unit tests для helpers, repositories и инфраструктуры
- Allure-отчетность
- Списки регулярных запусков через `tests_to_run_*.txt`

## Структура

```text
src/
  config/        # конфигурация
  drivers/       # Playwright и Appium драйверы
  pages/         # Page Objects
  repositories/  # доступ к данным
  services/      # бизнес-сервисы и проверки
  utils/         # утилиты
  validators/    # валидаторы

tests/
  backend/       # backend/data checks
  web/           # web UI tests
  mobile/        # mobile UI tests
  unit/          # unit tests
  integration/   # integration tests

docs/
  qa/           # поддерживаемая QA-документация
```

## Быстрый старт

```bash
pip install -r requirements.txt
playwright install chromium
pytest
```

## Запуск тестов

```bash
pytest -m backend
pytest -m web
pytest -m mobile
python run_tests.py
```

## Allure

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

Подробнее: [Allure reporting](docs/qa/architecture/reporting-allure.md).

## Технологии

- Python
- Pytest
- Playwright
- Appium / Selenium
- MongoDB / PyMongo
- PostgreSQL / psycopg2
- Allure
