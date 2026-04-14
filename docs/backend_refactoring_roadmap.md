# План постепенного рефакторинга backend-тестов

## Цель

Постепенно превратить backend-набор из смеси тестов, мониторинга и аналитических скриптов в управляемую тестовую платформу с понятными слоями:

- `checks` — проверки бизнес-правил и инвариантов
- `monitoring` — отчёты и наблюдение за продом
- `research` — разовые аналитические сценарии

## Главные проблемы, которые закрываем

- Backend-прогоны по умолчанию ориентированы на `prod`
- В один suite смешаны gate-тесты и непадающие отчёты
- Бизнес-логика и Mongo-запросы зашиты прямо в тестовые файлы
- Много хардкода: даты, ObjectId, исключения клубов, sample user id
- Инфраструктура backend частично размазана между `tests/conftest.py` и `tests/backend/conftest.py`

## Принципы рефакторинга

- Не переписывать всё сразу
- Сначала отделять типы сценариев, потом выносить логику в слои
- Каждый шаг должен быть маленьким и обратимым
- После каждого этапа suite должен оставаться запускаемым
- Все новые backend-проверки писать только по новой схеме

## Целевая структура

```text
tests/
└── backend/
    ├── checks/
    │   ├── payments/
    │   ├── notifications/
    │   └── trainings/
    ├── monitoring/
    │   ├── payments/
    │   └── bonuses/
    ├── research/
    └── conftest.py

src/
├── repositories/
│   ├── payments/
│   ├── notifications/
│   └── trainings/
├── services/
│   ├── backend_checks/
│   ├── monitoring/
│   └── reporting/
└── utils/
    └── allure/
```

## Этап 0. Подготовка и правила

Статус:
- [ ] Зафиксировать текущую структуру и договориться о новых папках
- [ ] Ввести marker-ы `backend_check`, `backend_monitoring`, `backend_research`
- [ ] Запретить добавление новых аналитических сценариев в общий backend suite

Что делаем:
- Обновить `pytest.ini`
- Обновить `tests_to_run_backend.txt`
- Добавить короткие правила в `docs/backend_testing_strategy.md`

Критерий готовности:
- Любой backend-файл можно отнести к одному из трёх типов

## Этап 1. Отделить monitoring от настоящих тестов

Приоритет: очень высокий

Статус:
- [ ] Вынести непадающие сценарии из общего списка запуска
- [ ] Создать отдельный файл запуска для monitoring
- [ ] Сохранить Allure-репорты, но убрать их из gate-прогона

Кандидаты на перенос в `monitoring`:
- `tests/backend/payments/test_recent_transactions.py`
- `tests/backend/payments/bonuses/test_bonus_usage_distribution.py`
- `tests/backend/test_statistics_2025.py`

Что делаем:
1. Создать `tests_to_run_backend_monitoring.txt`
2. Перенести туда явно аналитические сценарии
3. Оставить в `tests_to_run_backend.txt` только проверки, которые реально могут валить прогон по бизнес-правилам

Критерий готовности:
- Основной backend-прогон больше не содержит тестов с форматом “просто распечатать статистику”

## Этап 2. Убрать prod-first поведение

Приоритет: очень высокий

Статус:
- [ ] Сделать `stage` дефолтным окружением для backend checks
- [ ] Оставить `prod` только для monitoring или для явно помеченных сценариев
- [ ] Исправить Environment в Allure для backend-раннера

Что делаем:
- Пересмотреть дефолт в `tests/conftest.py`
- Пересмотреть дефолт в `tests/backend/conftest.py`
- Исправить `run_tests.py`, чтобы окружение в отчёте бралось из реального запуска, а не было всегда `Production`

Критерий готовности:
- Нельзя случайно запустить основной backend suite по продовым данным без явного решения

## Этап 3. Разделить инфраструктуру pytest по доменам

Приоритет: высокий

Статус:
- [ ] Убрать backend-специфику из общего `tests/conftest.py`
- [ ] Оставить backend-фикстуры только в `tests/backend/conftest.py`
- [ ] Свести к одному источнику правды для `db`, `backend_env`, `period_days`

Что делаем:
- Перенести всё backend-специфичное в `tests/backend/conftest.py`
- Оставить в корневом `tests/conftest.py` только truly shared hooks
- Проверить, что mobile/web не зависят от backend fixture-логики

Критерий готовности:
- Для backend-инфраструктуры есть один понятный entrypoint

## Этап 4. Ввести настоящий repository/service слой

Приоритет: высокий

Статус:
- [ ] Перестать писать Mongo-запросы прямо в test-файлах
- [ ] Вынести чтение данных в `src/repositories/...`
- [ ] Вынести вычисление нарушений в `src/services/backend_checks/...`

Правило для новых тестов:
- test-файл только orchestration
- repository отвечает за доступ к данным
- service отвечает за вычисление нарушений
- report builder отвечает за Allure/text/html

