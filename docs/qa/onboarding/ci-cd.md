# CI/CD

## Назначение

CI/CD должен:

- установить зависимости
- подготовить окружение
- запустить нужный набор тестов
- сохранить `allure-results`
- опубликовать `allure-report` или artifacts

## Универсальный pipeline

```text
checkout
  -> setup python
  -> install dependencies
  -> install playwright browsers
  -> prepare .env / secrets
  -> run pytest
  -> generate allure report
  -> publish artifacts
```

## Базовые команды

```bash
pip install -r requirements.txt
playwright install chromium
pytest -m "backend or web" --alluredir=allure-results
allure generate allure-results -o allure-report --clean
```

## Mobile в CI

Перед запуском mobile-тестов нужны:

- Android emulator или physical device
- Appium server
- переменные `MOBILE_*`
- установленное приложение или путь к APK

```bash
adb devices
appium
pytest -m mobile --alluredir=allure-results
```

## Рекомендуемые jobs

- `unit` - быстрые unit tests
- `backend` - backend gate checks
- `web-smoke` - web smoke
- `mobile-smoke` - mobile smoke
- `monitoring` - scheduled backend monitoring

## Artifacts

```text
allure-results/
allure-report/
screenshots/
tmp/
```

## См. также

- [[run-tests]]
- [[reporting-allure]]
- [[debugging]]
