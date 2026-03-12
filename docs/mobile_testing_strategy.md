# Стратегия тестирования мобильного приложения

## Режимы приложения (Client / Coach)

Приложение работает в двух режимах в зависимости от роли пользователя:

| Режим | Доступность | Описание |
|-------|-------------|----------|
| **Client app** | У всех пользователей (режим по умолчанию) | Основной сценарий: клиент записывается, смотрит записи, профиль и т.д. |
| **Coach app** | Только у пользователей с ролью тренера | Отдельный функционал для тренеров. |

**Поведение при запуске:**

- Если у пользователя **только Client** — приложение сразу открывается в режиме Client app.
- Если у пользователя есть доступ к **Coach app** — при запуске сначала показывается **выбор режима** (Client / Coach), после выбора открывается соответствующий режим.

В дальнейшем потребуется покрытие тестами и для Coach app (отдельные страницы, флоу, роль пользователя в тестовых данных).

### Совместимость с текущей архитектурой

**Рефакторить сейчас не нужно.** Текущая реализация заточена под Client app (все страницы, shell, home, фикстуры `potential_user_on_main_screen`, `run_auth_to_main` и т.д.) — это корректно: тестовые пользователи (например, `role: potential`) не имеют доступа к Coach, поэтому экран выбора режима им не показывается и флоу остаётся «запуск → Preview/авторизация → главная Client».

**Когда появятся тесты для Coach app и пользователи с доступом в Coach:**

1. **Экран выбора режима** — добавить Page Object (например `AppModeSelectionPage` в `auth/` или в `shell/`), который определяет экран и нажимает «Client» или «Coach».
2. **Фикстуры Client** — в хелперах/фикстурах, ведущих «до главной Client», после запуска приложения добавить шаг: если отображается экран выбора режима → выбрать «Client», затем продолжать текущий флоу (Preview → …).
3. **Тесты Coach** — отдельные фикстуры (пользователь-тренер, выбор «Coach» при запуске), отдельная структура страниц под Coach app (например `pages/mobile/coach/` или явная маркировка страниц по режиму), тесты в `tests/mobile/coach/` или по смыслу рядом с существующими.

Драйвер и пакет приложения общие; различается только точку входа (выбор режима) и последующие экраны.

## Приоритетные тесты для начала

### 1. Smoke тесты (критичные функции)

#### ✅ Тест 1: Запуск приложения
- Приложение открывается
- Правильный экран загружается
- Нет критических ошибок

#### ✅ Тест 2: Навигация по основным экранам
- Переходы между главными разделами работают
- Кнопки навигации кликабельны
- Нет зависаний

#### ✅ Тест 3: Авторизация (если есть)
- Поля ввода работают
- Кнопка входа кликабельна
- Валидация работает

### 2. Регрессионные тесты (основной функционал)

#### ✅ Тест 4: Проверка видимости ключевых элементов
- Главные кнопки видны
- Текст читаем
- Изображения загружаются

#### ✅ Тест 5: Взаимодействие с элементами
- Клики работают
- Свайпы работают
- Скролл работает

#### ✅ Тест 6: Формы и ввод данных
- Поля ввода принимают текст
- Валидация работает
- Кнопки отправки активны

### 3. UI тесты (интерфейс)

#### ✅ Тест 7: Проверка элементов на экране
- Все элементы на месте
- Правильные тексты
- Правильные размеры

#### ✅ Тест 8: Адаптивность
- Элементы не перекрываются
- Текст не обрезается
- Кнопки доступны

## Запуск тестов

Мобильные тесты запускаются через скрипт **`run_tests_mobile.py`** и список тестов в **`tests_to_run_mobile.txt`**:

```bash
python run_tests_mobile.py
```

- **Файл списка:** по умолчанию `tests_to_run_mobile.txt`. Другой файл: `python run_tests_mobile.py -f <файл>`.
- **Без Allure:** `python run_tests_mobile.py --no-allure`.
- В `tests_to_run_mobile.txt` поддерживаются директивы: `ALLURE`, `OPEN_REPORT`, `INTERACTIVE`, `PYTEST_ARGS`. Строки с путями — относительные пути к тестам (как в pytest); после `|` можно указать аргументы pytest для строки (например `-v -m mobile --mobile-no-reset`).

