# Настройка Android тестирования

## Предварительные требования

### 1. Установка Android SDK

1. Установите [Android Studio](https://developer.android.com/studio)
2. В Android Studio: **Tools → SDK Manager**
3. Установите:
   - Android SDK Platform-Tools
   - Android SDK Build-Tools
   - Android Emulator (если используете эмулятор)

### 2. Настройка переменных окружения

Добавьте в PATH:
- `ANDROID_HOME` = путь к Android SDK (например: `C:\Users\YourName\AppData\Local\Android\Sdk`)
- `%ANDROID_HOME%\platform-tools`
- `%ANDROID_HOME%\tools`
- `%ANDROID_HOME%\tools\bin`

### 3. Установка Appium

```bash
# Установка Appium через npm
npm install -g appium

# Установка UiAutomator2 драйвера (для Android)
appium driver install uiautomator2
```

### 4. Подключение устройства

#### Вариант A: Физическое устройство

1. Включите **Режим разработчика** на Android:
   - Настройки → О телефоне → 7 раз нажмите на "Номер сборки"
2. Включите **Отладка по USB**:
   - Настройки → Для разработчиков → Отладка по USB
3. Подключите устройство через USB
4. Проверьте подключение:
   ```bash
   adb devices
   ```
   Должно показать ваше устройство

#### Вариант B: Эмулятор

1. Создайте AVD (Android Virtual Device) в Android Studio
2. Запустите эмулятор
3. Проверьте подключение:
   ```bash
   adb devices
   ```

### 5. Получение информации об устройстве

**Linux/Mac:**
```bash
# Список подключенных устройств
adb devices

# Имя устройства (для MOBILE_DEVICE_NAME)
adb devices -l

# Версия Android (для MOBILE_PLATFORM_VERSION)
adb shell getprop ro.build.version.release

# Package name установленного приложения (если приложение уже установлено)
adb shell pm list packages | grep your.app.name
```

**Windows PowerShell:**
```powershell
# Список подключенных устройств
adb devices

# Имя устройства (для MOBILE_DEVICE_NAME)
adb devices -l

# Версия Android (для MOBILE_PLATFORM_VERSION)
adb shell getprop ro.build.version.release

# Package name установленного приложения (если приложение уже установлено)
adb shell pm list packages | Select-String -Pattern "your.app.name"
# Или через findstr
adb shell pm list packages | findstr "your.app.name"
```

### 6. Получение информации о приложении

Если приложение уже установлено на устройстве:

**Linux/Mac:**
```bash
# Получить package name и activity
adb shell dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'

# Или через aapt (Android Asset Packaging Tool)
aapt dump badging your_app.apk | grep package
aapt dump badging your_app.apk | grep launchable-activity
```

**Windows PowerShell:**
```powershell
# Получить package name и activity
adb shell dumpsys window | Select-String -Pattern 'mCurrentFocus|mFocusedApp'

# Или через findstr
adb shell dumpsys window | findstr /R "mCurrentFocus mFocusedApp"

# Или через aapt (Android Asset Packaging Tool)
aapt dump badging your_app.apk | Select-String -Pattern "package"
aapt dump badging your_app.apk | Select-String -Pattern "launchable-activity"
```

**Пример вывода команды:**
```
mCurrentFocus=Window{721969e u0 com.example.app/com.example.app.MainActivity}
mFocusedApp=ActivityRecord{179889719 u0 com.example.app/.MainActivity t964}
```

**Из этого вывода извлекаем:**
- **Package name**: `com.example.app`
- **Activity**: `com.example.app.MainActivity` (полное имя) или `.MainActivity` (короткое)

## Настройка конфигурации

Откройте `.env` файл и укажите:

```bash
# Mobile Application Configuration
MOBILE_APP_PATH=  # Укажите путь к .apk, если нужно установить приложение
MOBILE_PLATFORM=Android
MOBILE_DEVICE_NAME=emulator-5554  # Или имя вашего устройства из 'adb devices'
MOBILE_PLATFORM_VERSION=14  # Версия Android
MOBILE_APP_PACKAGE=com.example.app  # Из вывода adb shell dumpsys window
MOBILE_APP_ACTIVITY=.MainActivity  # Из вывода adb shell dumpsys window
APPIUM_SERVER_URL=http://localhost:4723
```

**Вариант 1: Использование констант из конфига (рекомендуется)**

Если вы указали `MOBILE_APP_PACKAGE` и `MOBILE_APP_ACTIVITY` в `.env`, фикстура в `tests/conftest.py` будет использовать их автоматически:
```python
@pytest.fixture(scope="function")
def appium_driver():
    """Фикстура для Appium драйвера с установленным приложением."""
    driver = AppiumDriver()
    driver.start()  # Использует MOBILE_APP_PACKAGE и MOBILE_APP_ACTIVITY из .env
    yield driver
    driver.close()
```

**Вариант 2: Переопределение в тестах**

Если нужно использовать другие значения в конкретном тесте:
```python
@pytest.fixture(scope="function")
def appium_driver():
    """Фикстура для Appium драйвера с установленным приложением."""
    driver = AppiumDriver()
    driver.start(
        app_package="com.example.app",
        app_activity="com.example.app.MainActivity"
    )
    yield driver
    driver.close()
```

## Запуск Appium сервера

```bash
# Запустить Appium сервер
appium

# Или с логами
appium --log-level debug
```

Appium должен запуститься на `http://localhost:4723`

## Проверка настройки

Запустите тест:

```bash
pytest tests/mobile/test_app_launch.py -v -s
```

Если все настроено правильно, приложение должно запуститься на устройстве/эмуляторе.

## Решение проблем

### Ошибка: "Unable to find a connected device"
- Проверьте: `adb devices` показывает устройство
- Убедитесь, что USB отладка включена
- Попробуйте перезапустить adb: `adb kill-server && adb start-server`

### Ошибка: "Cannot connect to Appium server"
- Убедитесь, что Appium запущен: `appium`
- Проверьте URL в конфиге: `http://localhost:4723`

### Ошибка: "App not found"
- Проверьте путь к .apk файлу
- Или укажите правильный package name и activity

### Ошибка: "UiAutomator2 not installed"
```bash
appium driver install uiautomator2
```

