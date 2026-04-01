# Стратегия тестирования веб-сайта

## Назначение

Web тесты проверяют **публичный сайт `https://invictus.kz`** через браузер с помощью Playwright. Сайт на Next.js, интерфейс на казахском языке.

## Конфигурация

| Переменная | Назначение | По умолчанию |
|-----------|-----------|--------------|
| `WEB_BASE_URL` | Базовый URL сайта | `https://invictus.kz` |
| `WEB_TIMEOUT` | Таймаут операций (мс) | `30000` |

Переменные задаются в `.env`, читаются через `src/config/app_config.py`.

Браузер: **Chromium**, режим по умолчанию — `headless=False`. Для CI изменить в `tests/conftest.py`.

## Структура тестов

```
tests/web/
├── test_home_page.py      # Главная страница: загрузка, навигация, CTA, футер
├── test_clubs_page.py     # Страница клубов: список, фильтры, пагинация, карточки
├── test_auth_page.py      # Авторизация: форма телефона, валидация, кнопки
└── test_navigation.py     # Межстраничная навигация
```

## Запуск тестов

```bash
# Все web тесты
pytest -m web -v

# Только smoke
pytest -m "web and smoke" -v

# Один файл
pytest tests/web/test_clubs_page.py -v

# Один тест
pytest tests/web/test_clubs_page.py::test_clubs_list_not_empty -v
```

Активные тесты перечислены в `tests_to_run_web.txt`. Формат строк и логика запуска — аналогичны другим `tests_to_run_*.txt` файлам.

**Правило**: каждый новый тест-файл нужно добавить в `tests_to_run_web.txt`.

## Фикстуры

Объявлены в `tests/conftest.py`:

```python
@pytest.fixture(scope="function")
def playwright_driver():
    """Запускает браузер Chromium. Закрывается после каждого теста."""

@pytest.fixture(scope="function")
def web_page(playwright_driver):
    """Возвращает Playwright Page для использования в тесте."""
```

Каждый тест получает свежий экземпляр браузера (`scope="function"`), независимо от других.

## Page Objects

### Иерархия

```
BasePage (src/pages/base_page.py)
└── BaseWebPage (src/pages/web/base_web_page.py)   ← общие методы Playwright
    ├── HomePage   (src/pages/web/home_page.py)
    ├── ClubsPage  (src/pages/web/clubs_page.py)
    └── AuthPage   (src/pages/web/auth_page.py)
```

### BaseWebPage

Оборачивает Playwright `Page`. Предоставляет:

```python
click(selector)              # клик по элементу
fill(selector, value)        # ввод текста
get_text(selector)           # получить текст
is_visible(selector)         # проверить видимость
navigate_to(url)             # перейти по URL
get_current_url()            # текущий URL
```

Для прямого доступа к Playwright API: `self.page`.

Используются Playwright CSS-селекторы: `:has-text()`, `[href*=]`, `input[placeholder]` и т.д.

### HomePage

**URL:** `WEB_BASE_URL`

Покрывает: навигацию (Клубтар, Жаттығулар, Жаттықтырушылар, Store, Франшиза, Біз туралы), хедер (кнопка Кіру, скачать приложение), hero-секцию (заголовок, CTA-кнопки), секции типов клубов (Fitness, GO, Girls, Kids), футер.

### ClubsPage

**URL:** `WEB_BASE_URL/clubs`

Покрывает: список клубов, фильтры по типу (Fitness / GO / Girls), фильтр по городу, пагинацию, переход в карточку клуба, кнопку «Показать на карте».

Особенность: фильтры добавляют query-параметр `?type=...` в URL — тесты проверяют это явно.

### AuthPage

**URL:** `WEB_BASE_URL/auth`

Покрывает: поле телефона с маской `(000) 000 00 00`, код страны `+7`, кнопку «Келесі» (активна только при введённом номере), кнопку «Артқа».

## Маркеры

```ini
markers =
    web:        все web тесты (Playwright)
    smoke:      критичные быстрые проверки
    regression: полный регресс
```

**Smoke тесты** (~10 штук) — загрузка страниц, ключевые элементы навигации, заголовки. Запускаются при каждом деплое.

## Особенности сайта

- **Cookie consent** — диалог согласия с куки появляется при первом заходе. Тесты должны его учитывать или закрывать, если он блокирует взаимодействие.
- **Казахский язык** — все видимые тексты в селекторах на казахском: "Клубтар", "Кіру", "Келесі", "Артқа" и т.д.
- **Next.js SSR** — страницы могут требовать `wait_for_load_state("networkidle")` перед проверками.

## Что тестируется

| Файл | Тестов | Описание |
|------|--------|---------|
| `test_home_page.py` | 8 | Загрузка, навигация, секции клубов, CTA, футер |
| `test_clubs_page.py` | 11 | Список клубов, фильтры, пагинация, карточки |
| `test_auth_page.py` | 7 | Форма телефона, валидация кнопки, навигация назад |
| `test_navigation.py` | 6 | Переходы между страницами, параметризованный тест nav-ссылок |
