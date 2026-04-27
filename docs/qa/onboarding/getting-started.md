# Getting Started

## Установка зависимостей

```bash
pip install -r requirements.txt
playwright install chromium
```

## Настройка окружения

Создать `.env` из примера:

```bash
copy .env.example .env
```

Заполнить основные переменные:

```env
ENVIRONMENT=prod
WEB_BASE_URL=https://your-web-app.com

MONGO_USER_PROD=
MONGO_PASSWORD_PROD=
MONGO_HOSTS_PROD=
MONGO_REPLICA_SET_PROD=rs0
MONGO_DB_NAME_PROD=Cluster0

POSTGRES_HOST=
POSTGRES_PORT=5432
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DATABASE=master

APPIUM_SERVER_URL=http://localhost:4723
MOBILE_PLATFORM=Android
MOBILE_DEVICE_NAME=
MOBILE_PLATFORM_VERSION=
MOBILE_APP_PACKAGE=
MOBILE_APP_ACTIVITY=
```

## Проверка окружения

```bash
pytest --version
python -m pytest tests/unit -v
```

## Web prerequisites

```bash
playwright install chromium
```

## Mobile prerequisites

```bash
adb devices
appium --version
appium
```

## Allure prerequisites

```bash
allure --version
```

## См. также

- [[run-tests]]
- [[mobile]]
- [[debugging]]
- [[../../android_setup|Android setup]]
