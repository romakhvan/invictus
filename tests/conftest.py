import pytest
import pymongo
from src.config.db_config import MONGO_URI_PROD, DB_NAME

# Для обратной совместимости используем PROD по умолчанию
# Но фикстуры в tests/backend/ и tests/mobile/ переопределяют это поведение
MONGO_URI = MONGO_URI_PROD

# Опциональный импорт Playwright (для веб-тестов)
try:
    from src.drivers.playwright_driver import PlaywrightDriver
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightDriver = None

# Опциональный импорт Appium (для мобильных тестов)
try:
    from src.drivers.appium_driver import AppiumDriver
    APPIUM_AVAILABLE = True
except ImportError:
    APPIUM_AVAILABLE = False
    AppiumDriver = None


# ==================== Backend фикстуры ====================

@pytest.fixture(scope="session")
def db():
    """Фикстура для подключения к MongoDB."""
    print("\n🔌 Connecting to MongoDB...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    yield db
    print("\n🧹 Closing Mongo connection.")
    client.close()


# ==================== Web фикстуры (Playwright) ====================

@pytest.fixture(scope="function")
def playwright_driver():
    """Фикстура для Playwright драйвера (на каждый тест)."""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright не установлен. Установите: pip install playwright && playwright install chromium")
    driver = PlaywrightDriver()
    driver.start(headless=False)  # Измените на True для CI/CD
    yield driver
    driver.close()


@pytest.fixture(scope="function")
def web_page(playwright_driver):
    """Фикстура для получения Playwright Page объекта."""
    return playwright_driver.get_page()


# ==================== Mobile фикстуры (Appium) ====================

@pytest.fixture(scope="function")
def appium_driver():
    """Фикстура для Appium драйвера (на каждый тест)."""
    if not APPIUM_AVAILABLE:
        pytest.skip("Appium не установлен. Установите: pip install Appium-Python-Client selenium")
    driver = AppiumDriver()
    driver.start()
    yield driver
    driver.close()


@pytest.fixture(scope="function")
def mobile_driver(appium_driver):
    """Фикстура для получения Appium WebDriver объекта."""
    return appium_driver.get_driver()
