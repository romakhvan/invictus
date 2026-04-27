# Стратегия тестирования мобильного приложения

## Назначение

Mobile-тесты проверяют Android-приложение через Appium:

- запуск приложения и подключение к Appium
- авторизацию и onboarding
- главный экран и его состояния
- нижнюю навигацию
- записи и клубные фильтры
- сквозные flow-сценарии

Основная точка входа новой документации: [docs/qa/platforms/mobile.md](qa/platforms/mobile.md).

## Актуальный запуск

В репозитории используется общий раннер `run_tests.py` и список `tests_to_run_mobile.txt`.

```bash
python run_tests.py
```

Для прямого запуска через pytest:

```bash
pytest tests/mobile -v
pytest -m mobile -v
pytest -m "mobile and smoke" -v
```

Для точечного запуска:

```bash
pytest tests/mobile/infra/test_appium_connection.py -v -s
pytest tests/mobile/bookings/test_bookings_entrypoints.py -v -m mobile --mobile-no-reset
pytest tests/mobile/bookings/test_bookings_entrypoints.py -v -m mobile --mobile-no-reset -k personal --keepalive
pytest tests/mobile/stats/test_stats_modes.py -v -m mobile -s --mobile-no-reset
```

Важно:

- `run_tests_mobile.py` в репозитории отсутствует.
- `tests_to_run_mobile.txt` не запускается как Python-скрипт.
- Если нужен запуск списка mobile-тестов, используйте `run_tests.py` с `MODE = "mobile"` или прямой `pytest`.

## Prerequisites

```bash
adb devices
appium --version
appium
```

Переменные окружения:

```env
APPIUM_SERVER_URL=http://localhost:4723
MOBILE_PLATFORM=Android
MOBILE_DEVICE_NAME=
MOBILE_PLATFORM_VERSION=
MOBILE_APP_PACKAGE=
MOBILE_APP_ACTIVITY=
MOBILE_APP_PATH=
```

## Структура тестов

```text
tests/mobile/
  conftest.py
  helpers/
  infra/
    test_appium_connection.py
    test_mobile_locator_debug.py
  auth/
    test_phone_auth_refactored.py
  onboarding/
    test_client_onboarding.py
    test_client_onboarding_kyrgyzstan.py
  home/
    test_home_entrypoints_new_user.py
    test_home_club_filter.py
  bookings/
    test_bookings_entrypoints.py
    test_bookings_tabs.py
    test_personal_club_filter.py
  stats/
    test_stats_modes.py
  navigation/
    test_bottom_navigation.py
    test_navigation_new_user.py
  flows/
    rabbit_hole/
      new_client_buy_rh.py
```

## Структура Page Objects

```text
src/pages/mobile/
  base_mobile_page.py
  base_content_block.py
  auth/
  onboarding/
  home/
  bookings/
  clubs/
  stats/
  profile/
  products/
  common/
  shell/
```

## Client / Coach modes

Приложение может работать в режимах Client и Coach:

- Client app - основной сценарий для клиентских mobile-тестов.
- Coach app - отдельный режим для пользователей с ролью тренера.

Текущие mobile-тесты ориентированы на Client app. Если пользователь имеет доступ к Coach app и появляется экран выбора режима, helper/fixture должен явно выбрать Client перед продолжением клиентского flow.

## Onboarding и usermetadatas

- Если у клиента уже есть запись в `usermetadatas`, после OTP onboarding не показывается.
- Для сценариев, где после авторизации ожидается главный экран или `NEW_USER`, использовать пользователя с ролью `potential`, готовым `usermetadatas` и без записей в `rabbitholev2`, `visits`, `usersubscriptions`, `accesscontrols`.
- Для полного onboarding flow использовать новый номер или пользователя без записи в `usermetadatas`.

## Helpers vs Page Objects

Page Objects (`src/pages/mobile/...`):

- локаторы
- ожидания
- UI-действия
- проверка загрузки экрана

Fixtures (`tests/mobile/conftest.py`):

- driver
- окружение
- пользователь
- preconditions

Helpers (`tests/mobile/helpers/`):

- orchestration-level шаги
- сквозные flow из готовых page-методов
- минимум retry-логики, не привязанной к одному экрану

Запрещено в helpers:

- хранить XPath/CSS/Appium локаторы
- напрямую вызывать `driver.find_element`
- дублировать методы Page Objects
- использовать `time.sleep()` вместо page-level ожиданий

## Shell и tabbar

- `BaseMobilePage` - базовый класс для всех экранов.
- `BaseShellPage` - базовый класс для экранов с tabbar.
- `BottomNav` - компонент нижней навигации.
- Home / Bookings / Stats / Profile наследуются от `BaseShellPage`.
- Auth / Onboarding / полноэкранные flow наследуются от `BaseMobilePage`.

Пример:

```python
home = HomePage(driver).wait_loaded()
bookings = home.nav.open_bookings()
stats = bookings.nav.open_stats()
profile = stats.nav.open_profile()
home = profile.nav.open_main()
```

## Stats screen

`StatsPage` поддерживает два состояния раздела `Статистика`:

- пустое состояние статистики с CTA `Выбрать абонемент`;
- сегмент `InBody` с описанием оценки состава тела.
- статистика клиента после покупки/активности: streak `НЕДЕЛИ ПОДРЯД`,
  фильтры `Неделя` / `Месяц` / `Год`, недельная метрика `Часы`
  и метрика месяца/года `Время в зале`.

Тесты режимов статистики лежат в `tests/mobile/stats/test_stats_modes.py`.
Они проверяют переход из статистики к выбору клуба/абонемента и переход в
модуль `InBody` через page-object методы `open_subscription_selection()` и
`open_inbody()`.

## Home screen

Главный экран реализован как оболочка и контент по состоянию:

- `HomePage`
- `HomeState`
- `home/content/*`

```python
home = HomePage(driver).wait_loaded()
state = home.get_current_home_state()
content = home.get_content()
```

## Маркеры

```ini
markers =
    mobile: Mobile tests (Appium)
    smoke: Smoke tests
    regression: Regression tests
    interactive_mobile: Mobile tests with interactive debug menu
    flow: Mobile end-to-end flow tests
```

## См. также

- [QA Mobile Docs](qa/platforms/mobile.md)
- [Run Tests](qa/onboarding/run-tests.md)
- [Debugging](qa/architecture/debugging.md)
- [Android setup](android_setup.md)
- [Appium troubleshooting](appium_troubleshooting.md)
- [Appium inspector guide](appium_inspector_guide.md)
