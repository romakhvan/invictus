# Debugging

## Базовый алгоритм

1. Запустить тест отдельно.
2. Добавить `-v -s`.
3. Проверить `.env`.
4. Проверить доступность БД, web-сайта или Appium.
5. Открыть Allure attachments.

```bash
pytest path/to/test.py::test_name -v -s
```

## Backend

Проверить:

- `ENVIRONMENT`
- MongoDB/PostgreSQL credentials
- доступность коллекций/таблиц
- период `--period-days`
- repository/query logic
- наличие данных

## Web

Проверить:

- `WEB_BASE_URL`
- доступность сайта
- cookie consent
- локаторы
- headless/headed режим
- ожидания загрузки

## Mobile

```bash
adb devices
appium --version
```

Проверить:

- устройство online
- Appium server запущен
- package/activity корректны
- приложение установлено
- экран не заблокирован
- разрешения выданы

## Allure

```bash
pytest path/to/test.py --alluredir=allure-results
allure serve allure-results
```

## Что прикладывать к багу

- команда запуска
- окружение
- stack trace
- Allure report или artifacts
- screenshot
- mobile page source
- входные данные
- expected/actual

## Deep dive

- [[../../appium_troubleshooting|Appium troubleshooting]]
- [[../../APP_MINIMIZE_PREVENTION|App minimize prevention]]
- [[../../allure/README|Allure docs]]

## См. также

- [[reporting-allure]]
- [[test-data]]
- [[best-practices]]
