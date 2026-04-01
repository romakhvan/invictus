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

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # prod | staging | development

# Package и Activity по окружению
_APP_CONFIG_MAP: dict[str, dict[str, str]] = {
    "prod": {
        "package":  "kz.fitnesslabs.invictus",
        "activity": "kz.fitnesslabs.invictus.MainActivity",
    },
    "staging": {
        "package":  "kz.fitnesslabs.invictus.staging",
        "activity": ".MainActivity",
    },
    "development": {
        "package":  "kz.fitnesslabs.invictus.development",
        "activity": "kz.fitnesslabs.invictus.development.MainActivity",
    },
}

_env_cfg = _APP_CONFIG_MAP.get(ENVIRONMENT, _APP_CONFIG_MAP["staging"])

MOBILE_APP_PACKAGE = os.getenv("MOBILE_APP_PACKAGE", _env_cfg["package"])
MOBILE_APP_ACTIVITY = os.getenv("MOBILE_APP_ACTIVITY", _env_cfg["activity"])

# Общие настройки
IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "10"))  # секунды
EXPLICIT_WAIT = int(os.getenv("EXPLICIT_WAIT", "20"))  # секунды

