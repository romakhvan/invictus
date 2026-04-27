# Каталог Backend-Тестов

## Назначение

Этот каталог описывает backend-тесты, которые входят в реальные backend suite:

- `tests_to_run_backend.txt` - gate checks, профиль `backend_check`
- `tests_to_run_backend_monitoring.txt` - monitoring/reporting checks, профиль `backend_monitoring`

Используйте этот файл при добавлении, изменении или ревью backend-тестов.
Run-list файлы остаются исполняемым источником состава suite, а этот каталог
объясняет назначение тестов и ожидаемую форму отчётности.

## Общие Правила

- Backend-тесты используют централизованную фикстуру `db` из `tests/backend/conftest.py`.
- Проверки с временным окном должны использовать `period_days`; значение по умолчанию задаётся в run-list.
- Gate checks должны падать при нарушении бизнес-правил.
- Monitoring checks могут быть report-only, если их цель аналитическая, но должны явно прикладывать summary-данные в Allure.
- Backend Allure-отчёты должны показывать период, количество обработанных записей, количество нарушений и actionable examples.
- Для бизнес-смыслов `visit`, их DB-маппинга и связи между `visits`,
  `accesscontrols`, `transactions` и `userbonuseshistories` см. [[visit-types]].
- Для бизнес-смыслов `subscription`/`recurrent` и membership см. [[subscriptions]].

## Уведомления

### `tests/backend/notifications/test_welcome_push.py`

**Тесты:** `test_welcome_push_with_new_subscriptions`  
**Профиль:** `backend_check`  
**Цель:** Проверить welcome push для пользователей, которые купили первый абонемент и не посещали клуб после покупки.  
**Логика:** Находит последний подходящий notification, проверяет title/text, рассчитывает ожидаемых получателей по подпискам и истории входов в клуб, затем сравнивает фактический `toUsers` с ожидаемыми пользователями после фильтра по возрасту покупки.  
**Данные:** MongoDB `notifications`, `users`, `usersubscriptions`, `accesscontrols`; push validators/repositories.  
**Allure:** Feature/story/title, параметры push metadata, pass criteria, text/HTML summary, language summary, recipient mismatch details, debug instructions при падении.  
**Критерий:** Падает, если push не найден, контент неверный, ожидаемые пользователи отсутствуют или есть missing/extra recipients.

### `tests/backend/notifications/test_birthday_push.py`

**Тесты:** `test_birthday_push_with_active_users`  
**Профиль:** `backend_check`  
**Цель:** Проверить получателей birthday push среди пользователей с активной подпиской.  
**Логика:** Запускает birthday-push validator и ожидает, что он подтвердит корректность контента и eligibility получателей.  
**Данные:** MongoDB notification/subscription/user data через validator.  
**Allure:** Feature/story/title/description/severity/tags и validator attachments, если они формируются.  
**Критерий:** Падает, если birthday push validator возвращает неуспешный результат.

### `tests/backend/notifications/test_guest_visits_push.py`

**Тесты:** `test_guest_visits_push_recipients`  
**Профиль:** `backend_check`  
**Цель:** Проверить получателей guest-visits push по subscription data.  
**Логика:** Загружает recipient ids из `data/Cluster0.notifications.json`, проверяет, что список не пустой, затем через PostgreSQL печатает количество подписок и даты последних подписок для этих пользователей.  
**Данные:** JSON fixture `data/Cluster0.notifications.json`, PostgreSQL `master.mongo.usersubscriptions`, MongoDB user ids.  
**Allure:** Legacy console-heavy test; сейчас нет структурированных Allure steps/attachments. При изменении добавить summary и mismatch attachments.  
**Критерий:** Падает только если список получателей пустой; иначе работает как информационная проверка.

### `tests/backend/notifications/test_guest_visit_discount_push.py`

