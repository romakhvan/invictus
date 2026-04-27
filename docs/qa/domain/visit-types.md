# Visit Types

## Назначение

Этот документ описывает, какие типы `visit` уже зафиксированы в текущей
автоматизации Invictus, как они понимаются в бизнесе и по каким полям
определяются в MongoDB.

Документ опирается только на текущий код и тесты репозитория. Если в базе
существуют другие значения `visits.source`, но они не используются в
автоматизации, здесь они не интерпретируются как отдельные бизнес-типы.

## Что считается `visit` в текущей автоматизации

В репозитории слово `visit` используется в двух связанных, но разных смыслах:

- `visits` - отдельная запись о выданном пользователю визите.
- `accesscontrols` - факт реального входа в клуб.

Для бизнес-правил этого проекта важно различать:

- сам визит как entitlement в `visits`;
- фактический вход по визиту в `accesscontrols`;
- покупку визитов как продукта в `transactions`;
- начисление бонуса за посещение в `userbonuseshistories`.

## Бизнес-типы `visit`, которые подтверждены репозиторием

| Бизнес-смысл | Как определяется | Где подтверждено |
|---|---|---|
| Rabbit Hole visit | `visits.type="visit"` и `visits.source="rabbit"` | `src/repositories/visits_repository.py`, mobile Rabbit Hole flow, селектор `RABBIT_HOLE_USER` |
| Guest visit / пользовательский visit | `visits.source="user"` | `tests/backend/guest_visits/test_guest_visits_monitoring.py`, `tests/backend/guest_visits/test_guest_visit_actions_monitoring.py` |
| Вход по визиту | `accesscontrols.type="enter"` и `accesscontrols.accessType="visits"` | `tests/backend/notifications/test_guest_visit_discount_push.py`, payment visit bonus checks |

Важные ограничения:

- `accesscontrols.accessType="visits"` сам по себе означает только вход по визиту.
- Для различения guest visit и других visit-сценариев автоматизация смотрит на
  связанный контекст `visits.source`.
- В текущих payment checks вход по `accessType=visits` с `visits.source=user`
  не считается основанием для начисления `VISIT`-бонуса.

## Как это определяется в базе

### 1. `visits`

Это основная коллекция, где хранится сам выданный пользователю визит.

Ключевые поля:

- `type` - в текущей автоматизации ожидается `visit`
- `source` - бизнес-источник визита, подтверждённые значения: `rabbit`, `user`
- `user` - владелец визита
- `isActive` - визит ещё доступен к использованию
- `isDeleted` - логическое удаление
- `isExpired` - визит истёк
- `created_at`, `updatedAt`, `endDate` - временной контекст
- `club`, `clubUnion` - клубная привязка

Пример:

```json
{
  "_id": "visit_id",
  "user": "user_id",
  "type": "visit",
  "source": "rabbit",
  "club": "club_id",
  "clubUnion": "club_union_id",
  "isActive": true,
  "isDeleted": false,
  "isExpired": false,
  "created_at": "2026-04-20T10:00:00",
  "updatedAt": "2026-04-20T10:00:00",
  "endDate": "2026-05-20T23:59:59"
}
```

Как используется:

- Rabbit Hole flow ожидает, что после покупки пользователю выданы активные
  `visits` с `source="rabbit"`.
- Guest visits monitoring агрегирует `visits` с `source="user"` и делит их на
  used/unused по `isActive`.

### 2. `accesscontrols`

Это коллекция фактических входов в клуб. Для visit-сценариев автоматизация
рассматривает успешные `enter`-события без `err`.

Ключевые поля:

- `type` - ожидается `enter`
- `accessType` - для входа по визиту ожидается `visits`
- `user` - кто вошёл
- `time` - время входа
- `club` - клуб входа
- `err` - если поле есть, такой вход для business checks исключается
- `visits.source` - дополнительный контекст источника визита, если он доступен
  во вложенной записи; если `visits` хранится как ObjectId, payment checks
  дочитывают `source` из коллекции `visits`

Пример:

```json
{
  "_id": "entry_id",
  "user": "user_id",
  "type": "enter",
  "accessType": "visits",
  "club": "club_id",
  "time": "2026-04-23T09:30:00",
  "visits": {
    "source": "user"
  }
}
```

Как используется:

- guest-visit discount push проверяет, что перед отправкой push у получателя был
  успешный `accesscontrols` entry с `accessType=visits`;
- VISIT bonus checks ищут реальные club entries;
- для payment-логики вход по `accessType=visits` и `visits.source=user`
  исключается из visit bonus accrual/coverage.

