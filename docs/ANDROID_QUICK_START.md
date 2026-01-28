# 🚀 Быстрый старт: Android тестирование

## Шаг 1: Проверка окружения (5 минут)

Запустите скрипт проверки:

```bash
python scripts/check_android_setup.py
```

Скрипт проверит:
- ✅ Установлен ли ADB
- ✅ Подключены ли устройства
- ✅ Установлен ли Appium
- ✅ Запущен ли Appium сервер
- ✅ Правильность конфигурации

## Шаг 2: Настройка конфигурации (2 минуты)

Откройте `src/config/app_config.py` и укажите:

```python
# Вариант 1: Если у вас есть .apk файл
MOBILE_APP_PATH = r"C:\path\to\your\app.apk"

# Вариант 2: Если приложение уже установлено
MOBILE_APP_PATH = None  # Оставьте None
# И укажите package и activity в тестах (см. ниже)

# Имя устройства (из 'adb devices')
MOBILE_DEVICE_NAME = "emulator-5554"  # или имя вашего устройства

# Версия Android
MOBILE_PLATFORM_VERSION = "13.0"  # или ваша версия
```

## Шаг 3: Запуск Appium сервера

Откройте новый терминал и запустите:

```bash
appium
```

Должно появиться:
```
[Appium] Appium REST http interface listener started on 0.0.0.0:4723
```

## Шаг 4: Запуск первого теста

```bash
# Запустить тест запуска приложения
pytest tests/mobile/test_app_launch.py -v -s

# Или все мобильные тесты
pytest -m mobile -v -s
```

## Если приложение уже установлено

Если приложение уже установлено на устройстве, используйте package и activity:

1. Узнайте package name:
```bash
adb shell pm list packages | grep your.app
```

2. Узнайте activity:
```bash
adb shell dumpsys window | grep -E 'mCurrentFocus'
```

3. В тесте или конфиге укажите:
```python
# В conftest.py или в тесте
driver.start(
    app_package="com.your.app.package",
    app_activity="com.your.app.MainActivity"
)
```

## Пример: Тест с package и activity

Создайте файл `tests/mobile/test_installed_app.py`:

```python
import pytest
from appium.webdriver import Remote

@pytest.mark.mobile
def test_installed_app(mobile_driver: Remote):
    # Переопределяем фикстуру для установленного приложения
    pass
```

Или измените фикстуру в `tests/conftest.py`:

```python
@pytest.fixture(scope="function")
def appium_driver():
    driver = AppiumDriver()
    driver.start(
        app_package="com.your.app.package",
        app_activity="com.your.app.MainActivity"
    )
    yield driver
    driver.close()
```

## Решение проблем

### Устройство не найдено
```bash
# Проверить устройства
adb devices

# Перезапустить adb
adb kill-server
adb start-server
```

### Appium не запускается
```bash
# Проверить установку
appium --version

# Установить драйвер
appium driver install uiautomator2
```

### Приложение не запускается
- Проверьте путь к .apk файлу
- Проверьте package name и activity
- Убедитесь, что приложение установлено на устройстве

## Следующие шаги

После успешного запуска приложения:
1. Создайте Page Objects для экранов приложения
2. Напишите тесты для ключевых функций
3. Интегрируйте с Backend проверками

См. также:
- [Полная документация по настройке Android](docs/android_setup.md)
- [Примеры Page Objects](src/pages/mobile/example_mobile_page.py)