**Тесты:** `test_guest_visit_discount_push`  
**Профиль:** `backend_check`  
**Цель:** Проверить guest-visit discount push, который отправляется после входа по гостевому визиту.  
**Логика:** Находит подходящие notification documents за период, показывает language/document stats, затем валидирует description/title/text и проверяет, что получатели имели успешные `accesscontrols` entries с `accessType=visits` примерно за 30 минут до отправки push.  
**Данные:** MongoDB `notifications`, `accesscontrols`, users через guest-visit discount push validator.  
**Allure:** Push sent time, matching document counts, checked docs, recipient count, text summary, validation step.  
**Критерий:** Skip, если за период не найден matching notification; падение при ошибке контента или recipient rule validation.

### `tests/backend/notifications/test_inactive_user_push.py`

**Тесты:** `test_inactive_user_push_1_week`, `test_inactive_user_push_2_weeks`, `test_inactive_user_push_4_weeks`, `test_inactive_user_push_8_weeks`  
**Профиль:** `backend_check`  
**Цель:** Проверить inactive-user push notifications для окон неактивности 1, 2, 4 и 8 недель.  
**Логика:** Каждый тест делегирует проверку соответствующему inactive-user push validator и ожидает `true`.  
**Данные:** MongoDB notifications/subscriptions/access history через `inactive_user_push_validator`.  
**Allure:** Legacy console/assertion tests; в файле нет явных Allure decorators или attachments. При изменении добавить параметры окна/периода и recipient mismatch attachments.  
**Критерий:** Падает, если validator возвращает `false`.

## Платежи

### `tests/backend/payments/test_freeze_days_no_duplicate.py`

**Тесты:** `test_freeze_days_no_duplicate`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что один абонемент не замораживается больше одного раза.  
**Логика:** Проверяет успешные `FREEZE_DAYS` transactions по `userSubscriptionID` и ищет подписки с двумя и более freeze transactions за период анализа.  
**Данные:** MongoDB `transactions`, subscription ids; `run_freeze_days_no_duplicate_check`.  
**Allure:** Transaction count, unique subscription count, skipped-without-subscription count, duplicate count, text result или duplicate report.  
**Критерий:** Skip, если нет `FREEZE_DAYS` transactions; падение, если найдены duplicate freezes.

### `tests/backend/payments/test_visit_price.py`

**Тесты:** `test_visits_are_purchased_at_configured_prices`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что visits покупаются по настроенным club-specific или club-type ценам.  
**Логика:** Идёт от `paidFor.visits.clubServiceId` к club service и club type, применяет настроенные цены с fallback rules GO/Girls и сравнивает expected total price с фактической ценой транзакции.  
**Данные:** MongoDB `transactions`, `clubservices`, `clubs`; `run_visit_price_check`.  
**См. также:** [[visit-types]] для общего описания visit-сценариев и их представления в базе.  
**Allure:** Sample period, checked counts, visit transaction counts, violation count, text/HTML summary, by-club table, mismatch patterns, latest violations.  
**Критерий:** Skip, если нет visit transactions или configured matches; падение при price mismatches.

### `tests/backend/payments/test_promo_code_discount.py`

**Тесты:** `test_promo_code_discount_correctness`  
**Профиль:** `backend_check`  
**Цель:** Проверить, что promo-code discounts корректно отражены в transactions.  
**Логика:** Для успешных transactions с `paidFor.discountId` проверяет существование скидки, `isDeleted=false`, активное date window и математику discounted price для subscription transactions.  
**Данные:** MongoDB `transactions`, `discounts`, subscription-related data; `run_promo_code_discount_check`.  
**Allure:** Promo transaction count, unique discount count, violation count, text result или violation report.  
**Критерий:** Skip, если нет promo-code transactions; падение при missing/deleted/inactive discounts или price mismatches.

### `tests/backend/payments/test_internal_error_transactions.py`

**Тесты:** `test_no_internal_error_transactions`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что payment transactions со статусом `internalError` отсутствуют.  
**Логика:** Ищет transactions за период анализа, группирует найденные ошибки по клубу и product type, любое наличие internal server payment error считает нарушением.  
**Данные:** MongoDB `transactions`, club/product grouping через reporting helpers.  
**Allure:** Internal-error count, affected clubs, result report, transaction report, productType breakdown.  
**Критерий:** Pass при нуле internal errors; падение при любой `internalError` transaction.

### `tests/backend/payments/test_subscription_access_type.py`