### 3. `transactions`

`transactions` в текущей автоматизации не определяет `source` самого выданного
визита, но показывает покупку визитов как продукта.

Ключевые поля:

- `productType` - для purchase checks ожидается `visits`
- `status` - в visit price check ожидается `success`
- `userId` - пользователь-покупатель
- `created_at` - время транзакции
- `price`, `paidFor.totalPrice` - фактическая цена
- `paidFor.visits.clubServiceId` - связка с club service
- `paidFor.visits.visitsCount` - количество купленных визитов

Пример:

```json
{
  "_id": "tx_id",
  "userId": "user_id",
  "productType": "visits",
  "status": "success",
  "created_at": "2026-04-23T08:55:00",
  "price": 5000,
  "paidFor": {
    "totalPrice": 5000,
    "visits": {
      "clubServiceId": "club_service_id",
      "visitsCount": 1
    }
  }
}
```

Как используется:

- `tests/backend/payments/test_visit_price.py` идёт от
  `paidFor.visits.clubServiceId` к `clubservices` и `clubs`, чтобы проверить
  ожидаемую цену визита.

### 4. `userbonuseshistories`

Эта коллекция показывает бонусные операции. Для темы `visit` в текущей
автоматизации важен именно `type="VISIT"`.

Ключевые поля:

- `type` - ожидается `VISIT`
- `user` - кому начислен бонус
- `time` - когда начислен бонус
- `amount` - сумма бонуса
- `description` - manual description-based entries исключаются из visit bonus checks

Пример:

```json
{
  "_id": "bonus_id",
  "user": "user_id",
  "type": "VISIT",
  "time": "2026-04-23T09:30:03",
  "amount": 500
}
```

Как используется:

- `test_visit_bonus_accrual` проверяет направление `bonus -> реальный вход`;
- `test_visit_generates_bonus` проверяет направление `visit day -> bonus coverage`.

## Сквозной маппинг по коллекциям

| Сценарий | `visits` | `accesscontrols` | `transactions` | `userbonuseshistories` |
|---|---|---|---|---|
| Rabbit Hole visit | `source="rabbit"` | может приводить к входу по визиту | покупка/выдача проверяется рядом с Rabbit Hole flow | напрямую в текущем репо не описывается |
| Guest visit / пользовательский visit | `source="user"` | вход по визиту: `accessType="visits"` | напрямую не классифицируется как guest visit | для `VISIT`-бонусов такой вход исключается |
| Покупка visit как продукта | не определяет `source` entitlement | не обязательна сама по себе | `productType="visits"` и `paidFor.visits.*` | не обязательна сама по себе |
| Бонус за посещение | не хранится здесь | нужен валидный entry | не участвует напрямую | `type="VISIT"` |

## Как это используется в автотестах и проверках

Основные источники истины в репозитории:

- `src/repositories/visits_repository.py`
  - читает активные Rabbit Hole visits по `type="visit"` и `source="rabbit"`;
- `tests/mobile/flows/rabbit_hole/new_client_buy_rh.py`
  - ожидает, что после сценария Rabbit Hole пользователю выданы 3 `visit`;
- `tests/backend/guest_visits/test_guest_visits_monitoring.py`
  - рассматривает `visits.source="user"` как guest visits;
- `tests/backend/guest_visits/test_guest_visit_actions_monitoring.py`
  - проверяет transfer/use actions вокруг guest visits;
- `tests/backend/notifications/test_guest_visit_discount_push.py`
  - опирается на `accesscontrols.type=enter` и `accessType=visits`;
- `tests/backend/payments/test_visit_price.py`
  - проверяет покупку визитов как продукта через `transactions.paidFor.visits`;
- `tests/backend/payments/bonuses/test_visit_bonus_accrual.py`
  - проверяет `VISIT`-бонусы по отношению к реальным входам;
- `src/services/backend_checks/payments_checks_service.py`
  - содержит правило: `accessType=visits` с `visits.source=user` не является
    eligible entry для `VISIT`-bonus accrual checks.

## Что текущая автоматизация не фиксирует

- Она не описывает все возможные значения `visits.source`, которые могут
  существовать в продовой базе.
- Она не утверждает, что каждая запись в `transactions.productType="visits"`
  обязательно порождает один и тот же бизнес-тип `visit` в коллекции `visits`.
- Она не вводит самостоятельную бизнес-классификацию сверх того, что уже
  подтверждено кодом и тестами.

Если понадобится расширить этот справочник, сначала нужно найти подтверждение в
репозитории: тест, repository query, validator или service logic.
