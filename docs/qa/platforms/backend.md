# Backend Tests

## Назначение

Backend-тесты проверяют:

- бизнес-правила
- консистентность MongoDB/PostgreSQL данных
- платежи
- бонусы
- гостевые визиты
- push-уведомления
- monitoring/reporting сценарии

## Где лежит код

```text
tests/backend/
tests/backend/conftest.py
src/repositories/
src/services/backend_checks/
src/validators/
```

## Запуск

```bash
pytest tests/backend -v
pytest -m backend -v
pytest -m backend_check -v
pytest -m backend_monitoring -v
python run_tests.py
```

## Профили

- `backend_check` - gate checks, могут валить основной прогон
- `backend_monitoring` - операционный мониторинг и отчеты
- `backend_research` - разовые аналитические сценарии

## Правила

- новые backend-сценарии сначала классифицировать как check/monitoring/research
- `tests_to_run_backend.txt` держать только для gate checks
- monitoring добавлять в `tests_to_run_backend_monitoring.txt`
- запросы к данным выносить в repositories
- отчетные таблицы прикладывать в Allure

## Deep dive

- [[../../backend_testing_strategy|Backend testing strategy]]
- [[../../allure/backend_reporting_rules|Backend Allure reporting rules]]
- [[subscriptions|Subscriptions QA reference]]
- [[../../coach_wallet_testing_guide|Coach wallet testing guide]]
- [[backend-tests|Backend tests catalog]]
- [[webkassa|Web-Kassa checks]]

## См. также

- [[test-data]]
- [[reporting-allure]]
- [[debugging]]
