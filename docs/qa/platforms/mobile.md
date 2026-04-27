# Mobile Tests

## Назначение

Mobile-тесты проверяют Android-приложение через Appium.

## Где лежит код

```text
tests/mobile/
tests/mobile/helpers/
src/pages/mobile/
src/drivers/appium_driver.py
```

## Запуск

```bash
adb devices
appium
pytest tests/mobile -v
pytest -m mobile -v
python run_tests.py
```

## Lifecycle приложения

Текущий flow запуска mobile-теста состоит из нескольких слоёв:

1. Fixture `appium_driver` создаёт новую Appium-сессию на каждый тест через
   `AppiumDriver.start(...)`.
2. Fixture `mobile_driver` получает WebDriver и вызывает
   `ensure_mobile_app_in_foreground(...)`, чтобы убедиться, что нужный package
   открыт в foreground.
3. Fixture или сам тест выбирает helper подготовки пользователя:
   `ensure_test_user_session`, `ensure_new_user_on_home_screen`,
   `ensure_rabbit_hole_user_on_home_screen` и т.д.
4. Helper подготовки пользователя проверяет текущую сессию приложения и при
   необходимости делает restart/auth fallback.

`mobile_driver` по умолчанию не перезапускает приложение вручную:
`ENABLE_APP_RESTART = False`. Это сделано намеренно, потому что Appium уже
запускает приложение при создании сессии, а дополнительный
`terminate_app`/`activate_app` перед каждым тестом замедляет suite и может
добавлять нестабильность.

Флаг `--mobile-no-reset` передаёт в Appium `no_reset=True` и сохраняет данные
приложения между тестами. Это позволяет переиспользовать авторизованную сессию,
но не гарантирует, что данные никогда не будут очищены: helper может вызвать
`clearApp`, если нужно переключиться на другого тестового пользователя или
восстановить некорректное состояние сессии.

## Stats modes

`tests/mobile/stats/test_stats_modes.py` проверяет два режима раздела «Статистика»:

- `no_stats-potential-entrypoints` — для пользователя без абонемента: виден таб
  «InBody», кнопка «Выбрать абонемент» открывает `ClubsPage`;
- `with_stats-rabbit_hole-controls` — для пользователя с историей посещений:
  переключение периодов «Месяц» / «Год» и открытие датапикера.

`StatsPage.assert_ui()` принимает два валидных состояния таба «Статистика»:
пустое состояние с CTA покупки, а также фактическую статистику клиента
(`НЕДЕЛИ ПОДРЯД`, фильтры периода, `Часы` для недели или `Посещения`
для месяца/года).

Прямой запуск:

```bash
pytest tests/mobile/stats/test_stats_modes.py -v -m mobile -s --mobile-no-reset
```

## Rabbit Hole flow

`tests/mobile/flows/rabbit_hole/new_client_buy_rh.py` проверяет сквозной сценарий,
в котором новый потенциальный клиент покупает Rabbit Hole.

Основной сценарий:

- авторизовать пользователя и убедиться, что открыта главная в состоянии
  `NEW_USER`;
- открыть оффер Rabbit Hole с главной через `Расскажите подробнее!`;
- проверить цену оффера и цену на кнопке покупки;
- перейти к покупке, выбрать первый клуб Invictus GO и открыть подтверждение
  оплаты;
- выбрать сохраненную карту, принять оферту, оплатить и проверить success screen.

После оплаты тест дополнительно сверяет backend-состояние:

- появилась свежая запись в `transactions` с ожидаемой суммой;
- пользователю выданы 3 visit;
- создана запись покупки в `rabbitholev2`.

Тестовые данные:

- пользователь из MongoDB STAGE с ролью `potential` и записью в
  `usermetadatas`;
- сохраненная банковская карта `•• 6267`, которую тест привязывает к выбранному
  пользователю перед покупкой.

Критерии выбора mobile test users по ролям и сценариям описаны в
[[test-data#Mobile test users]].

Прямой запуск:

```bash
pytest tests/mobile/flows/rabbit_hole/new_client_buy_rh.py -v -m mobile -s --mobile-ui-logs --mobile-no-reset
```

## Конфигурация

```env
APPIUM_SERVER_URL=http://localhost:4723
MOBILE_PLATFORM=Android
MOBILE_DEVICE_NAME=
MOBILE_PLATFORM_VERSION=
MOBILE_APP_PACKAGE=
MOBILE_APP_ACTIVITY=
MOBILE_APP_PATH=
```

## Актуальный раннер

- Использовать `run_tests.py`.
- `run_tests_mobile.py` в репозитории сейчас отсутствует.
- Старые упоминания `run_tests_mobile.py` требуют сверки перед использованием.

## Правила

- UI-действия и локаторы держать в Page Objects
- helpers использовать для orchestration-level flows
- не хранить XPath/CSS/Appium локаторы в helpers
- для диагностики сохранять screenshot/page source
- `interactive_mobile` не должен попадать в CI без явного решения

## Deep dive

- [[mobile-tests|Каталог mobile-тестов]] — назначение, логика и критерии падения конкретных тест-файлов.
- [[../../mobile_testing_strategy|Mobile testing strategy]]
- [[../../android_setup|Android setup]]
- [[../../ANDROID_QUICK_START|Android quick start]]
- [[../../appium_troubleshooting|Appium troubleshooting]]
- [[../../appium_inspector_guide|Appium inspector guide]]

## См. также

- [[getting-started]]
- [[debugging]]
- [[test-data]]
- [[mobile-page-states]]
