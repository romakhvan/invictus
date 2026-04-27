# Test Strategy

## Цели

- проверять критичные пользовательские сценарии
- ловить регрессии в backend-данных
- покрывать smoke flows для web/mobile
- разделять gate checks, monitoring и research
- делать падения диагностичными

## Уровни покрытия

```text
unit
  -> backend/data checks
  -> web/mobile smoke
  -> web/mobile regression
  -> e2e flows
  -> monitoring/research
```

## Приоритеты

### P0

- авторизация
- покупка и оплата
- посещения
- абонементы
- бонусы
- критичные mobile flows

### P1

- навигация
- фильтры
- клубы
- бронирования
- уведомления

### P2

- редкие edge cases
- аналитические проверки
- exploratory/research checks

## Правила добавления теста

- выбрать уровень: unit/backend/web/mobile/e2e
- выбрать маркеры
- использовать существующие fixtures
- не дублировать helpers/repositories/page objects
- добавить Allure metadata, если тест попадает в отчет
- обновить `tests_to_run_*.txt`, если тест должен входить в регулярный прогон

## См. также

- [[backend]]
- [[web]]
- [[mobile]]
- [[best-practices]]
- [[../../testing_roadmap|Testing roadmap]]
