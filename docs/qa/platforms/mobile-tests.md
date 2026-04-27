# Каталог Mobile-Тестов

## Назначение

Этот каталог описывает конкретные mobile UI-тесты: их назначение, логику, данные и критерии падения.

- `tests_to_run_mobile.txt` — набор тестов, которые входят в mobile suite.

Используйте этот файл при добавлении, изменении или ревью mobile-тестов.
[mobile.md](mobile.md) остаётся общим entrypoint платформы (запуск, конфигурация, правила),
а этот документ объясняет смысл конкретных тест-файлов.

## Общие Правила Mobile UI-Тестов

- Профиль `mobile`; запуск через Appium Android, реальное или эмулируемое устройство.
- UI-действия и локаторы держать в Page Objects; helpers — только для orchestration-level flows.
- Фикстуры готовят STAGE-пользователя и гарантируют его стартовое состояние до начала теста.
- Состояние экрана проверяется через `assert_ui()` page object; тест не дублирует локаторы.
- Allure в mobile-тестах не используется; диагностика — через stdout print и screenshot/page source при падении.

## Статистика

### `tests/mobile/stats/test_stats_modes.py`

**Тест:** `test_stats_modes_expose_expected_entrypoints` (параметризован)  
**Профиль:** `mobile`  
**Цель:** Проверить, что раздел «Статистика» корректно работает в двух режимах — без статистики (`POTENTIAL_USER`) и с накопленной статистикой (`RABBIT_HOLE_USER`).

**Сценарии:**

| id | Пользователь | Проверочная функция |
|---|---|---|
| `no_stats-potential-entrypoints` | `POTENTIAL_USER` | `_check_no_stats_entrypoints` |
| `with_stats-rabbit_hole-controls` | `RABBIT_HOLE_USER` | `_check_with_stats_controls` |

**Общие шаги (оба сценария):**

1. `MobileTestUserSelector.select_or_skip(scenario)` — выбрать STAGE-пользователя или пропустить тест.
2. `ensure_test_user_session(driver, db, context)` — авторизовать и гарантировать стартовое состояние.
3. `nav.open_stats()` — нажать BottomNav «Статистика»; assert `isinstance(stats, StatsPage)`.
4. Вызвать проверочную функцию `stats_check(stats)`.

**Сценарий `_check_no_stats_entrypoints` (POTENTIAL_USER):**

1. `stats.assert_inbody_entrypoint_visible()` — entrypoint InBody виден.
2. `stats.open_inbody()` → assert `isinstance(inbody, InBodyPage)`.
3. `inbody.nav.open_stats()` — вернуться на Stats; assert `isinstance(stats, StatsPage)`.
4. `stats.open_subscription_selection()` → assert `isinstance(clubs_page, ClubsPage)`.

**Сценарий `_check_with_stats_controls` (RABBIT_HOLE_USER):**

1. `stats.assert_inbody_entrypoint_visible()` — entrypoint InBody виден.
2. `stats.select_month_period().assert_ui()` — переключить на «Месяц».
3. `stats.select_year_period().assert_ui()` — переключить на «Год».
4. `stats.open_datepicker()` — нажать текущий заголовок периода.

**Проверка фильтров периода (режим статистики клиента):**

| Фильтр | Когда проверяется | Маркер активного фильтра |
|---|---|---|
| **Неделя** | `assert_ui()` при открытии экрана (режим по умолчанию) | `"Часы"` + диапазон дат вида `"27 апреля - 03 мая"` |
| **Месяц** | `select_month_period()` + `assert_ui()` | `"Посещения"` + заголовок `"апрель 2026"` (динамически) |
| **Год** | `select_year_period()` + `assert_ui()` | `"Посещения"` + заголовок `"2026"` (динамически) |

Все три заголовка периода формируются динамически на основе `datetime.now()` в момент выполнения теста. Для «Недели» используются родительный падеж (`RUSSIAN_MONTH_NAMES_GENITIVE`) и нулевой паддинг дней (`%02d`), например `"27 апреля - 03 мая"`. Экран открывается в режиме «Неделя» по умолчанию; `"Часы"` уникален для этого режима и отсутствует в «Месяце» и «Годе».

**Поддержанные состояния `StatsPage.assert_ui()`:**

| Состояние | Маркеры |
|---|---|
| Пустая статистика | `"Тут появятся время в зале…"` + кнопка `"Выбрать абонемент"` |
| InBody | `"Пройдите оценку Inbody"` + описание теста |
| Статистика клиента | `"НЕДЕЛИ ПОДРЯД"` + фильтры `Неделя/Месяц/Год` + `"Часы"` (если активна «Неделя») |

Если ни одно состояние не распознано — `assert_ui()` выбрасывает `AssertionError`.

**Данные:**

- `POTENTIAL_USER` — STAGE-пользователь без абонемента.
- `RABBIT_HOLE_USER` — STAGE-пользователь с накопленной статистикой.
- Page Objects: `StatsPage`, `InBodyPage`, `ClubsPage`.

**Критерии падения:**

- `select_or_skip` не нашёл подходящего пользователя → `pytest.skip`.
- `open_stats()` вернул не `StatsPage` → assert `isinstance`.
- `assert_ui()` не нашла ни одного валидного состояния → `AssertionError`.
- `select_month_period()` / `select_year_period()` не дождались метрики или заголовка → `wait_visible` timeout.
- `open_inbody()` / `open_subscription_selection()` вернули неожиданный тип → assert `isinstance` с именем фактического класса.

**Прямой запуск:**

```bash
pytest tests/mobile/stats/test_stats_modes.py -v -m mobile -s --mobile-no-reset
```

**См. также:** [mobile.md](mobile.md) — конфигурация Appium, правила запуска.
