"""
Конфигурация приложения для UI тестов.
"""

# Web приложение
WEB_BASE_URL = "https://your-web-app.com"  # Замените на реальный URL
WEB_TIMEOUT = 30000  # 30 секунд в миллисекундах

# Mobile приложение
MOBILE_APP_PATH = None  # Путь к .apk/.ipa файлу или bundle_id
MOBILE_PLATFORM = "Android"  # или "iOS"
MOBILE_DEVICE_NAME = "adb-R3CT60QGWPP-Jms8yO._adb-tls-connect._tcp"  # Имя устройства/эмулятора
MOBILE_PLATFORM_VERSION = "16"  # Версия ОС
MOBILE_APPIUM_SERVER = "http://localhost:4723"  # URL Appium сервера

# Package и Activity для установленного приложения (если MOBILE_APP_PATH = None)
# Пример: "kz.fitnesslabs.invictus.staging"
MOBILE_APP_PACKAGE = "kz.fitnesslabs.invictus.staging"  # Package name установленного приложения
# Пример: "kz.fitnesslabs.invictus.staging.MainActivity" или ".MainActivity"
MOBILE_APP_ACTIVITY = ".MainActivity"  # Activity установленного приложения

# Общие настройки
IMPLICIT_WAIT = 10  # секунды
EXPLICIT_WAIT = 20  # секунды