**Тесты:** `test_subscription_entry_access_type`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что входы в клуб по нерекуррентным подпискам записываются как `accesscontrols.accessType=subscription`.  
**Логика:** Берёт выборку активных non-recurrent subscriptions, находит валидные club entries в окне действия подписки и проверяет, что каждый релевантный entry имеет `accessType='subscription'`.  
**Данные:** MongoDB `subscriptions`, `usersubscriptions`, `accesscontrols`, `clubs`; `run_subscription_access_type_check`.  
**Allure:** Plan/subscription/user/entry counts, in-window/outside-window counts, no-clubId diagnostics, violation counts, summary, by-club и by-plan reports, violation details.  
**Критерий:** Skip, если отсутствуют plans, active subscriptions или entries; падение при entries с неверным access type.

## Бонусы

### `tests/backend/payments/bonuses/test_kyrgyzstan_no_bonuses.py`

**Тесты:** `test_kyrgyzstan_no_bonuses_spent`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что бонусы не используются в успешных Kyrgyzstan transactions.  
**Логика:** Делает PROD sanity check по известной транзакции, затем ищет успешные KG transactions с `bonusesSpent != null` за период анализа.  
**Данные:** MongoDB `transactions`; known Kyrgyzstan country id.  
**Allure:** Violation attachment, если найдены KG bonus-spend transactions.  
**Критерий:** Падает, если sanity transaction не найдена или любая KG transaction использует бонусы.

### `tests/backend/payments/bonuses/test_visit_bonus_accrual.py`

**Тесты:** `test_visit_bonus_accrual`, `test_visit_generates_bonus`  
**Профиль:** `backend_check`  
**Цель:** Проверить начисление VISIT-бонусов в двух направлениях: от бонуса к реальному входу и от реального входа к наличию бонуса.
**Allure titles:** `VISIT-бонусы начисляются только за реальные входы` и `Каждый eligible вход в клуб покрыт VISIT-бонусом`.

**Общее правило данных:** Оба теста работают с автоматическими `userbonuseshistories.type="VISIT"` за период анализа и исключают ручные/служебные записи с `description`. Валидный вход берётся из `accesscontrols` по пользователю, где `type="enter"`, нет поля `err`, `accessType!="staff"` и `time` попадает в анализируемое окно. Для входов с `accessType="visits"` source определяется либо из вложенного `accesscontrols.visits.source`, либо из связанного документа `visits` по ObjectId. Если source равен `user`, это купленный пользовательский визит, который не является основанием для VISIT-бонуса.

**`test_visit_bonus_accrual`: bonus -> accesscontrol**
**Allure title:** `VISIT-бонусы начисляются только за реальные входы`.

- Берёт последние `VISIT_BONUS_SAMPLE_SIZE` VISIT-бонусов из `userbonuseshistories`, отсортированные по `time` по убыванию.
- Для этих бонусов собирает пользователей и временное окно от самого раннего до самого позднего bonus time с допуском `VISIT_BONUS_TIME_TOLERANCE_SEC` секунд в обе стороны.
- Загружает `accesscontrols` для этих пользователей в расширенном окне и оставляет только eligible entries.
- Матчит бонус к входу по паре `user + time bucket`; допускается небольшое расхождение времени в пределах tolerance.
- Отдельно проверяет ограничение “не больше одного VISIT-бонуса на пользователя в день” по ключу `user + bonus.time.date()`.
- Отвечает на вопрос: нет ли лишних или невалидных VISIT-бонусов.
- Нарушения:
  - `duplicate_days` - у пользователя больше одного VISIT-бонуса за одну дату;
  - `missing_visit_bonuses` - VISIT-бонус есть, но matching eligible `accesscontrols` entry не найден.

**`test_visit_generates_bonus`: accesscontrol -> bonus coverage**
**Allure title:** `Каждый eligible вход в клуб покрыт VISIT-бонусом`.

