# Руководство по тестированию кошелька тренера

## Обзор

Система тестирования кошелька тренера включает 7 основных проверок для выявления ошибок поступления и списания денег.

## Варианты тестирования

### 1. ✅ Проверка согласованности баланса (`check_wallet_balance_consistency`)

**Что проверяет:**
- Соответствие `totalAmount` в `coachwallets` сумме всех транзакций из `coachwallethistories`
- Корректность расчёта баланса на основе истории операций

**Что выявляет:**
- Расхождения между фактическим балансом и рассчитанным
- Пропущенные транзакции
- Неправильное обновление баланса при операциях

**Использование:**
```python
from src.validators.coach_wallet_validator import check_wallet_balance_consistency

result = check_wallet_balance_consistency(db, coach_user_id="65fae5f178c80d001fba9493")
```

---

### 2. ✅ Проверка расчёта комиссий (`check_commission_calculations`)

**Что проверяет:**
- Корректность формулы: `gross - комиссии = net`
- Правильность расчёта каждой комиссии (club, acquiring, platform)
- Соответствие процентов и сумм в `commissionBreakdown`

**Что выявляет:**
- Ошибки в расчёте комиссий
- Несоответствие между gross и net суммами
- Неправильные проценты комиссий

**Использование:**
```python
from src.validators.coach_wallet_validator import check_commission_calculations

result = check_commission_calculations(db, coach_user_id="65fae5f178c80d001fba9493")
```

---

### 3. ✅ Проверка на дубликаты (`check_duplicate_transactions`)

**Что проверяет:**
- Наличие дублирующихся транзакций
- Одинаковые `source`, `transaction`, `amount`, `operation` в разных записях

**Что выявляет:**
- Двойное начисление/списание денег
- Повторная обработка одной транзакции
- Ошибки в логике создания записей

**Использование:**
```python
from src.validators.coach_wallet_validator import check_duplicate_transactions

# Проверка за последние 30 дней
result = check_duplicate_transactions(db, coach_user_id="65fae5f178c80d001fba9493", days=30)
```

---

### 4. ✅ Проверка последовательности транзакций (`check_transaction_sequence`)

**Что проверяет:**
- Хронологический порядок транзакций
- Отсутствие нарушений временной последовательности

**Что выявляет:**
- Транзакции с неправильными датами
- Нарушения в порядке операций
- Проблемы с временными метками

**Использование:**
```python
from src.validators.coach_wallet_validator import check_transaction_sequence

result = check_transaction_sequence(db, coach_user_id="65fae5f178c80d001fba9493")
```

---

### 5. ✅ Проверка отрицательного баланса (`check_negative_balance`)

**Что проверяет:**
- Отсутствие отрицательных балансов в кошельках
- Корректность операций списания

**Что выявляет:**
- Кошельки с отрицательным балансом (если недопустимо)
- Ошибки при списании денег
- Проблемы с валидацией операций

**Использование:**
```python
from src.validators.coach_wallet_validator import check_negative_balance

# Проверка конкретного тренера
result = check_negative_balance(db, coach_user_id="65fae5f178c80d001fba9493")

# Проверка всех кошельков
result = check_negative_balance(db)
```

---

### 6. ✅ Проверка целостности данных (`check_data_integrity`)

**Что проверяет:**
- Существование связанных сущностей (coach, source, transaction)
- Корректность ссылок между коллекциями
- Наличие записей в связанных коллекциях

**Что выявляет:**
- "Висячие" ссылки на несуществующие записи
- Проблемы с удалением связанных данных
- Ошибки в связях между коллекциями

**Использование:**
```python
from src.validators.coach_wallet_validator import check_data_integrity

result = check_data_integrity(db, coach_user_id="65fae5f178c80d001fba9493")
```

---

### 7. ✅ Проверка данных в transactions (`check_transactions_data`)

**Что проверяет:**
- Соответствие сумм: `transactions.price` = `coachwallethistories.amount.gross`
- Статус транзакции (должен быть `success`)
- Соответствие `coachId` в `transactions.paidFor.serviceProducts` и `coach` в `coachwallethistories`
- Соответствие `userServiceProductId` в transactions и `source` в coachwallethistories
- Временная последовательность: `transactions.time` должен быть раньше `coachwallethistories.createdAt`

**Что выявляет:**
- Несоответствие сумм между transactions и coachwallethistories
- Транзакции с неправильным статусом
- Ошибки в связях между transactions и coachwallethistories
- Нарушения временной последовательности

**Использование:**
```python
from src.validators.coach_wallet_validator import check_transactions_data

result = check_transactions_data(db, coach_user_id="65fae5f178c80d001fba9493")
```

---

## Комплексная проверка

### `validate_coach_wallet` - Все проверки сразу

Выполняет все 7 проверок и возвращает результаты:

```python
from src.validators.coach_wallet_validator import validate_coach_wallet

results = validate_coach_wallet(db, coach_user_id="65fae5f178c80d001fba9493")

# Результаты:
# {
#     "balance_consistency": True/False,
#     "commission_calculations": True/False,
#     "duplicate_transactions": True/False,
#     "transaction_sequence": True/False,
#     "negative_balance": True/False,
#     "data_integrity": True/False,
#     "transactions_data": True/False
# }
```

---

## Запуск тестов

### Через pytest:

```bash
# Все тесты кошелька
pytest tests/test_coach_wallet.py -v

# Конкретный тест
pytest tests/test_coach_wallet.py::test_coach_wallet_balance_consistency -v

# Комплексная проверка
pytest tests/test_coach_wallet.py::test_coach_wallet_full_validation -v
```

### Программно:

```python
from pymongo import MongoClient
from src.config.db_config import DB_NAME, MONGO_URI
from src.validators.coach_wallet_validator import validate_coach_wallet

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Проверка конкретного тренера
results = validate_coach_wallet(db, "65fae5f178c80d001fba9493")
```

---

## Дополнительные проверки (можно добавить)

### 7. Проверка суммы транзакций за период
- Сравнение суммы транзакций с ожидаемыми значениями
- Проверка соответствия бизнес-логике

### 8. Проверка скорости обновления баланса
- Время между транзакцией и обновлением баланса
- Задержки в синхронизации

### 9. Проверка корректности типов операций
- Соответствие `operation` типу источника
- Валидность комбинаций полей

### 10. Проверка на аномалии
- Необычно большие/малые суммы
- Подозрительные паттерны в транзакциях
- Статистический анализ отклонений

---

## Рекомендации по использованию

1. **Регулярное тестирование**: Запускайте проверки после каждого релиза или изменения логики кошелька
2. **Мониторинг**: Интегрируйте проверки в CI/CD pipeline
3. **Алерты**: Настройте уведомления при обнаружении ошибок
4. **Логирование**: Сохраняйте результаты проверок для анализа трендов
5. **Периодичность**: 
   - Ежедневно: проверка баланса и дубликатов
   - Еженедельно: все проверки
   - После изменений: комплексная проверка

---

## Примеры использования в тестах

См. файл `tests/test_coach_wallet.py` для примеров интеграции в pytest-тесты.

