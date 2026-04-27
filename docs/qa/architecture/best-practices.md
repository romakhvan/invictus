# Best Practices

## Общие правила

- тест проверяет одно понятное поведение
- имя теста отражает ожидаемый результат
- setup отделен от assertion
- повторяемая логика вынесена в helper/service/page object
- секреты не хранятся в коде
- данные и окружение описаны явно

## Assertions

Плохо:

```python
assert result
```

Лучше:

```python
assert result.is_valid, f"Найдены нарушения: {result.violations}"
```

## Fixtures

- использовать existing fixtures из `conftest.py`
- не создавать тяжелые fixtures без необходимости
- scope выбирать осознанно
- не прятать важные действия в autouse fixture без причины

## Page Objects

- локаторы внутри page object
- методы называют пользовательское действие
- page object не содержит business assertions
- тест не дублирует locator logic

## Backend checks

- запросы держать в repositories
- бизнес-правила держать в services/validators
- monitoring отделять от gate checks
- отсутствие данных оформлять через `pytest.skip()`

## Flaky prevention

- использовать явные ожидания
- не зависеть от порядка тестов
- не использовать общие изменяемые данные
- стабилизировать тест до добавления в регулярный прогон

## Review checklist

- выбран правильный уровень теста
- есть нужные маркеры
- тест запускается отдельно
- Allure заполнен
- failure диагностичен
- нет секретов
- нет лишнего `sleep`
- нет дублирования существующих helpers

## См. также

- [[test-strategy]]
- [[debugging]]
- [[architecture]]
