# Генерация Allure-отчёта

Этот документ описывает техническую сторону генерации Allure-отчёта в проекте.

## Основной поток

Главная точка входа — `run_tests.py`.

При включённой генерации Allure раннер:

1. создаёт или очищает каталог `allure-results`;
2. пишет `environment.properties`;
3. пишет `categories.json`;
4. добавляет `--alluredir <каталог>` в pytest-аргументы, если флаг ещё не задан;
5. запускает pytest по тестам из run-list;
6. после выполнения вызывает `allure generate -o allure-report <allure-results>`;
7. применяет локальный UI-патч через `src/utils/allure_report_patcher.py`;
8. открывает итоговый отчёт через `allure open allure-report`.

## Что задаётся в `run_tests.py`

В `run_tests.py` живёт именно orchestration-логика, а не канонические правила оформления тестовых вложений.

Там задаются:

- имя каталога результатов `allure-results`;
- имя итогового каталога `allure-report`;
- содержимое `environment.properties` по режимам `mobile`, `backend`, `monitoring`, `web`;
- выбор `categories.json`;
- вызовы `allure generate` и `allure open`.

## Что задаётся не здесь

Ниже перечислены вещи, которые не считаются частью генератора отчёта и поэтому описаны отдельно:

- правила оформления backend Allure-отчётов: `backend_reporting_rules.md`;
- общие backend-параметры Allure (`Окружение`, `Период анализа`, `Диапазон дат`): `tests/backend/conftest.py`;
- визуальная постобработка HTML-вложений: `report_ui_patch.md`.

## Связанные файлы

- `run_tests.py`
- `tests_to_run_backend.txt`
- `tests_to_run_backend_monitoring.txt`
- `tests_to_run_mobile.txt`
- `tests_to_run_web.txt`
