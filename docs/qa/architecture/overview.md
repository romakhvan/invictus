# Overview

## Назначение

Проект автоматизирует проверки для:

- backend-данных и бизнес-правил
- публичного web-сайта через Playwright
- Android mobile-приложения через Appium
- unit/integration проверок инфраструктуры
- monitoring/reporting сценариев с Allure-вложениями

## Технологии

- Python
- Pytest
- Playwright
- Appium / Selenium
- MongoDB / PyMongo
- PostgreSQL / psycopg2
- Allure

## Основные директории

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
```

## Маркеры

- `backend`
- `backend_check`
- `backend_monitoring`
- `backend_research`
- `web`
- `mobile`
- `smoke`
- `regression`
- `interactive_mobile`
- `flow`

## См. также

- [[architecture]]
- [[test-strategy]]
- [[run-tests]]
- [[legacy-docs-index]]
