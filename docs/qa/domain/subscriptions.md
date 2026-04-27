# Subscriptions

## Назначение

Этот документ фиксирует, как текущая автоматизация различает:

- `абонементы`
- `подписки` / `recurrent`

Это QA-справка по текущему репозиторию, а не формальная бизнес-спецификация.
Если терминология в коде, тестах или базе местами смешивается, источником истины
для этого документа считаются уже существующие тесты, page objects, repositories
и backend checks.

## Рабочая модель в проекте

В текущем проекте удобно использовать такую QA-модель:

- `абонемент` - обычный service product / membership, который в mobile-логике
  ближе всего к состоянию `HomeState.MEMBER`
- `подписка` / `recurrent` - одна и та же сущность: рекуррентная подписка с
  автосписанием, которая в mobile-логике ближе всего к состоянию
  `HomeState.SUBSCRIBED`

Дополнительное доменное уточнение:

- подписка определяется через `subscriptions.isRecurrent=true`
- `membershipFee` может быть и у подписки, и у обычного абонемента, но смысл
  поля разный:
  у абонемента это разовая покупка абонемента, у подписки это ежемесячное
  списание
- у подписки есть `joinFee` - разовая вступительная оплата при подключении
  продукта, и это отличительный признак подписки

Важно:

- В репозитории слово `subscription` может использоваться широко, но в рамках
  этой QA-справки `subscription` и `recurrent` считаются одним и тем же
  продуктовым типом.
- Для QA важнее не название само по себе, а то, в каком состоянии приложения,
  коллекции и бизнес-правиле эта сущность участвует.

## Где это видно в mobile

Ключевой ориентир для mobile-части - `HomeState` в
`src/pages/mobile/home/home_state.py`.

| Home state | Как понимать в QA |
|---|---|
| `NEW_USER` | У пользователя нет активного релевантного продукта для home dashboard |
| `SUBSCRIBED` | У пользователя есть активная подписка |
| `MEMBER` | У пользователя есть активный абонемент / service product |
| `RABBIT_HOLE` | Отдельный сценарий Rabbit Hole, не равен обычной подписке |

Связанные content classes:

- `src/pages/mobile/home/content/home_subscribed_content.py`
- `src/pages/mobile/home/content/home_member_content.py`
- `src/pages/mobile/home/content/home_new_user_content.py`

См. также: [[mobile-page-states]].

## Где это лежит в данных

Ниже не полная схема БД, а QA-карта основных коллекций, которые уже участвуют в
проверках.

### `usersubscriptions`

Основная коллекция для пользовательских подписок / абонементов в текущих
backend-репозиториях и валидаторах.

Как уже используется:

- поиск активной подписки: `find_users_with_active_subscription`
- поиск новых подписок: `get_new_subscriptions`
- поиск первой подписки пользователя: `get_first_time_subscribers`

Файл:

- `src/repositories/subscriptions_repository.py`

Практически важно для QA:

- активность обычно определяется через `isActive=True` и `isDeleted=False`
- в части сценариев однодневные продукты и детские записи дополнительно
  отфильтровываются
- welcome/inactive push checks опираются именно на эту коллекцию

### `subscriptions`

Коллекция планов и метаданных subscription products.

Как уже используется:

- загрузка названий и интервалов планов
- сопоставление transaction -> plan
- агрегация отчётов по планам

Практически важно для QA:

- backend checks по бонусам и access type смотрят на длительность плана
  (`interval`) и его классификацию
- в отчётах часто нужен human-readable plan label, а не только id
- если нужно подтвердить, что речь именно о подписке, сначала проверяйте
  `subscriptions.isRecurrent`
- в платёжных сценариях полезно отдельно фиксировать, проверяем ли мы
  ежемесячный `membershipFee` или разовый `joinFee`
- если нужно отличить подписку от обычного абонемента, `membershipFee` сам по
  себе недостаточен; полезнее смотреть на `subscriptions.isRecurrent` и наличие
  `joinFee`
- при анализе `membershipFee` всегда уточняйте контекст продукта: для
  абонемента это разовая покупка, для подписки это ежемесячное списание

### `transactions`

Главная коллекция платежных сценариев.

Как уже используется:

- `productType` отделяет разные типы продуктов
- для темы subscriptions особенно важны subscription/recurrent products
- правила бонусов и проверок оплаты читаются именно отсюда

Практически важно для QA:

- часть проверок может отдельно фильтровать subscription/recurrent сценарии по
  типу транзакции или productType

### `userbonuseshistories`

Источник истины для бонусных начислений и списаний.

Как уже используется:

- `type=SUBSCRIPTION` для бонусов за покупку subscription products
- `type=PAY` для подтверждения списания бонусов при оплате