- Берёт выборку пользователей, у которых уже были VISIT-бонусы за период (`VISIT_BONUS_FORWARD_SAMPLE_USERS`).
- Для этих пользователей загружает VISIT-бонусы с начала календарного дня нижней границы периода и все eligible `accesscontrols` entries за период.
- Строит множество `bonus_days = (user, bonus.time.date())` и сравнивает его с днями реальных входов.
- Если у пользователя есть eligible вход в клуб в дату, но в `bonus_days` нет такой пары, это нарушение coverage.
- Каждое нарушение содержит конкретный `accesscontrolId` (`accesscontrols._id`), дату и пользователя, чтобы можно было сразу открыть проблемный вход.
- Отвечает на вопрос: нет ли реальных eligible входов, за которые бонус не начислился.

**Данные:** MongoDB `userbonuseshistories`, `accesscontrols`; helper layer `run_visit_bonus_accrual_check` и `run_visit_bonus_coverage_check`.  
**См. также:** [[visit-types]]; отдельное правило про `accessType=visits` и `visits.source=user` описано там же.  
**Allure:**  

- `test_visit_bonus_accrual` показывает количество проверенных бонусов, найденных валидных входов, дублей за день, бонусов без посещения и общий счётчик нарушений.
- При нарушениях прикладываются `Итог проверки VISIT-бонусов`, `Нарушения VISIT-бонусов` и `Expected vs Actual`.
- `test_visit_generates_bonus` показывает количество пользователей в выборке, дней с VISIT-бонусами, дней с посещениями и нарушений.
- При coverage-нарушениях attachment `Посещения без VISIT-бонуса` содержит строки вида `date | accesscontrolId=... | user=... | expected=VISIT-бонус | actual=нет бонуса`.

**Критерий:** Skip, если нет релевантных VISIT-бонусов или пользователей с VISIT-бонусами за период. Падение, если найден daily duplicate, бонус без matching входа или eligible вход без VISIT-бонуса за день.

### `tests/backend/payments/bonuses/test_forbidden_types_no_bonus_spend.py`

**Тесты:** `test_forbidden_types_no_bonus_spend`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что product types без поддержки оплаты бонусами никогда не списывают бонусы.  
**Логика:** Проверяет настроенные forbidden `productType`: `recurrent`, `rabbitHoleV2`, `saveCard`, `fillBalance`, `freezing` на наличие `bonusesSpent > 0`.  
**Данные:** MongoDB `transactions`; `FORBIDDEN_BONUS_PRODUCT_TYPES`.  
**Allure:** Forbidden type count, violation count, text result или grouped violation report by productType.  
**Критерий:** Падает, если любой forbidden product type имеет bonus spending.

### `tests/backend/payments/bonuses/test_deduction_limits_by_plan.py`

**Тесты:** `test_deduction_limits_by_plan`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что лимиты списания бонусов соблюдаются по длительности подписки.  
**Логика:** Проверяет успешные transactions с `bonusesSpent > 0` и subscription products, исключая recurrent payments, по лимитам для годовых, полугодовых, трёхмесячных и месячных планов.  
**Данные:** MongoDB `transactions`, `subscriptions`; `run_bonus_deduction_limits_check`.  
**Allure:** Checked transaction count, loaded plan count, violation count, result или violation report.  
**Критерий:** Skip, если нет релевантных transactions; падение, если bonus-spend percentage превышает лимит плана.

### `tests/backend/payments/bonuses/test_bonus_deduction_consistency.py`

**Тесты:** `test_bonus_deduction_consistency`  
**Профиль:** `backend_check`  
**Цель:** Убедиться, что каждое списание бонусов в transaction отражено в `userbonuseshistories`.  
**Логика:** Для каждой успешной transaction с `bonusesSpent > 0` ожидает matching `type=PAY` bonus history record для того же пользователя с `amount=-bonusesSpent` в допустимом временном окне.  
**Данные:** MongoDB `transactions`, `userbonuseshistories`; `run_bonus_deduction_consistency_check`.  
**Allure:** Transaction count, PAY record count, violation count, result или missing-PAY report.  
**Критерий:** Skip, если нет bonus-spend transactions; падение, если matching PAY records отсутствуют.

### `tests/backend/payments/bonuses/test_subscription_bonus_accrual.py`

