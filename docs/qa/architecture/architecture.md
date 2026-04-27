# Architecture

## Общая схема

```text
tests
  -> fixtures / conftest
  -> pages / services / repositories / validators
  -> drivers / config
  -> allure-results / allure-report
```

## Tests

Отвечают за сценарий, входные условия и assertions.

```text
tests/backend/
tests/web/
tests/mobile/
tests/unit/
tests/integration/
```

## Page Objects

Отвечают за UI-взаимодействие и локаторы.

```text
src/pages/web/
src/pages/mobile/
```

Правила:

- тест не должен хранить локаторы
- повторяемое UI-действие живет в Page Object
- flow orchestration живет в helper/fixture, а не в странице

## Drivers

```text
src/drivers/playwright_driver.py
src/drivers/appium_driver.py
```

Отвечают за создание и настройку браузера или mobile-сессии.

## Repositories

```text
src/repositories/
```

Отвечают за доступ к MongoDB/PostgreSQL. В тестах не должно быть прямых `db[collection]`, если уже есть repository-слой.

## Services and Validators

```text
src/services/
src/validators/
```

Используются для бизнес-логики, составных проверок и формирования отчетов.

## Reporting

```text
allure-results/
allure-report/
src/utils/allure_report_patcher.py
src/utils/allure_html.py
```

## См. также

- [[backend]]
- [[web]]
- [[mobile]]
- [[reporting-allure]]