Шаблон целевого сценария:

```python
def test_some_rule(db, period_days):
    result = some_check_service.run(db=db, period_days=period_days)
    attach_report(result)
    assert not result.violations
```

Критерий готовности:
- В новых backend checks нет `.find(...)` и `.aggregate(...)` прямо в тесте

## Этап 5. Убрать хардкод параметров из файлов

Приоритет: высокий

Статус:
- [ ] Вынести даты, ObjectId и исключения в конфиг
- [ ] Убрать sample user id из тестов
- [ ] Убрать ручное редактирование верхних строк файла как основной способ настройки

Что выносить в конфиг:
- `SPECIFIC_USP_ID`
- фиксированные временные окна
- `excluded_club_ids`
- тестовые `user_id`
- пороги ошибок и проценты

Форматы:
- `.env` — только секреты и окружения
- `data/*.json` или `docs/config examples` — статические справочники
- CLI flags / pytest options — параметры запуска

Критерий готовности:
- Поведение теста не меняется через ручное редактирование Python-файла

## Этап 6. Разрезать большие файлы

Приоритет: средний

Самые тяжёлые файлы:
- `tests/backend/test_statistics_2025.py`
- `tests/backend/payments/test_webkassa_monitoring.py`
- `tests/backend/payments/test_subscription_access_type.py`
- `tests/backend/trainings/test_personal_trainings_consistency.py`

Подход:
1. Выделить query functions
2. Выделить domain calculations
3. Выделить report builders
4. Оставить в test-файле только сценарий

Критерий готовности:
- test-файлы не превращаются в мини-приложения на 300-1500 строк

## Этап 7. Нормализовать запуск suite

Приоритет: средний

Статус:
- [ ] Разделить запуск `checks` и `monitoring`
- [ ] Упростить `run_tests.py`
- [ ] Уменьшить ручную зависимость от txt-списков

Минимальная цель:
- `python run_tests.py` для основного backend checks
- отдельный профиль для monitoring

Желаемая цель:
- marker-based запуск:
  - `pytest -m backend_check`
  - `pytest -m backend_monitoring`
  - `pytest -m "backend and not backend_research"`

Критерий готовности:
- Состав suite определяется правилами и marker-ами, а не только ручным списком файлов

## Быстрые победы на 1-2 дня

- [ ] Убрать `test_recent_transactions.py` из основного backend списка
- [ ] Убрать `test_bonus_usage_distribution.py` из основного backend списка
- [ ] Добавить новые marker-ы в `pytest.ini`
- [ ] Исправить backend Allure environment в `run_tests.py`
- [ ] Зафиксировать дефолтную стратегию окружений в `docs/backend_testing_strategy.md`

## Первая волна рефакторинга по файлам

### Волна 1

- [ ] `tests/backend/payments/test_recent_transactions.py`
- [ ] `tests/backend/payments/bonuses/test_bonus_usage_distribution.py`
- [ ] `tests/backend/test_statistics_2025.py`

Цель:
- классифицировать и вынести из основного suite

### Волна 2

- [ ] `tests/backend/payments/test_webkassa_monitoring.py`
- [ ] `tests/backend/payments/test_subscription_access_type.py`
- [ ] `tests/backend/trainings/test_personal_trainings_consistency.py`

Цель:
- разрезать на query/service/report

### Волна 3

- [ ] `tests/backend/notifications/test_welcome_push.py`
- [ ] `tests/backend/notifications/test_birthday_push.py`
- [ ] `tests/backend/notifications/test_inactive_user_push.py`

Цель:
- довести push validators до консистентного шаблона

## Definition of Done для backend checks

Сценарий считается отрефакторенным, если:

- test-файл короче и описывает только бизнес-правило
- нет прямого доступа к `db["collection"]` в тесте
- нет редактируемых вручную констант в верхней части теста
- есть явный тип сценария: `check`, `monitoring` или `research`
- отчёт отделён от вычисления логики
- запуск не требует ручного редактирования кода

## Рабочий порядок выполнения

1. Сначала отделить monitoring от checks
2. Потом убрать prod-first defaults
3. Потом стабилизировать conftest и запуск
4. Потом переносить доменную логику в services/repositories
5. Только после этого браться за самые большие файлы

## Замечания по процессу

- Не делать большой “one-shot” рефакторинг
- На каждый PR брать 1 тип проблемы или 1-2 файла
- После каждого шага обновлять этот roadmap
- Для спорных файлов сначала решать: это test, monitoring или research

## Журнал прогресса

### Выполнено

- [ ] Ничего не отмечено

### В работе

- [ ] Не заполнено

### Следующий шаг

- [ ] Перенести аналитические сценарии из `tests_to_run_backend.txt` в отдельный monitoring-профиль
