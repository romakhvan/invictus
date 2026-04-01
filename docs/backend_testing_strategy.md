# Стратегия тестирования backend (MongoDB)

## Назначение

Backend тесты проверяют **бизнес-правила и консистентность данных** напрямую в MongoDB, минуя UI. Инструменты: `pymongo`, `pytest`, `allure`.

## Окружения

| Фикстура | БД | Когда использовать |
|----------|----|--------------------|
| `db` | MongoDB **STAGE** | Функциональные проверки, coach wallet, разработка |
| `prod_db` | MongoDB **PROD** | Проверки консистентности production-данных |

Обе фикстуры объявлены в `tests/backend/conftest.py` с `scope="session"`.

Большинство активных тестов работают с **PROD** — проверяют реальные данные на соответствие бизнес-правилам.

## Структура тестов

Тесты организованы **по функциональным областям**. Каждая область — отдельная папка.

```
tests/backend/
├── conftest.py                          # Фикстуры db (STAGE) и prod_db (PROD)
├── notifications/                       # Push-уведомления
│   ├── test_welcome_push.py             # Новые подписчики без входа 1 неделю
│   ├── test_birthday_push.py            # День рождения + активная подписка
│   ├── test_guest_visits_push.py        # Гостевые визиты (MongoDB + PostgreSQL)
│   └── test_inactive_user_push.py       # Неактивность 1/2/4/8 недель
├── payments/                            # Платежи
│   ├── test_webkassa_monitoring.py      # Мониторинг фискальных чеков (7 дней)
│   ├── test_recent_transactions.py      # Анализ транзакций за текущий день
│   └── bonuses/                         # Правила применения бонусов
│       ├── test_kyrgyzstan_no_bonuses.py    # КГ: бонусы не применяются (PROD) ✅
│       └── test_subscription_bonus_limit.py # Бонусы ≤ 20% от суммы (PROD)
├── trainings/                           # Тренировки
│   └── test_personal_trainings_consistency.py  # Консистентность в 3 коллекциях (PROD) ✅
├── test_coach_wallet.py                 # Баланс кошелька тренера (STAGE)
├── test_statistics_2025.py              # Статистика клиентов за год (PROD)
├── test_rabbitholev2_no_duplicate_users.py  # Дубликаты в RabbitHole (PROD)
├── test_high_frequency_clients_no_subscription.py  # PostgreSQL: частые посетители
└── test_subscription_gaps.py           # Пропуски подписок > 2 месяцев
```

Значком **✅** отмечены тесты, активные в `tests_to_run_backend.txt`.

## Запуск тестов

Backend тесты запускаются через `run_tests.py` и список `tests_to_run_backend.txt`:

```bash
python run_tests.py   # MODE = "backend" в run_tests.py
```

Прямой запуск pytest:

```bash
pytest -m backend -v
pytest tests/backend/trainings/test_personal_trainings_consistency.py -v
```

Флаги по умолчанию (из `tests_to_run_backend.txt`): `-q --tb=no --no-header`.

Формат `tests_to_run_backend.txt`: каждая строка — относительный путь к тесту; после `|` можно указать дополнительные флаги pytest. Закомментированные строки (`#`) не запускаются.

**Правило**: каждый новый тест-файл нужно добавить в `tests_to_run_backend.txt`.

## Репозитории (слой доступа к данным)

Все MongoDB-запросы инкапсулированы в `src/repositories/`. В тестах не должно быть прямых вызовов `db[collection]` — только методы репозиториев.

| Репозиторий | Коллекция | Назначение |
|------------|-----------|-----------|
| `users_repository.py` | users | Поиск по телефону, день рождения, роли |
| `subscriptions_repository.py` | usersubscriptions | Новые подписки, фильтры по датам |
| `transactions_repository.py` | transactions | Платежи, бонусы, группировка |
| `accesscontrols_repository.py` | accesscontrols | Входы в клуб, статистика посещений |
| `notifications_repository.py` | notifications | Push-уведомления по типам |
| `coachwallethistories_repository.py` | coachwallets, coachwallethistories | Кошелёк тренера, история |
| `userserviceproducts_repository.py` | userserviceproducts | Услуги пользователя (тренировки) |
| `rabbitholev2_repository.py` | rabbitholev2 | Подписки RabbitHole |

