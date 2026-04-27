# Выбор тестового пользователя в начале mobile-теста

## Назначение

Этот документ описывает текущую схему подготовки mobile-теста: как выбирается
тестовый пользователь, как проверяется уже открытая сессия в приложении и когда
запускается повторная авторизация.

Основные файлы:

- `tests/mobile/conftest.py` - pytest fixture'ы для mobile-тестов.
- `tests/mobile/helpers/session_helpers.py` - orchestration подготовки сессии.
- `src/repositories/mobile_test_users_repository.py` - выбор `TestUserContext`.
- `src/repositories/mobile_test_users_cache.py` - локальный JSON-cache выбранных пользователей.
- `src/repositories/users_repository.py` - MongoDB-запросы и валидация кандидатов.

## Сценарии пользователей

Тип пользователя задается через `MobileTestUserScenario`:

| Сценарий | Ожидаемое состояние |
|---|---|
| `POTENTIAL_USER` | существующий potential-клиент, `HomeState.NEW_USER` |
| `SUBSCRIBED_USER` | клиент с активным абонементом, `HomeState.SUBSCRIBED` |
| `MEMBER_USER` | клиент с активным service product, `HomeState.MEMBER` |
| `RABBIT_HOLE_USER` | клиент с Rabbit Hole, `HomeState.RABBIT_HOLE` |
| `COACH_USER` | coach-пользователь; flow сейчас завершается `pytest.skip` |
| `ONBOARDING_NEW_USER` | новый свободный телефон для полного onboarding |
| `KYRGYZSTAN_ONBOARDING_NEW_USER` | onboarding через номер Кыргызстана из CLI override |

Большинство существующих mobile fixture'ов работают с уже существующими
пользователями из MongoDB STAGE. Onboarding-сценарии отличаются: они не ищут
готовую авторизованную сессию, а берут свободный или явно переданный номер.

## Выбор `TestUserContext`

Выбор выполняет `MobileTestUserSelector.select_or_skip(...)`.

Для cacheable-сценариев (`POTENTIAL_USER`, `SUBSCRIBED_USER`, `MEMBER_USER`,
`RABBIT_HOLE_USER`, `COACH_USER`) порядок такой:

1. Открывается локальный cache `data/mobile_test_users_cache.json`.
2. Для нужной категории берется последний валидный пользователь.
3. Cache-entry повторно проверяется через MongoDB validator:
   `validate_potential_test_user`, `validate_subscribed_test_user`,
   `validate_member_test_user`, `validate_rabbit_hole_test_user` или
   `validate_coach_test_user`.
4. Если cache-entry валиден, возвращается `TestUserContext` с `phone`, `user_id`,
   `role`, `expected_home_state` и `selection_source="cache"`.
5. Если entry больше не подходит, он помечается как `invalid`, причина пишется в
   cache, а его `user_id` исключается из следующего DB-поиска.
6. Если cache не дал валидного пользователя, selector ищет нового кандидата в
   MongoDB через функции `get_phone_for_*`.
7. Найденный кандидат превращается в `TestUserContext` с
   `selection_source="db_lookup"` и добавляется в cache как `valid`.

Если подходящего кандидата нет, selector выбрасывает `ValueError`, а
`select_or_skip(...)` превращает это в `pytest.skip`.

## Fixture'ы и подготовка сессии

Mobile fixture'ы в `tests/mobile/conftest.py` вызывают helper'ы из
`session_helpers.py`:

| Fixture | Helper |
|---|---|
| `potential_user_on_main_screen` | `ensure_new_user_on_home_screen` |
| `new_user_on_home` | `ensure_new_user_on_home_screen` |
| `authorized_potential_user` | `ensure_new_user_on_home_screen` |
| `subscribed_user_on_home` | `ensure_subscribed_user_on_home_screen` |
| `member_user_on_home` | `ensure_member_user_on_home_screen` |
| `rabbit_hole_user_on_home` | `ensure_rabbit_hole_user_on_home_screen` |
| `coach_user_on_home` | `ensure_coach_user_on_home_screen` |