Прямой запуск pytest для мобильных тестов:

```bash
pytest tests/mobile/ -v -m mobile
```

Для отладки с сохранением состояния приложения между тестами: `--mobile-no-reset`. Фикстуры и маркеры описаны в `tests/mobile/conftest.py`.

## Рекомендуемый порядок реализации

### Неделя 1: Базовые проверки
1. Запуск приложения ✅ (уже есть)
2. Проверка главного экрана
3. Проверка навигации

### Неделя 2: Взаимодействие
4. Клики по кнопкам
5. Ввод текста
6. Свайпы и скролл

### Неделя 3: Функциональность
7. Авторизация (если есть)
8. Основные сценарии использования
9. Обработка ошибок

## Структура тестов

Тесты организованы **по функциональным областям**. Тип проверки (smoke / regression / ui) задаётся маркерами pytest, а не папками.

```
tests/mobile/
├── __init__.py
├── conftest.py
├── helpers/                    # Вспомогательные функции для тестов
│   ├── __init__.py
│   ├── auth_helpers.py
│   ├── profile_helpers.py
│   └── onboarding_helpers.py
├── infra/                      # Технические проверки: связь Appium, запуск приложения
│   ├── test_appium_connection.py
│   └── test_app_launch.py
├── auth/                       # Авторизация: Preview → phone → SMS
│   └── test_phone_auth_refactored.py
├── onboarding/                 # Онбординг нового клиента (полный флоу)
│   └── test_client_onboarding.py
├── home/                       # Главный экран: состояния, точки входа
│   ├── test_main_screen.py
│   └── test_home_entrypoints_new_user.py
├── navigation/                 # Навигация, таббар
│   ├── test_bottom_navigation.py
│   └── test_navigation_new_user.py
└── flows/                      # Сквозные e2e сценарии (cross-area)
    └── rabbit_hole/
        └── new_client_buy_rh.py
```

### Маркеры pytest (вместо папок-по-типу)

```ini
# pytest.ini / pyproject.toml
markers =
    smoke:      критичные проверки, запускаются при каждом деплое
    regression: полный регресс
    ui:         проверки визуальных элементов
    mobile:     все мобильные тесты
```

Примеры запуска:

```bash
pytest tests/mobile/ -m smoke                     # только smoke
pytest tests/mobile/home/ -m "smoke or regression"
pytest tests/mobile/ -m mobile                    # все мобильные
```

## Структура страниц (Page Objects)

