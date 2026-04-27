# Reporting: Allure

## Назначение

Allure используется для:

- просмотра результатов прогонов
- группировки тестов по feature/story/tag
- вложений с диагностикой
- публикации artifacts в CI/CD
- анализа gate checks и monitoring scenarios

## Локальный запуск

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## Генерация HTML-отчета

```bash
allure generate allure-results -o allure-report --clean
allure open allure-report
```

## Через `run_tests.py`

```bash
python run_tests.py
```

`run_tests.py`:

- очищает или создает `allure-results`
- пишет `environment.properties`
- добавляет `categories.json`
- передает `--alluredir`
- генерирует `allure-report`
- применяет `src/utils/allure_report_patcher.py`

## Metadata pattern

```python
@allure.feature("Payments")
@allure.story("Bonus accrual")
@allure.title("Бонусы начисляются корректно")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses")
```

## Attachments

```python
allure.attach(
    report_text,
    name="Violations",
    attachment_type=allure.attachment_type.TEXT,
)
```

## Deep dive

- [[../../allure/README|Allure docs]]
- [[../../allure/report_generation|Report generation]]
- [[../../allure/report_ui_patch|Report UI patch]]
- [[../../allure/backend_reporting_rules|Backend reporting rules]]

## См. также

- [[run-tests]]
- [[backend]]
- [[ci-cd]]
