# Стратегия тестирования мобильного приложения

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

```
tests/mobile/
├── __init__.py
├── conftest.py
├── smoke/              # Смоук и критичный функционал
│   ├── test_app_launch.py
│   ├── test_main_screen.py
│   ├── test_client_onboarding.py
│   └── test_phone_auth_refactored.py
├── navigation/         # Навигация по приложению
│   ├── test_bottom_navigation.py
│   └── test_navigation_new_user.py   # Smoke: навигация для NEW_USER (вход по potential → обход табов, без онбординга)
├── elements/           # Базовые проверки UI‑элементов
│   └── test_buttons.py
├── scenarios/          # Сквозные пользовательские сценарии
│   └── test_basic_user_flow.py
├── flows/              # Сложные бизнес‑флоу
│   └── rabbit_hole/
│       └── new_client_buy_rh.py
├── helpers/            # Вспомогательные функции для тестов
│   ├── __init__.py
│   └── auth_helpers.py
└── utils/              # Технические проверки/утилиты
    └── test_appium_connection.py
```

## Структура страниц (Page Objects)

```
src/pages/mobile/
├── base_mobile_page.py         # Базовый класс для всех мобильных страниц
├── shell/                      # Оболочка приложения (main shell / tabbar)
│   ├── base_shell_page.py      # Базовый класс для страниц с таббаром; предоставляет .nav
│   └── bottom_nav.py           # Компонент нижней навигации (open_main/bookings/stats/profile)
├── auth/                       # Экраны авторизации (без таббара → BaseMobilePage)
│   ├── phone_auth_page.py
│   ├── sms_code_page.py
│   ├── country_selector_page.py
│   └── preview_page.py
├── onboarding/                 # Онбординг нового клиента (без таббара → BaseMobilePage)
│   ├── name_page.py
│   ├── birth_date_page.py
│   ├── gender_page.py
│   ├── fitness_goal_page.py
│   ├── workout_experience_page.py
│   ├── workout_frequency_page.py
│   ├── height_page.py
│   ├── weight_page.py
│   └── onboarding_complete_page.py
├── home/                       # Таб «Главная» (наследник BaseShellPage → имеет .nav)
│   ├── home_page.py            # Оболочка: wait_loaded(), get_current_home_state(), get_content()
│   ├── home_state.py           # Enum: NEW_USER, SUBSCRIBED, MEMBER, UNKNOWN
│   └── content/
│       ├── home_new_user_content.py    # Контент для нового пользователя
│       ├── home_subscribed_content.py  # Контент для клиента с подпиской
│       └── home_member_content.py      # Контент для клиента с абонементом
├── bookings/                   # Таб «Записи» (BaseShellPage)
│   └── bookings_page.py
├── stats/                      # Таб «Статистика» (BaseShellPage)
│   └── stats_page.py
├── profile/                    # Таб «Профиль» (BaseShellPage)
│   └── profile_page.py
└── products/                   # Продукты/фичи внутри приложения
    └── rabbit_hole_page.py
```

### Архитектура shell + tabbar

Tabbar принадлежит **оболочке приложения (main shell)**, а не конкретному разделу:

- **`BaseMobilePage`** — основа для всех страниц. `nav` недоступен.
- **`BaseShellPage(BaseMobilePage)`** — базовый класс для разделов с таббаром. Предоставляет свойство `.nav → BottomNav`.
- **`BottomNav`** — компонент навигации. Каждый метод кликает по табу, ждёт загрузки и возвращает нужный Page Object.
- **Страницы с таббаром** (Home / Bookings / Stats / Profile) наследуются от `BaseShellPage`.
- **Страницы без таббара** (auth, onboarding, fullscreen-флоу) наследуются от `BaseMobilePage`.

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
- **Классы в `home/content/`** — контент для каждого типа пользователя. У каждого есть `DETECT_LOCATOR` для автоматического определения состояния.

```python
home = HomePage(driver).wait_loaded()
state = home.get_current_home_state()   # → HomeState.NEW_USER / SUBSCRIBED / MEMBER
content = home.get_content()            # → HomeNewUserContent / ...
```