**Тесты:** `test_subscription_bonus_accrual`  
**Профиль:** `backend_check`  
**Цель:** Проверить type и amount бонусов за покупку подписки.  
**Логика:** Для recent subscription purchases годовые и полугодовые планы должны иметь `SUBSCRIPTION` bonus records с ожидаемыми amounts, а месячные/трёхмесячные/recurrent plans не должны получать subscription bonuses.  
**Данные:** MongoDB `transactions`, `subscriptions`, `userbonuseshistories`; `run_subscription_bonus_accrual_check`.  
**Allure:** Transaction count, loaded plan count, found subscription-bonus count, total violation count, result или violation report.  
**Критерий:** Skip, если нет subscription purchases; падение при missing, wrong-amount или unexpected subscription bonuses.

## Тренировки

### `tests/backend/trainings/test_personal_trainings_consistency.py`

**Тесты:** `test_personal_trainings_count_consistency`  
**Профиль:** `backend_check`  
**Цель:** Проверить, что остаток персональных тренировок в `userserviceproducts` согласован с билетами, историей и фактическими списаниями.  
**Логика:** Берёт активные `userserviceproducts` типа `SPECIALIST` по текущему фильтру периода или конкретному `SPECIFIC_USP_ID`. Через `serviceProduct` подтягивает `serviceproducts.title`, `type`, `trainingType` и исключает продукты, где title содержит `Inbody` без учёта регистра. Для каждой оставшейся записи сравнивает:

- `userserviceproducts.count`;
- количество активных неиспользованных `trainingtickets`;
- `currentCount` последней записи `userserviceproductshistories`;
- формулу списаний `trainingsessions + CANCEL_BOOKING без восстановления == initialCount - count`.

Если в `userserviceproductshistories` есть ручное изменение `type="UPDATE"` с `changes.field="count"`, такая ошибка отделяется от обычных расхождений.

**Данные:** MongoDB `userserviceproducts`, `serviceproducts`, `trainingtickets`, `userserviceproductshistories`, `trainingsessions`.  
**Allure:** Summary с общим количеством проверенных записей, OK/FAIL, обычными расхождениями и расхождениями после ручного изменения count. Ошибки прикладываются text-таблицами и HTML-таблицами. HTML-таблицы сгруппированы по правилам ошибки: `count != active trainingtickets`, `count != latest history currentCount`, `active trainingtickets != latest history currentCount`, `trainingsessions + cancel_not_restored != initialCount - count`. Внутри каждой rule-секции есть сворачиваемые группы по `serviceproducts.trainingType`; одна USP-запись может отображаться в нескольких rule-секциях. В начале HTML есть rule summary и summary по `duo`, `mg`, `pt`, `trio`: количество ошибок и последний `updated_at`. В таблицах показываются `Title`, `SP Type`, USP/user ids, counts, expected/actual по правилу, tickets/history/sessions/cancel-not-restored, manual history id/change/date и даты USP.  
**Критерий:** Падает, если найдены любые расхождения: как обычные, так и связанные с ручным изменением `count`. Skip, если по заданным фильтрам нет активных записей для проверки.

## Мониторинг

### `tests/backend/payments/test_webkassa_monitoring.py`

**Тесты:** `test_webkassa_status_by_clubs`  
**Профиль:** `backend_monitoring`  
**Цель:** Мониторить статус создания WebKassa receipts по клубам.  
**Логика:** Анализирует transactions за настроенный период, джойнит receipt ids из `webKassaIds`, группирует receipt success/error/missing states по клубам и подсвечивает проблемные clubs/transactions.  
**Данные:** MongoDB `transactions`, `webkassas`, `clubs`; см. также `docs/qa/domain/webkassa.md`.  
**Allure:** Period summary, processed transaction counts, club statistics, examples of failed/missing receipts, HTML/text reports.  
**Критерий:** Monitoring check падает только по своей внутренней threshold/assertion logic; основная ценность - operational reporting.

### `tests/backend/payments/test_recent_transactions.py`

