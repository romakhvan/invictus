# Web Tests

## Назначение

Web-тесты проверяют публичный сайт через Playwright.

## Где лежит код

```text
tests/web/
src/pages/web/
src/drivers/playwright_driver.py
```

## Запуск

```bash
pytest tests/web -v
pytest -m web -v
pytest -m "web and smoke" -v
```

## Конфигурация

```env
WEB_BASE_URL=https://your-web-app.com
WEB_TIMEOUT=30000
```

## Page Object pattern

```text
src/pages/web/base_web_page.py
src/pages/web/home_page.py
src/pages/web/clubs_page.py
src/pages/web/auth_page.py
```

## Правила

- локаторы хранить в Page Object
- проверять видимое состояние, а не только URL
- не добавлять `sleep` без причины
- учитывать cookie consent и загрузку Next.js страниц
- новый регулярный тест добавлять в `tests_to_run_web.txt`

## Deep dive

- [[../../web_testing_strategy|Web testing strategy]]
- [[../../ui_testing_setup|UI testing setup]]

## См. также

- [[architecture]]
- [[run-tests]]
- [[debugging]]
