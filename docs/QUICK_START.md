# Quick Start

## Назначение

Короткий старт для локального запуска автотестов. Основная документация живет в [docs/qa/README.md](qa/README.md).

## 1. Установить зависимости

```bash
pip install -r requirements.txt
playwright install chromium
```

## 2. Настроить `.env`

Создайте локальный файл окружения:

```bash
copy .env.example .env
```

Заполните нужные переменные:

```env
ENVIRONMENT=prod
WEB_BASE_URL=https://your-web-app.com

MONGO_USER_PROD=
MONGO_PASSWORD_PROD=
MONGO_HOSTS_PROD=
MONGO_REPLICA_SET_PROD=rs0
MONGO_DB_NAME_PROD=Cluster0

APPIUM_SERVER_URL=http://localhost:4723
MOBILE_PLATFORM=Android
MOBILE_DEVICE_NAME=
MOBILE_PLATFORM_VERSION=
MOBILE_APP_PACKAGE=
MOBILE_APP_ACTIVITY=
```

## 3. Проверить окружение

```bash
pytest --version
python -m pytest tests/unit -v
```

Для web:

```bash
pytest -m web -v
```

Для backend:

```bash
pytest -m backend -v
```

Для mobile:

```bash
adb devices
appium
pytest -m mobile -v
```

## 4. Запустить через общий раннер

```bash
python run_tests.py
```

`run_tests.py` использует списки:

- `tests_to_run_backend.txt`
- `tests_to_run_backend_monitoring.txt`
- `tests_to_run_mobile.txt`
- `tests_to_run_web.txt`

## 5. Открыть Allure

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

Или через общий раннер:

```bash
python run_tests.py
```

## Полезные ссылки

- [QA Docs](qa/README.md)
- [Run tests](qa/onboarding/run-tests.md)
- [Mobile tests](qa/platforms/mobile.md)
- [Backend tests](qa/platforms/backend.md)
- [Web tests](qa/platforms/web.md)
- [Allure reporting](qa/architecture/reporting-allure.md)
- [Debugging](qa/architecture/debugging.md)