Для parametrized entrypoint-тестов, где сценарий выбирается внутри теста,
используется `ensure_test_user_session(mobile_driver, db, context)`.

## Что происходит в начале теста

Для `POTENTIAL_USER` / `NEW_USER` путь сейчас такой:

1. Fixture вызывает `ensure_new_user_on_home_screen`.
2. Selector выбирает `POTENTIAL_USER` и возвращает `TestUserContext`.
3. `_restart_app_when_tabbar_missing` проверяет авторизованный tabbar через
   `is_authorized_shell_visible`.
4. Если tabbar не найден, приложение один раз перезапускается через
   `_restart_app`, затем tabbar проверяется повторно.
5. Helper пытается переиспользовать текущую сессию:
   `_try_reuse_existing_potential_home` открывает профиль через `BottomNav`,
   сверяет пользователя с выбранным `TestUserContext` через MongoDB и возвращает
   на главную.
6. Если профиль совпал и состояние главной равно ожидаемому `HomeState`, тест
   стартует без повторной OTP-авторизации.
7. Если сессия не подходит, выполняется `_ensure_home_state_by_phone`:
   приложение перезапускается, запускается `run_auth_to_home`, затем проверяется
   фактическое состояние `HomePage`.
8. После авторизации профиль еще раз сверяется с выбранным пользователем, и
   helper возвращает приложение на главную.

Для `SUBSCRIBED_USER`, `MEMBER_USER` и `RABBIT_HOLE_USER` helper'ы сейчас проще:
они выбирают пользователя через selector и сразу вызывают
`_ensure_home_state_by_phone`, то есть перезапускают приложение и проходят auth
до ожидаемого `HomeState`.

## `ensure_test_user_session`

`ensure_test_user_session` используется там, где один test file проверяет один и
тот же экран под разными user scenarios, например Bookings или Stats entrypoints.

Алгоритм:

1. Тест сам выбирает `context = MobileTestUserSelector(db).select_or_skip(...)`.
2. `ensure_test_user_session` проверяет tabbar через
   `_restart_app_when_tabbar_missing`.
3. Если после первичной проверки или одного restart tabbar виден, helper
   открывает профиль через `BottomNav.open_profile`.
4. Телефон из профиля сравнивается с `context.phone` по последним 10 цифрам.
5. Если телефон совпадает, текущая сессия переиспользуется, и helper возвращает
   `profile.nav`.
6. Если tabbar не появился, профиль не открылся или телефон другой, запускается
   `run_auth_to_home(mobile_driver, context.phone, expected_state=...)`.
7. После auth helper возвращает новый `BottomNav(mobile_driver)`.

### Lifecycle внутри `ensure_test_user_session`

Текущий flow сначала определяет состояние приложения и только потом решает,
нужен ли restart или повторная авторизация:

1. Helper вызывает `_detect_startup_app_state`.
2. Если открыт `PREVIEW` или `PHONE_AUTH`, сразу запускается
   `run_auth_to_home(..., context.phone, expected_state=...)`.
3. Если открыт `SMS_CODE`, helper не вводит код для неизвестного номера:
   сначала выполняет `reset sms auth state`, затем авторизуется под
   `context.phone`.
4. Если виден tabbar или известный Home state, helper открывает профиль через
   `BottomNav.open_profile` и сверяет телефон с `TestUserContext`.
5. Если телефон совпал, текущая сессия переиспользуется.
6. Если телефон другой, helper сначала пробует UI logout из профиля, затем
   запускает `run_auth_to_home` под нужным пользователем.
7. Если UI logout не найден или не сработал, используется `clearApp` fallback.
8. Если состояние приложения неизвестно, helper один раз перезапускает
   приложение и коротко ждёт известное состояние через
   `wait app state after restart`.