## Категории тестов

### Payments / Bonuses

Проверяют, что бонусы применяются по правилам:

- **`test_kyrgyzstan_no_bonuses.py`** — в Кыргызстане (`country = ObjectId("67c1a10edd7823df5c8bcace")`) бонусы не должны списываться. Тест ищет успешные транзакции с `bonusesSpent != null`.
- **`test_subscription_bonus_limit.py`** — при покупке абонемента бонусы не должны превышать 20% от стоимости (`bonusesSpent / subscription.price ≤ 0.20`). Период: последние 90 дней.

Оба теста работают с PROD и падают при обнаружении нарушений. Выводят в Allure таблицу нарушений.

### Trainings

- **`test_personal_trainings_consistency.py`** — проверяет, что количество персональных тренировок совпадает в трёх местах:
  - `userserviceproducts.count`
  - количество активных неиспользованных билетов в `trainingtickets`
  - `currentCount` последней записи в `userserviceproductshistories`

  Конфигурируется в верхних строках файла: `DB_ENVIRONMENT`, `SPECIFIC_USP_ID`, фильтры по дате. Вывод в Allure: сводная таблица, HTML-таблица расхождений, полный JSON.

### Notifications

Архитектура: все пуш-тесты используют универсальный валидатор из `src/validators/push_notifications/base.py`. Паттерн:

1. Найти пуш в коллекции `notifications` по описанию.
2. Определить ожидаемых получателей через бизнес-логику (кто по условиям должен был получить).
3. Сравнить фактических (`toUsers`) с ожидаемыми → отчёт по Missing и Extra.

| Тест | Бизнес-правило |
|------|---------------|
| `test_welcome_push.py` | Первая подписка + 7 дней без входа |
| `test_birthday_push.py` | День рождения + активная подписка |
| `test_inactive_user_push.py` | Инактивность 1/2/4/8 недель после последнего входа |
| `test_guest_visits_push.py` | Гостевые визиты (совместно с PostgreSQL) |

### Payments (мониторинг)

- **`test_webkassa_monitoring.py`** — за последние 7 дней проверяет статус фискальных чеков по клубам: `success / error / отсутствует`. Исключает тестовые клубы. Вывод: клубы с проблемами + примеры ошибочных транзакций.
- **`test_recent_transactions.py`** — анализирует транзакции текущего дня с 14:55 UTC+5, группирует по `instalmentType`, выводит примеры `fail`.

### Other

| Тест | Окружение | Суть |
|------|-----------|------|
| `test_coach_wallet.py` | STAGE | 8 мягких проверок (`pytest-check`): баланс = сумма транзакций, комиссии, дубликаты |
| `test_statistics_2025.py` | PROD | Статистика: первые визиты, стрики, потери клиентов, персональные тренировки |
| `test_rabbitholev2_no_duplicate_users.py` | PROD | Дубликаты подписок за 14 дней |
| `test_high_frequency_clients_no_subscription.py` | PostgreSQL | Клиенты с высокой частотой посещений без подписки |
| `test_subscription_gaps.py` | PROD | Записи с пропусками подписок > 2 месяцев |

## Конвенции

- **Конфигурация в верхних строках** — переменные `DB_ENVIRONMENT`, `SPECIFIC_USP_ID`, периоды дат — в начале файла теста для удобного переключения режима.
- **Sanity-check** — тесты с PROD данными проверяют подключение к нужной БД через поиск известной записи (например, `ObjectId("69a98aa3245025ac664f144e")`).
- **Allure attachments** — каждый тест прикрепляет результаты: таблицы нарушений (TEXT + HTML), полный JSON, статистику.
- **Не использовать `db[collection]` в тестах напрямую** — только через методы репозиториев из `src/repositories/`.
- **Мягкие assert** (`pytest-check`) — используются там, где нужно собрать все нарушения, а не остановиться на первом.
