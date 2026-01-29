"""
Конфигурация приложения для UI тестов.
"""

import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Web приложение
WEB_BASE_URL = os.getenv("WEB_BASE_URL", "https://your-web-app.com")
WEB_TIMEOUT = int(os.getenv("WEB_TIMEOUT", "30000"))  # миллисекунды

# Mobile приложение
MOBILE_APP_PATH = os.getenv("MOBILE_APP_PATH")  # Путь к .apk/.ipa файлу
MOBILE_PLATFORM = os.getenv("MOBILE_PLATFORM", "Android")  # Android или iOS
MOBILE_DEVICE_NAME = os.getenv("MOBILE_DEVICE_NAME", "emulator-5554")
MOBILE_PLATFORM_VERSION = os.getenv("MOBILE_PLATFORM_VERSION", "14")
MOBILE_APPIUM_SERVER = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")

# Package и Activity для установленного приложения
MOBILE_APP_PACKAGE = os.getenv("MOBILE_APP_PACKAGE", "com.example.app")
MOBILE_APP_ACTIVITY = os.getenv("MOBILE_APP_ACTIVITY", ".MainActivity")

# Общие настройки
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))  # секунды
EXPLICIT_WAIT = int(os.getenv("EXPLICIT_WAIT", "20"))  # секунды

