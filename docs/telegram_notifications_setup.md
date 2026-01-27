# Настройка уведомлений в Telegram

Руководство по настройке автоматической отправки результатов тестов в Telegram.

## 📋 Содержание
1. [Предварительные требования](#предварительные-требования)
2. [Настройка .env файла](#настройка-env-файла)
3. [Структура топиков](#структура-топиков)
4. [Использование](#использование)
5. [Устранение неполадок](#устранение-неполадок)

---

## Предварительные требования

✅ Установлены зависимости:
```bash
pip install -r requirements.txt
```

✅ У вас есть:
- **Bot Token**: `8513025994:AAHPlAeaUZjsQszfiIMpLLL5o5m4X7CkI8g`
- **Chat ID группы**: `-1003873139850`
- **Топики созданы** в супергруппе `Invictus_tests_results`

---

## Настройка .env файла

### Создайте файл `.env` в корне проекта:

```bash
# В корне проекта (где находится requirements.txt)
touch .env
```

### Добавьте следующее содержимое:

```ini
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=8513025994:AAHPlAeaUZjsQszfiIMpLLL5o5m4X7CkI8g
TELEGRAM_CHAT_ID=-1003873139850

# Allure Report URL (опционально)
# ALLURE_REPORT_URL=https://your-domain.com/allure-report
```

**⚠️ ВАЖНО**: Файл `.env` уже добавлен в `.gitignore` и не будет коммититься в Git.

---

## Структура топиков

Результаты тестов автоматически распределяются по топикам:

| Топик | ID | Категория тестов | Паттерн файлов |
|-------|-----|------------------|----------------|
| **personal_trainings** | 2 | Персональные тренировки | `*personal_training*` |
| **payments** | 10 | Платежи | `*payment*` |
| **notifications** | 4 | Остальные тесты | Все остальные |

### Пример:
- `tests/backend/test_personal_trainings_consistency.py` → **топик 2**
- `tests/backend/test_payment_flow.py` → **топик 10**
- `tests/backend/test_auth.py` → **топик 4**

---

## Использование

### 1. Запуск тестов

Просто запустите тесты как обычно:

```bash
# Запуск всех тестов
pytest

# Запуск конкретного файла
pytest tests/backend/test_personal_trainings_consistency.py

# Запуск с маркерами
pytest -m backend
```

### 2. Автоматическая отправка

После завершения тестов результаты **автоматически** отправляются в Telegram:

```
📤 Отправка результатов тестов в Telegram...
  ✅ Personal Trainings: результаты отправлены
  ✅ Payments: результаты отправлены
✅ Отправка результатов завершена
```

### 3. Формат сообщения в Telegram

```
✅ Результаты тестов: Personal Trainings

📊 Статистика:
  • Всего: 15
  • ✅ Пройдено: 14
  • ❌ Упало: 1

⏱ Время выполнения: 2м 34.56с
📅 Дата: 27.01.2026 14:35

📊 Открыть полный отчёт (если настроен ALLURE_REPORT_URL)
```

---

## Настройка ссылки на Allure отчёт

### Вариант 1: Локальный сервер (для разработки)

После запуска тестов, сгенерируйте и запустите Allure отчёт:

```bash
# Генерация отчёта
allure generate allure-results --clean -o allure-report

# Запуск локального сервера
allure open allure-report
```

Для отправки ссылки в Telegram добавьте в `.env`:
```ini
ALLURE_REPORT_URL=http://localhost:63342/allure-report
```

### Вариант 2: GitHub Pages

1. Настройте GitHub Actions для публикации отчётов:

```yaml
# .github/workflows/tests.yml
- name: Deploy Allure Report to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./allure-report
```

2. Добавьте в `.env`:
```ini
ALLURE_REPORT_URL=https://your-username.github.io/your-repo
```

### Вариант 3: CI/CD артефакты

Для Jenkins, GitLab CI или других CI/CD систем используйте URL артефакта:

```ini
ALLURE_REPORT_URL=https://jenkins.your-domain.com/job/tests/lastBuild/allure
```

---

## Добавление новых категорий

### Шаг 1: Создайте новый топик в Telegram
1. Зайдите в группу `Invictus_tests_results`
2. Создайте новый топик (например, `auth`)

### Шаг 2: Получите ID топика
1. Отправьте сообщение в новый топик
2. Откройте в браузере:
```
https://api.telegram.org/bot8513025994:AAHPlAeaUZjsQszfiIMpLLL5o5m4X7CkI8g/getUpdates
```
3. Найдите `"message_thread_id"` для вашего сообщения

### Шаг 3: Обновите код

Откройте `src/utils/telegram_notifier.py` и добавьте новую категорию:

```python
TOPIC_MAPPING = {
    "personal_trainings": 2,
    "payment": 10,
    "auth": 12,  # Новая категория
    "notifications": 4,
}
```

Обновите метод `determine_topic_id`:

```python
def determine_topic_id(self, test_file_path: str) -> int:
    test_file_path_lower = test_file_path.lower()
    
    if "personal_training" in test_file_path_lower:
        return TOPIC_MAPPING["personal_trainings"]
    
    if "payment" in test_file_path_lower:
        return TOPIC_MAPPING["payment"]
    
    if "auth" in test_file_path_lower:  # Новая проверка
        return TOPIC_MAPPING["auth"]
    
    return TOPIC_MAPPING["notifications"]
```

Обновите `tests/conftest.py` в функции `pytest_sessionfinish`:

```python
# Добавьте новую категорию
if "auth" in test_file.lower():
    category = "Auth"
```

---

## Устранение неполадок

### ❌ Сообщения не отправляются

**Проблема**: В консоли появляется:
```
⚠️ Telegram notifier не настроен (отсутствуют переменные окружения)
```

**Решение**:
1. Убедитесь, что файл `.env` создан в **корне проекта**
2. Проверьте, что в `.env` указаны `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`
3. Перезапустите тесты

---

### ❌ Ошибка при отправке

**Проблема**: В консоли:
```
❌ Ошибка отправки в Telegram: ...
```

**Решение**:
1. Проверьте, что бот добавлен в группу как **администратор**
2. Проверьте права бота: **Отправка сообщений** должна быть включена
3. Проверьте токен и Chat ID

---

### ❌ Сообщения отправляются не в тот топик

**Проблема**: Результаты попадают в `notifications` вместо нужного топика

**Решение**:
1. Проверьте имя файла теста - оно должно содержать ключевое слово:
   - `personal_training` → топик 2
   - `payment` → топик 10
2. Если нужна другая логика, обновите метод `determine_topic_id` в `telegram_notifier.py`

---

### 🔍 Отладка

Добавьте отладочную информацию в `telegram_notifier.py`:

```python
def determine_topic_id(self, test_file_path: str) -> int:
    test_file_path_lower = test_file_path.lower()
    print(f"🔍 Определяем топик для: {test_file_path_lower}")
    
    if "personal_training" in test_file_path_lower:
        print("  → Топик: personal_trainings (ID: 2)")
        return TOPIC_MAPPING["personal_trainings"]
    # ...
```

---

## Дополнительные возможности

### Отправка кастомных сообщений

Используйте модуль напрямую в тестах:

```python
from src.utils.telegram_notifier import get_telegram_notifier

def test_important_feature():
    notifier = get_telegram_notifier()
    if notifier:
        notifier.send_message(
            "🚨 Важный тест завершен!",
            thread_id=2  # ID топика
        )
    # ... ваш тест
```

### Отключение уведомлений

Закомментируйте или удалите переменные из `.env`:

```ini
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...
```

Тесты продолжат работать, но уведомления отправляться не будут.

---

## Контакты

При возникновении проблем:
1. Проверьте эту документацию
2. Проверьте логи в консоли
3. Обратитесь к команде разработки

**Удачного тестирования! 🚀**
