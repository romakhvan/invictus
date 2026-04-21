# Allure Documentation

Эта папка является единой точкой входа по работе с Allure в репозитории.

## Что где лежит

- `backend_reporting_rules.md` — канонический стандарт оформления backend Allure-отчётов.
- `report_generation.md` — как `run_tests.py` собирает `allure-results` и `allure-report`.
- `report_ui_patch.md` — зачем нужен `src/utils/allure_report_patcher.py` и что именно он меняет в UI отчёта.

## Быстрый маршрут по задачам

- Нужно понять, как оформлять backend-тест и вложения: откройте `backend_reporting_rules.md`.
- Нужно понять, откуда берутся `environment.properties`, `categories.json` и когда вызывается `allure generate`: откройте `report_generation.md`.
- Нужно понять, почему HTML-вложения в отчёте выглядят не как в vanilla Allure: откройте `report_ui_patch.md`.

## Связанные файлы в коде

- `run_tests.py` — orchestration-слой генерации отчёта.
- `tests/backend/conftest.py` — общие Allure-параметры backend-тестов.
- `src/utils/allure_report_patcher.py` — локальный UI-патч готового `allure-report`.

## Правило поддержки

Если меняется Allure-поведение, сначала обновляйте соответствующий документ в этой папке, а уже потом дублирующие ссылки или краткие упоминания в других файлах.
