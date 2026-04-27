# Test Data

Для бизнес-смыслов `visit`, различий между `visits.source`, фактом входа в
`accesscontrols`, покупкой визитов в `transactions` и `VISIT`-бонусами см.
[[visit-types]].

## Источники данных

- `.env`
- MongoDB
- PostgreSQL
- pytest fixtures
- repositories
- mobile test users
- helper modules

## Конфигурация

MongoDB:

```env
MONGO_USER_PROD=
MONGO_PASSWORD_PROD=
MONGO_HOSTS_PROD=
MONGO_REPLICA_SET_PROD=
MONGO_DB_NAME_PROD=

MONGO_USER_STAGE=
MONGO_PASSWORD_STAGE=
MONGO_HOSTS_STAGE=
MONGO_REPLICA_SET_STAGE=
MONGO_AUTH_SOURCE_STAGE=
MONGO_DB_NAME_STAGE=
```

PostgreSQL:

```env
POSTGRES_HOST=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DATABASE=
```

## Repositories

Доступ к данным должен идти через:

```text
src/repositories/
```

## Mobile test users

Mobile-тесты должны получать пользователей через
`src/repositories/mobile_test_users_repository.py`. Селектор возвращает
`TestUserContext` с телефоном, `user_id`, ожидаемым состоянием главной и
источником выбора данных. Низкоуровневые критерии выбора находятся в
`src/repositories/users_repository.py`.

### `POTENTIAL_USER`

- Role / type: `potential`
- Source:
  - MongoDB STAGE
  - `users`
  - `usermetadatas`
  - `rabbitholev2`
  - `visits`
  - `usersubscriptions`
  - `accesscontrols`
- Selection criteria:
  - `users.role = "potential"`
  - `firstName` заполнен
  - есть запись в `usermetadatas` по `user` или `userId`
  - нет ни одной записи по `user` или `userId` в `rabbitholev2`
  - нет ни одной записи по `user` или `userId` в `visits`
  - нет ни одной записи по `user` или `userId` в `usersubscriptions`
  - нет ни одной записи по `user` или `userId` в `accesscontrols`
  - любая историческая, inactive, deleted или expired запись в этих коллекциях исключает кандидата