**Тесты:** `test_recent_transactions_grouped_by_instalment_type`  
**Профиль:** `backend_monitoring`  
**Цель:** Показать recent non-POS transactions с группировкой по `instalmentType`.  
**Логика:** Использует фиксированное local start time, исключает `source='pos'`, группирует transactions по installment type, печатает status totals, recurrent success distribution и failed transaction samples.  
**Данные:** MongoDB `transactions`.  
**Allure:** Legacy console-only monitoring; structured Allure attachments отсутствуют. При изменении добавить summary и grouped HTML tables.  
**Критерий:** Использует assertion на non-negative count; фактически report-only.

### `tests/backend/payments/bonuses/test_bonus_usage_distribution.py`

**Тесты:** `test_bonus_usage_distribution`  
**Профиль:** `backend_monitoring`  
**Цель:** Мониторить распределение bonus usage по доле от полной стоимости transaction.  
**Логика:** Загружает успешные transactions с `bonusesSpent > 0`, считает `full_cost=price+bonusesSpent`, раскладывает transactions по корзинам 0-10% ... 90-100% и группирует по `productType`.  
**Данные:** MongoDB `transactions`, `subscriptions`.  
**Allure:** Bonus transaction count, configuration text, HTML tables by bucket/product type и overall productType summary.  
**Критерий:** Skip, если нет bonus-spend transactions; не падает из-за значений распределения.

### `tests/backend/payments/bonuses/test_bonus_usage_monitoring.py`

**Тесты:** `test_bonus_usage_monitoring`  
**Профиль:** `backend_monitoring`  
**Цель:** Мониторить использование бонусов по клиентам и купленным продуктам.  
**Логика:** Агрегирует успешные transactions с `bonusesSpent > 0`, показывает unique clients, total spent bonuses, products, product types и transaction details.  
**Данные:** MongoDB `transactions` и product/subscription references через `run_bonus_usage_monitoring`.  
**Allure:** Transaction count, unique client count, total bonuses spent, text summary, HTML tables for clients, products, product types и transactions.  
**Критерий:** Skip, если нет bonus-spend transactions; иначе report-only.

### `tests/backend/guest_visits/test_guest_visit_actions_monitoring.py`

**Run-list note:** `tests_to_run_backend_monitoring.txt` сейчас указывает на `tests/backend/notifications/test_guest_visit_actions_monitoring.py`, но реальный файл находится в `tests/backend/guest_visits/test_guest_visit_actions_monitoring.py`.  
**Тесты:** `test_guest_visit_actions_monitoring`  
**Профиль:** `backend_monitoring`  
**Цель:** Мониторить консистентность transfer/use actions гостевых визитов.  
**Логика:** Загружает `userguestvisitactions` за период, разделяет `TRANSFER` и `USE`, проверяет relation integrity с visits/subscriptions/users, записывает hard anomalies и более мягкие monitoring notes, показывает senders/receivers summary.  
**Данные:** MongoDB `userguestvisitactions`, `visits`, `usersubscriptions`, `users`.  
**Allure:** Action totals, transfer/use/source breakdowns, user totals, monitoring-note tables, anomaly summary/sample tables.  
**Критерий:** Skip, если actions отсутствуют; падение при hard anomalies.

### `tests/backend/guest_visits/test_guest_visits_monitoring.py`

**Run-list note:** `tests_to_run_backend_monitoring.txt` сейчас указывает на `tests/backend/notifications/test_guest_visits_monitoring.py`, но реальный файл находится в `tests/backend/guest_visits/test_guest_visits_monitoring.py`.  
**Тесты:** `test_guest_visits_monitoring`  
**Профиль:** `backend_monitoring`  
**Цель:** Мониторить клиентов с guest visits, созданными из `source=user`.  
**Логика:** Агрегирует `visits` по пользователям, разделяет used и unused guest visits, обогащает top clients последней подпиской, последним успешным entry и role.  
**Данные:** MongoDB `visits`, `usersubscriptions`, `accesscontrols`, `users`.  
**См. также:** [[visit-types]] для сквозного описания guest visits и входов по ним.  
**Allure:** HTML table с top clients по used и unused guest visits.  
**Критерий:** Skip, если нет source=user visits или reportable rows; иначе report-only.
