# Run Tests

## Все тесты

```bash
pytest
```

## Запуск по маркерам

```bash
pytest -m backend
pytest -m web
pytest -m mobile
pytest -m smoke
pytest -m regression
pytest -m "web and smoke"
pytest -m "mobile and regression"
```

## Backend

```bash
pytest tests/backend -v
pytest -m backend -v
pytest -m backend_check -v
pytest -m backend_monitoring -v
```

## Web

```bash
pytest tests/web -v
pytest -m web -v
pytest tests/web/test_clubs_page.py -v
pytest tests/web/test_clubs_page.py::test_clubs_list_not_empty -v
```

## Mobile

```bash
adb devices
appium
pytest tests/mobile -v
pytest -m mobile -v
```

## Unit tests

```bash
pytest tests/unit -v
```

## Запуск через `run_tests.py`

Актуальный раннер проекта:

```bash
python run_tests.py
```

`run_tests.py` читает списки:

- `tests_to_run_backend.txt`
- `tests_to_run_backend_monitoring.txt`
- `tests_to_run_mobile.txt`
- `tests_to_run_web.txt`

## Формат файла списка

```text
# PYTEST_ARGS: -v -s
# ALLURE: on
# OPEN_REPORT: off
# INTERACTIVE: off
# PERIOD_DAYS: 7

tests/backend/payments/test_visit_price.py
tests/web/test_home_page.py | -k smoke
```

## Устаревшие команды

- `run_tests_mobile.py` сейчас отсутствует в репозитории.
- Для mobile-списка использовать `run_tests.py` с `MODE = "mobile"` или прямой `pytest -m mobile`.

## См. также

- [[reporting-allure]]
- [[debugging]]
- [[ci-cd]]
- [[legacy-docs-index]]
