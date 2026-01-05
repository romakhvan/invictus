# Решение проблем с Appium

## Быстрая диагностика

Запустите диагностические тесты:
```bash
pytest tests/mobile/test_appium_connection.py -v -s
```

## Частые проблемы

### 1. Ошибка: "Connection refused" или "Failed to establish connection"

**Причина:** Appium сервер не запущен.

**Решение:**
```bash
# Запустите Appium сервер
appium

# Или с логами
appium --log-level debug
```

**Проверка:**
```bash
curl http://localhost:4723/status
```

### 2. Ошибка: "No such device" или "device not found"

**Причина:** Устройство не подключено или не видно через ADB.

**Решение:**
```bash
# Проверьте подключенные устройства
adb devices

# Если устройство не видно:
# 1. Проверьте USB кабель
# 2. Включите "Отладка по USB" в настройках Android
# 3. Перезапустите ADB сервер
adb kill-server
adb start-server
adb devices
```

### 3. Ошибка: "app not found" или "app not installed"

**Причина:** Приложение не установлено на устройстве.

**Решение:**
```bash
# Проверьте, установлено ли приложение
adb shell pm list packages | findstr "kz.fitnesslabs.invictus.staging"

# Если не установлено, установите:
adb install path/to/app.apk
```

### 4. Ошибка: "Session not created" или "Unable to create session"

**Причина:** Неправильные capabilities или версия Appium.

**Решение:**
1. Проверьте конфигурацию в `src/config/app_config.py`
2. Убедитесь, что версия Appium совместима:
   ```bash
   appium --version
   pip show Appium-Python-Client
   ```

### 5. Ошибка: "UiAutomator2 not installed"

**Причина:** Драйвер UiAutomator2 не установлен в Appium.

**Решение:**
```bash
appium driver install uiautomator2
```

## Проверка конфигурации

Убедитесь, что в `src/config/app_config.py` указаны правильные значения:

```python
MOBILE_DEVICE_NAME = "adb-R3CT60QGWPP-Jms8yO._adb-tls-connect._tcp"  # Из 'adb devices'
MOBILE_PLATFORM_VERSION = "16"  # Из 'adb shell getprop ro.build.version.release'
MOBILE_APP_PACKAGE = "kz.fitnesslabs.invictus.staging"  # Из 'adb shell dumpsys window'
MOBILE_APP_ACTIVITY = ".MainActivity"  # Из 'adb shell dumpsys window'
```

## Получение информации об устройстве

```bash
# Имя устройства
adb devices -l

# Версия Android
adb shell getprop ro.build.version.release

# Package и Activity запущенного приложения
adb shell dumpsys window | Select-String -Pattern 'mCurrentFocus|mFocusedApp'
```

## Логи Appium

Если проблема не решается, запустите Appium с подробными логами:

```bash
appium --log-level debug
```

Затем запустите тест в другом терминале и посмотрите логи Appium.

## Проверка версий

```bash
# Версия Appium
appium --version

# Версия Python клиента
pip show Appium-Python-Client

# Версия Selenium
pip show selenium
```

## Полезные команды

```bash
# Перезапуск ADB
adb kill-server && adb start-server

# Проверка подключения устройства
adb devices

# Проверка статуса Appium
curl http://localhost:4723/status

# Запуск всех диагностических тестов
pytest tests/mobile/test_appium_connection.py -v -s
```