9. Если после restart состояние всё ещё `UNKNOWN`, helper печатает диагностику
   и уходит в `clearApp` + auth fallback.

`SMS_CODE` не считается безопасной точкой продолжения auth для нового
`context.phone`, потому что экран может относиться к другому номеру.

### Состояния startup flow

`ensure_test_user_session` принимает решение по одному из состояний:

- авторизованный tabbar;
- известный Home state (`HOME_NEW_USER`, `HOME_RABBIT_HOLE`,
  `HOME_SUBSCRIBED`, `HOME_MEMBER`);
- `PREVIEW`;
- `PHONE_AUTH`;
- `SMS_CODE`;
- `UNKNOWN`/timeout с понятной диагностикой.

Цель такого flow: меньше ложных relogin, меньше лишних restart и более понятные
mobile-ui логи.

## Как определяется, что пользователь уже авторизован

Авторизованный shell определяется не по Home screen, а по нижней навигации:
`is_authorized_shell_visible` проверяет видимость всех четырех text-tab:

- `BottomNav.TAB_MAIN`
- `BottomNav.TAB_BOOKINGS`
- `BottomNav.TAB_STATS`
- `BottomNav.TAB_PROFILE`

Проверка временно ставит implicit wait в `0`, чтобы отсутствие tabbar не
замедляло старт теста. После проверки implicit wait возвращается к
`IMPLICIT_WAIT`.

## Логи и диагностика

Если выставить `MOBILE_UI_LOGS=1`, selector и session helpers печатают timing
логи:

```bash
pytest tests/mobile/... -v -s --mobile-ui-logs
```

Полезные точки в логах:

- `select_or_skip <SCENARIO>` - выбор пользователя.
- `cache hit`, `cache miss`, `cache invalid`, `cache append` - работа cache.
- `detect authorized shell` - первичная проверка tabbar.
- `restart app` - один восстановительный перезапуск приложения.
- `wait app state after restart` - ожидание известного состояния после restart.
- `open profile for session check` - проверка текущей сессии через профиль.
- `logout current user` - выход из профиля, если открыт другой пользователь.
- `reset sms auth state` - выход с экрана SMS-кода перед auth под нужным номером.
- `clear app data after logout fallback` - fallback, если UI logout не сработал.
- `run auth from ensure_test_user_session` или `run auth to home` - fallback на
  очистку данных и OTP-авторизацию.

Пример fallback при неизвестном состоянии:

```text
[mobile-ui] START detect startup app state
[mobile-ui] DONE detect startup app state: 0.05s
ℹ️ Известное состояние приложения не найдено, перезапускаем приложение
[mobile-ui] START restart app
[mobile-ui] DONE restart app: 4.02s
[mobile-ui] START wait app state after restart
[mobile-ui] DONE wait app state after restart: 4.00s
⚠️ Не удалось распознать состояние приложения после restart: package=..., activity=...
[mobile-ui] START run auth from ensure_test_user_session
```

После успешного restart лог показывает найденное состояние:

```text
[mobile-ui] START wait app state after restart
[mobile-ui] detected app state: tabbar
[mobile-ui] DONE wait app state after restart: 1.20s
```

или:

```text
[mobile-ui] START wait app state after restart
[mobile-ui] detected app state: preview
[mobile-ui] DONE wait app state after restart: 0.80s
```

## Важные ограничения

- Cache не является источником истины. Каждый cache-hit валидируется через
  MongoDB перед использованием.
- Один отсутствующий tabbar приводит максимум к одному restart в startup guard.
  Если tabbar не появился после restart, helper продолжает существующий auth-flow.
- `POTENTIAL_USER` должен соответствовать состоянию mobile `new_user`: одной
  роли `users.role="potential"` недостаточно, важны связанные записи и отсутствие
  конфликтующих состояний.
- Helpers не содержат локаторов экранов, кроме использования page objects и
  `BottomNav`; выбор и проверка пользователя остаются orchestration-логикой.