Практически важно для QA:

- наличие transaction само по себе не доказывает корректность бонусной логики
- для subscription-покупок нужно проверять и transaction, и соответствующую
  запись в `userbonuseshistories`

### `accesscontrols`

Источник истины для фактических входов в клуб.

Как уже используется:

- для subscription entry checks ожидается `accessType=subscription`
- это отдельная логика от входов по `visits`

Практически важно для QA:

- если продукт относится к обычной подписке / абонементу, входы должны
  классифицироваться не как `visits`, а как `subscription`

### `rabbitholev2`

Отдельная доменная зона для Rabbit Hole flow.

Практически важно для QA:

- не смешивать Rabbit Hole subscriptions с обычными membership/subscription
  сценариями без явного основания в коде
- в `test_forbidden_types_no_bonus_spend.py` также отдельно фигурирует
  `rabbitHoleV2`

## Какие проверки уже есть

### Mobile

- `tests/mobile/flows/rabbit_hole/new_client_buy_rh.py`
  Проверяет отдельный flow покупки Rabbit Hole и backend-следы этой покупки.
- `tests/unit/mobile/home/test_home_rabbit_hole_state.py`
  Проверяет, что home state не путает Rabbit Hole и другие состояния.
- `tests/unit/mobile/helpers/test_screen_detection_home_states.py`
  Проверяет корректное различение home states.

### Backend: subscriptions и access

- `tests/backend/payments/test_subscription_access_type.py`
  Проверяет, что входы по нерекуррентным подпискам записываются как
  `accesscontrols.accessType=subscription`.
- `tests/backend/test_subscription_gaps.py`
  Ищет большие разрывы между `created_at` и `startDate` у подписок.

### Backend: бонусы и платежи

- `tests/backend/payments/bonuses/test_subscription_bonus_accrual.py`
  Проверяет начисление `SUBSCRIPTION`-бонусов по типу и сумме.
- `tests/backend/payments/bonuses/test_deduction_limits_by_plan.py`
  Проверяет лимиты списания бонусов по длительности плана.
- `tests/backend/payments/bonuses/test_forbidden_types_no_bonus_spend.py`
  Проверяет, что запрещённые `productType`, включая `recurrent`, не списывают
  бонусы.
- `tests/backend/payments/test_recent_transactions.py`
  Используется как monitoring по recent transactions, включая группировку
  recurrent-транзакций.

### Backend: notifications

- `tests/backend/notifications/test_welcome_push.py`
  Использует first-time subscriptions как основу eligibility.
- `tests/backend/notifications/test_birthday_push.py`
  Ориентируется на пользователей с активной подпиской.
- `tests/backend/notifications/test_inactive_user_push.py`
  Проверяет сценарии, где у пользователя есть подписка, но нет входов после
  покупки.

## Как различать сущности в QA-практике

Используйте такие правила по умолчанию:

- Если речь про mobile home states, различайте `SUBSCRIBED` и `MEMBER` как
  разные состояния, даже если в бизнес-разговоре оба продукта могут называться
  "подпиской".
- Если речь про payment/bonus checks, всегда отдельно уточняйте, охватывает ли
  правило `recurrent`.
- Если речь про eligibility для push или access checks, сначала смотрите, какая
  именно коллекция и какой фильтр реально используются:
  `usersubscriptions`, `subscriptions`, `transactions`, `accesscontrols`.
- Если в новом тесте фигурирует слово `subscription`, полезно сразу зафиксировать,
  это подписка / recurrent или membership / абонемент.

## Типичные ориентиры по файлам

- `src/repositories/subscriptions_repository.py`
- `src/pages/mobile/home/home_state.py`
- `src/pages/mobile/home/content/home_subscribed_content.py`
- `src/pages/mobile/home/content/home_member_content.py`
- `tests/backend/payments/test_subscription_access_type.py`
- `tests/backend/payments/bonuses/test_subscription_bonus_accrual.py`
- `tests/backend/payments/bonuses/test_deduction_limits_by_plan.py`
- `tests/backend/payments/bonuses/test_forbidden_types_no_bonus_spend.py`

## Чего этот документ не утверждает

- Он не вводит новую бизнес-классификацию поверх продукта.
- Он не гарантирует, что терминология `subscription` единообразна во всех
  старых тестах и документах.
- Он не заменяет чтение конкретного test/service/repository, если нужно понять
  точное правило.

## См. также

- [[backend]]
- [[backend-tests]]
- [[mobile]]
- [[mobile-page-states]]
- [[visit-types]]
- [[../../allure/backend_reporting_rules|Backend Allure reporting rules]]