- Expected app state: `HomeState.NEW_USER`
- Expected page states: [[mobile-page-states#HOME_NEW_USER]]
- Used by:
  - `tests/mobile/flows/rabbit_hole/new_client_buy_rh.py`
  - `tests/mobile/navigation/test_navigation_new_user.py`
  - `tests/mobile/navigation/test_bottom_navigation.py`
  - `tests/mobile/home/test_home_entrypoints_new_user.py`
  - `tests/mobile/home/test_home_club_filter.py`
  - `tests/mobile/bookings/test_bookings_entrypoints.py`
  - `tests/mobile/bookings/test_bookings_tabs.py`
  - `tests/mobile/bookings/test_personal_club_filter.py`
- Implementation:
  - Selector: `MobileTestUserScenario.POTENTIAL_USER`
  - Query helper: `get_phone_for_potential_user()`
  - Session helper: `ensure_new_user_on_home_screen()`
- Missing data behavior: `select_or_skip()` skips the test with a clear reason.

### `SUBSCRIBED_USER`

- Role / type: subscribed client
- Source:
  - MongoDB STAGE
  - `usersubscriptions`
  - `users`
- Selection criteria:
  - `usersubscriptions.isActive = true`
  - `usersubscriptions.isDeleted = false`
  - поле `kid` отсутствует
- Expected app state: `HomeState.SUBSCRIBED`
- Expected page states: [[mobile-page-states#HOME_SUBSCRIBED]]
- Used by:
  - Прямых mobile-тестов сейчас нет.
- Covered by:
  - `tests/unit/repositories/test_mobile_test_users_repository.py`
  - `tests/unit/mobile/helpers/test_session_helpers_selector.py`
- Implementation:
  - Selector: `MobileTestUserScenario.SUBSCRIBED_USER`
  - Query helper: `get_phone_for_active_subscription_user()`
  - Session helper: `ensure_subscribed_user_on_home_screen()`
- Missing data behavior: `select_or_skip()` skips the test with a clear reason.

### `RABBIT_HOLE_USER`

- Role / type: Rabbit Hole client without active subscription
- Source:
  - MongoDB STAGE
  - `visits`
  - `users`
  - `usersubscriptions`
- Selection criteria:
  - есть минимум `3` записи в `visits`
  - `visits.type = "visit"`
  - `visits.source = "rabbit"`
  - `visits.isActive = true`
  - `visits.isDeleted = false`
  - `visits.isExpired = false`
  - поле `visits.user` существует
  - у пользователя нет активной записи в `usersubscriptions` с `isActive = true` и `isDeleted = false`
- Expected app state: `HomeState.RABBIT_HOLE`
- Expected page states: [[mobile-page-states#HOME_RABBIT_HOLE]]
- Used by:
  - Прямых mobile-тестов сейчас нет.
- Covered by:
  - `tests/unit/repositories/test_mobile_test_users_repository.py`
  - `tests/unit/repositories/test_users_repository.py`
  - `tests/unit/mobile/helpers/test_session_helpers_selector.py`
- Implementation:
  - Selector: `MobileTestUserScenario.RABBIT_HOLE_USER`
  - Query helper: `get_phone_for_active_rabbit_hole_user()`
  - Session helper: `ensure_rabbit_hole_user_on_home_screen()`
- Missing data behavior: `select_or_skip()` skips the test with a clear reason.

### `MEMBER_USER`

- Role / type: member client
- Source:
  - MongoDB STAGE
  - `userserviceproducts`
  - `users`
- Selection criteria:
  - `userserviceproducts.isActive = true`
  - `userserviceproducts.isDeleted = false`
  - поле `child` отсутствует
- Expected app state: `HomeState.MEMBER`
- Expected page states: [[mobile-page-states#HOME_MEMBER]]
- Used by:
  - Прямых mobile-тестов сейчас нет.
- Covered by:
  - `tests/unit/repositories/test_mobile_test_users_repository.py`
  - `tests/unit/mobile/helpers/test_session_helpers_selector.py`
- Implementation:
  - Selector: `MobileTestUserScenario.MEMBER_USER`
  - Query helper: `get_phone_for_active_service_product_user()`
  - Session helper: `ensure_member_user_on_home_screen()`
- Missing data behavior: `select_or_skip()` skips the test with a clear reason.

### `COACH_USER`

- Role / type: coach
- Source:
  - MongoDB STAGE
  - `coaches`
  - `users`
- Selection criteria:
  - `coaches.isDeleted = false`
  - поле `user` существует
- Expected app state: зависит от режима приложения; может открыться mode selection.
- Expected page states: стабильный page state пока не описан; возможен mode selection, dedicated page objects еще не автоматизированы.
- Used by:
  - Прямых mobile-тестов сейчас нет.
- Covered by:
  - `tests/unit/mobile/helpers/test_session_helpers_selector.py`
- Implementation:
  - Selector: `MobileTestUserScenario.COACH_USER`
  - Query helper: `get_phone_for_coach_user()`
  - Session helper: `ensure_coach_user_on_home_screen()`
- Missing data behavior: `select_or_skip()` skips the test with a clear reason.

### `ONBOARDING_NEW_USER`

- Role / type: new Kazakhstan client
- Source:
  - CLI override: `--onboarding-phone`
  - generated free phone
  - MongoDB STAGE `users`
- Selection criteria:
  - если передан `--onboarding-phone`, используется он
  - иначе ищется свободный номер от `77781000001`
  - выбранного номера нет в `users.phone` или `users.phoneNumber`
  - максимум `100` попыток подбора
- Expected app state: full onboarding, then main screen.
- Expected page flow: [[mobile-page-states#Auth screens]] + onboarding flow + `HomePage`
- Used by:
  - `tests/mobile/onboarding/test_client_onboarding.py`
- Implementation:
  - Selector: `MobileTestUserScenario.ONBOARDING_NEW_USER`
  - Query helper: `get_available_test_phone()`
  - CLI fixture: `onboarding_phone`
- Missing data behavior: `select_or_skip()` skips the test with a clear reason.

### `KYRGYZSTAN_ONBOARDING_NEW_USER`

- Role / type: new Kyrgyzstan client
- Source:
  - CLI override: `--onboarding-phone-kg`
- Selection criteria:
  - `--onboarding-phone-kg` обязателен
  - страна выбирается как `+996`
- Expected app state: full onboarding, then main screen.
- Expected page flow: [[mobile-page-states#Auth screens]] + onboarding flow + `HomePage`
- Used by:
  - `tests/mobile/onboarding/test_client_onboarding_kyrgyzstan.py`
- Implementation:
  - Selector: `MobileTestUserScenario.KYRGYZSTAN_ONBOARDING_NEW_USER`
  - CLI fixture: `onboarding_phone_kg`
- Missing data behavior: `select_or_skip()` skips the test with a clear reason.

Связанные точки в коде:

- `src/repositories/mobile_test_users_repository.py` — сценарии, `MobileTestUserSelector`, `TestUserContext`.
- `src/repositories/users_repository.py` — MongoDB-критерии и нормализация телефона.
- `tests/mobile/conftest.py` — fixtures для mobile-сценариев и CLI override телефонов.
- `tests/mobile/helpers/session_helpers.py` — авторизация под выбранным пользователем и вывод на нужное состояние главной.

Правила:

- не хардкодить реальные номера в тестах;
- использовать `MobileTestUserSelector` вместо прямых DB-запросов в mobile-тестах;
- использовать `select_or_skip()` для сценариев, где отсутствие подходящих данных должно превращаться в понятный skip;
- передавать новые onboarding-номера через `--onboarding-phone` или `--onboarding-phone-kg`, если нужен конкретный номер;
- не логировать и не прикладывать к отчетам лишние персональные данные.

## Visits в MongoDB

Кратко:

- `visits` хранит сам выданный пользователю визит;
- `accesscontrols` хранит факт входа в клуб;
- `transactions` хранит покупку визитов как продукта;
- `userbonuseshistories` хранит бонусные последствия visit-сценариев.

Подробный бизнес-справочник и DB-маппинг:

- [[visit-types]]

## Правила

- не хранить реальные секреты в репозитории
- не писать прямые DB-запросы в UI-тестах
- явно проверять наличие данных перед проверкой
- использовать `pytest.skip()` с понятной причиной, если данных нет
- маскировать персональные данные в отчетах
- не менять production-like данные без отдельного согласования

## Шаблон описания данных

```markdown
## Test data

- Source:
- Collections/tables:
- Required state:
- Created data:
- Cleanup:
- Risks:
```

## См. также

- [[backend]]
- [[mobile]]
- [[best-practices]]
