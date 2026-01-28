# 🚀 Быстрая настройка Telegram-уведомлений

## Что нужно сделать прямо сейчас:

### 1️⃣ Создайте файл `.env` в корне проекта

```bash
# Windows PowerShell
New-Item -Path .env -ItemType File

# Или просто создайте файл вручную
```

### 2️⃣ Скопируйте в `.env` следующее содержимое:

```ini
TELEGRAM_BOT_TOKEN=8513025994:AAHPlAeaUZjsQszfiIMpLLL5o5m4X7CkI8g
TELEGRAM_CHAT_ID=-1003873139850
```

### 3️⃣ Установите зависимости (если еще не установлены)

```bash
pip install python-dotenv
```

или

```bash
pip install -r requirements.txt
```

### 4️⃣ Запустите тесты

```bash
pytest
```

или

```bash
pytest tests/backend/test_personal_trainings_consistency.py
```

---

## ✅ Что произойдет

После завершения тестов в Telegram автоматически придут сообщения:

- **Топик "personal_trainings"** → результаты `test_personal_trainings_*.py`
- **Топик "payments"** → результаты `test_*payment*.py`  
- **Топик "notifications"** → все остальные тесты

---

## 📖 Подробная документация

Смотрите полную документацию: [docs/telegram_notifications_setup.md](docs/telegram_notifications_setup.md)

- Добавление новых категорий
- Устранение неполадок
- Кастомные сообщения

---

**Готово! 🎉**