```
src/pages/mobile/
├── __init__.py
├── base_mobile_page.py                 # Базовый класс для мобильных страниц (самостоятельный экран)
├── base_content_block.py               # Базовый класс и миксин для контент-блоков (секции внутри страницы)
├── shell/                              # Оболочка приложения (main shell / tabbar)
│   ├── __init__.py
│   ├── base_shell_page.py              # Базовый класс для страниц с таббаром; предоставляет .nav
│   └── bottom_nav.py                   # Компонент нижней навигации (Главная / Записи / QR / Статистика / Профиль)
├── auth/                               # Экраны авторизации (без таббара → BaseMobilePage)
│   ├── __init__.py
│   ├── phone_auth_page.py
│   ├── sms_code_page.py
│   ├── country_selector_page.py
│   └── preview_page.py
├── onboarding/                         # Онбординг нового клиента (без таббара → BaseMobilePage)
│   ├── __init__.py
│   ├── name_page.py
│   ├── birth_date_page.py
│   ├── gender_page.py
│   ├── fitness_goal_page.py
│   ├── workout_experience_page.py
│   ├── workout_frequency_page.py
│   ├── height_page.py
│   ├── weight_page.py
│   └── onboarding_complete_page.py
├── home/                               # Таб «Главная» (наследник BaseShellPage → имеет .nav)
│   ├── __init__.py
│   ├── home_page.py                    # Оболочка: wait_loaded(), get_current_home_state(), get_content()
│   ├── home_state.py                   # Enum: NEW_USER, SUBSCRIBED, MEMBER, UNKNOWN
│   └── content/
│       ├── __init__.py
│       ├── home_new_user_content.py    # Контент для нового пользователя
│       ├── home_subscribed_content.py  # Контент для клиента с подпиской
│       └── home_member_content.py      # Контент для клиента с абонементом
├── bookings/                           # Таб «Записи» + связанные экраны (BaseShellPage)
│   ├── __init__.py
│   ├── bookings_page.py
│   └── qr_overlay.py                   # QR-оверлей, открываемый из таббара
├── clubs/                              # Экраны «Клубы»
│   ├── __init__.py
│   ├── clubs_page.py
│   └── club_details_page.py            # Детали конкретного клуба (описание, адрес, CTA)
├── stats/                              # Таб «Статистика» (BaseShellPage)
│   ├── __init__.py
│   └── stats_page.py
├── profile/                            # Таб «Профиль» (BaseShellPage)
│   ├── __init__.py
│   └── profile_page.py
├── products/                           # Продукты/фичи внутри приложения
│   ├── __init__.py
│   ├── gym_buddy_page.py
│   ├── rabbit_hole_page.py
│   ├── health_page.py                  # Лендинг «Health» (открывается с главной по промо-баннеру)
│   └── store_page.py                   # Экран магазина Store (одежда, спортпит)
├── bonuses/                            # Экран «Бонусы» (открывается с главной NEW_USER)
│   ├── __init__.py
│   └── bonuses_page.py
├── notifications/                      # Экран «Уведомления»
│   ├── __init__.py
│   └── notifications_page.py
└── common/                             # Общие компоненты/утилиты для мобильных страниц
    ├── __init__.py
    └── (будущие общие компоненты)
```

### Архитектура shell + tabbar

Tabbar принадлежит **оболочке приложения (main shell)**, а не конкретному разделу:

- **`BaseMobilePage`** — основа для всех страниц. `nav` недоступен.
- **`BaseShellPage(BaseMobilePage)`** — базовый класс для разделов с таббаром. Предоставляет свойство `.nav → BottomNav`.
- **`BottomNav`** — компонент навигации. Каждый метод кликает по табу, ждёт загрузки и возвращает нужный Page Object.
- **Страницы с таббаром** (Home / Bookings / Stats / Profile) наследуются от `BaseShellPage`.
- **Страницы без таббара** (auth, onboarding, bonuses, notifications, fullscreen-флоу) наследуются от `BaseMobilePage`.

**Валидация страницы:** при открытии/инициализации любой страницы сначала выполняется проверка ключевых элементов (DETECT_LOCATOR / assert_ui); действия допустимы только после успешной валидации.

В тестах навигация выглядит так:

```python
home = HomePage(driver).wait_loaded()
bookings = home.nav.open_bookings()
stats = bookings.nav.open_stats()
profile = stats.nav.open_profile()
home = profile.nav.open_main()
```

### Главный экран (Home)

Главный экран реализован как **оболочка + контент по состоянию**:

- **`HomePage`** — наследник `BaseShellPage`. Определяет состояние главного экрана и возвращает нужный объект контента.
- **`HomeState`** — enum: `NEW_USER`, `SUBSCRIBED`, `MEMBER`, `UNKNOWN`.
- **Классы в `home/content/`** — контент для каждого типа пользователя; наследуются от **`BaseContentBlock`** (секция/контент-блок, не страница). У каждого есть `DETECT_LOCATOR` для автоматического определения состояния. Разделение: страница = `BaseMobilePage` / `BaseShellPage`, контент внутри страницы = `BaseContentBlock`.

```python
home = HomePage(driver).wait_loaded()
state = home.get_current_home_state()   # → HomeState.NEW_USER / SUBSCRIBED / MEMBER
content = home.get_content()            # → HomeNewUserContent / ...
```