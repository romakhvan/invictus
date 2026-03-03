# Предотвращение сворачивания приложения

## Проблема

Во время выполнения тестов приложение может сворачиваться по следующим причинам:

### 1. **Системные причины**
- 📲 Уведомления (push, SMS, звонки)
- 🔒 Автоблокировка экрана (устройство засыпает)
- ⚙️ Системные диалоги (обновления, низкий заряд)
- 🏠 Другие приложения получают фокус

### 2. **Причины в приложении**
- ⚠️ Неожиданный переход на другую activity
- 🐛 Ошибки в приложении
- 🔄 Редиректы на внешние приложения

### 3. **Причины в тесте**
- ⏰ Недостаточные waits перед взаимодействием
- 🎯 Неправильные локаторы (клик не по тому элементу)

---

## Решения

### ✅ Автоматическая защита (уже реализовано)

Capabilities в `src/drivers/appium_driver.py` уже настроены для предотвращения сворачивания:

```python
# Предотвращение автоблокировки
options.no_sign = True
options.settings = {
    'ignoreUnimportantViews': True,
    'allowInvisibleElements': True,
    'enableNotificationListener': False,
}
```

### 🛡️ Проверка и восстановление в тестах

#### Способ 1: Автоматическая проверка перед важными действиями

В любой Page Object используйте метод `ensure_app_is_active()`:

```python
def click_important_button(self):
    """Клик по важной кнопке с проверкой фокуса приложения."""
    # Проверяем что приложение активно
    self.ensure_app_is_active()
    
    # Выполняем действие
    self.click(AppiumBy.ID, "important_button")
```

#### Способ 2: Полная проверка состояния

Используйте `check_and_recover_app_state()` перед критическими шагами:

```python
def perform_critical_action(self):
    """Критическое действие с полной проверкой состояния."""
    # Разблокировка устройства + проверка фокуса приложения
    self.check_and_recover_app_state()
    
    # Выполняем действие
    self.click(AppiumBy.ID, "submit_button")
```

#### Способ 3: Восстановление после ошибки

```python
def enter_data_with_recovery(self, text: str):
    """Ввод данных с восстановлением при ошибке."""
    try:
        self.send_keys(AppiumBy.ID, "input_field", text)
    except Exception as e:
        print(f"⚠️ Ошибка ввода: {e}")
        
        # Пробуем восстановить состояние
        if self.check_and_recover_app_state():
            print("🔄 Повторная попытка ввода...")
            self.send_keys(AppiumBy.ID, "input_field", text)
        else:
            raise
```

---

## Диагностика проблемы

### 1. Интерактивное меню (при использовании --keepalive)

```bash
pytest tests/mobile/smoke/test_client_onboarding.py --keepalive -s
```

Команда **6 - 🔄 Проверить и активировать приложение**:
- Показывает текущий package/activity
- Проверяет блокировку устройства
- Автоматически активирует приложение если оно свернулось

### 2. Программная проверка

Добавьте в тест:

```python
def test_with_app_check(mobile_driver):
    """Тест с проверкой состояния приложения."""
    
    # Импортируем
    from src.config.app_config import MOBILE_APP_PACKAGE
    
    # В любой момент теста проверяем
    current_package = mobile_driver.current_package
    print(f"📱 Текущий package: {current_package}")
    
    if current_package != MOBILE_APP_PACKAGE:
        print("⚠️ ВНИМАНИЕ: Приложение не в фокусе!")
        mobile_driver.activate_app(MOBILE_APP_PACKAGE)
```

---

## Рекомендации для стабильных тестов

### ✅ DO (Делать)

1. **Используйте `ensure_app_is_active()`** перед критическими действиями
2. **Добавляйте достаточные waits** между действиями
3. **Проверяйте логи** если тест падает неожиданно
4. **Используйте диагностику** (команда 1 в --keepalive меню)
5. **Делайте скриншоты** в проблемных местах

### ❌ DON'T (Не делать)

1. ❌ Не используйте `time.sleep()` вместо явных waits
2. ❌ Не игнорируйте warning'и о смене package
3. ❌ Не запускайте тесты на устройствах с активными уведомлениями
4. ❌ Не используйте устройства с низким зарядом (могут быть системные диалоги)

---

## Настройка устройства для стабильных тестов

### Android

```bash
# Отключить автоблокировку
adb shell settings put system screen_off_timeout 2147483647

# Остаться на экране (screen always on при зарядке)
adb shell svc power stayon true

# Отключить анимации (ускорит тесты)
adb shell settings put global window_animation_scale 0
adb shell settings put global transition_animation_scale 0
adb shell settings put global animator_duration_scale 0
```

### Эмулятор AVD

1. Settings → Display → Sleep → **Never**
2. Settings → Notifications → **Do not disturb** → включить
3. Закрыть все фоновые приложения

---

## Методы для использования в тестах

### В BaseMobilePage доступны методы:

| Метод | Описание | Когда использовать |
|-------|----------|-------------------|
| `ensure_app_is_active()` | Проверяет и активирует приложение | Перед важными действиями |
| `wake_and_unlock()` | Разблокирует устройство | При длительных тестах |
| `check_and_recover_app_state()` | Полная проверка + восстановление | Перед критическими шагами |

### В AppiumDriver доступны методы:

| Метод | Описание |
|-------|----------|
| `keep_app_active()` | Активирует приложение |
| `wake_device()` | Разблокирует устройство |
| `check_app_state()` | Возвращает информацию о состоянии |

---

## Пример стабильного теста

```python
@pytest.mark.mobile
@pytest.mark.smoke
def test_stable_flow(mobile_driver):
    """Стабильный тест с проверками состояния."""
    
    # Шаг 1: Обычное действие
    preview = PreviewPage(mobile_driver).wait_loaded()
    preview.skip_preview()
    
    # Шаг 2: Критическое действие - проверяем состояние
    phone = PhoneAuthPage(mobile_driver).wait_loaded()
    phone.ensure_app_is_active()  # ← Проверка перед важным действием
    phone.enter_phone("7001234567")
    
    # Шаг 3: Длительная операция - полная проверка
    sms = SmsCodePage(mobile_driver).wait_loaded()
    sms.check_and_recover_app_state()  # ← Полная проверка
    sms.enter_code()
    
    # Готово!
```

---

## Дополнительная диагностика

### Лог текущего состояния

```python
# В любом месте теста
page = SomePage(mobile_driver)
print(f"Package: {mobile_driver.current_package}")
print(f"Activity: {mobile_driver.current_activity}")
print(f"Locked: {mobile_driver.is_locked()}")
```

### Автоматическая диагностика в файл

```python
page.diagnose_current_screen(context="После входа")
# → Создаст файл diagnostics/diag_SomePage_После_входа_20260210_143022.txt
```

---

## Итого

✅ Capabilities уже настроены для предотвращения сворачивания  
✅ Методы проверки доступны во всех Page Objects  
✅ Интерактивная диагностика через `--keepalive`  
✅ Настройки устройства для стабильности  

**Используйте эти инструменты для создания стабильных тестов!** 🎉
