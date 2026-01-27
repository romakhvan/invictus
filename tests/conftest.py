import pytest
import pymongo
import os
import time
from dotenv import load_dotenv
from src.config.db_config import MONGO_URI_PROD, DB_NAME
from src.utils.telegram_notifier import send_test_notification

# Загрузка переменных окружения из .env
load_dotenv()

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


# ==================== Telegram уведомления ====================

# Глобальное хранилище результатов тестов по категориям
test_results = {}


def pytest_runtest_logreport(report):
    """
    Хук pytest для сбора результатов каждого теста.
    Вызывается для каждой фазы теста (setup, call, teardown).
    """
    if report.when == "call":  # Учитываем только фазу выполнения теста
        # Получаем путь к файлу теста
        test_file = report.nodeid.split("::")[0] if "::" in report.nodeid else "unknown"
        
        # Инициализируем категорию если её нет
        if test_file not in test_results:
            test_results[test_file] = {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "duration": 0.0
            }
        
        # Обновляем статистику
        if report.passed:
            test_results[test_file]["passed"] += 1
        elif report.failed:
            test_results[test_file]["failed"] += 1
        elif report.skipped:
            test_results[test_file]["skipped"] += 1
        
        # Добавляем время выполнения
        test_results[test_file]["duration"] += report.duration


def pytest_sessionfinish(session, exitstatus):
    """
    Хук pytest, вызываемый после завершения всех тестов.
    Отправляет результаты в Telegram.
    """
    if not test_results:
        print("\n⚠️ Нет результатов тестов для отправки")
        return
    
    print("\n📤 Отправка результатов тестов в Telegram...")
    
    # Получаем URL отчёта из переменной окружения (если есть)
    report_url = os.getenv("ALLURE_REPORT_URL")
    
    # Группируем результаты по категориям
    categories = {}
    
    for test_file, results in test_results.items():
        # Определяем категорию на основе пути к файлу
        category = "Другие"
        
        if "personal_training" in test_file.lower():
            category = "Personal Trainings"
        elif "payment" in test_file.lower():
            category = "Payments"
        
        # Добавляем результаты в категорию
        if category not in categories:
            categories[category] = {
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "duration": 0.0,
                "files": []
            }
        
        categories[category]["passed"] += results["passed"]
        categories[category]["failed"] += results["failed"]
        categories[category]["skipped"] += results["skipped"]
        categories[category]["errors"] += results["errors"]
        categories[category]["duration"] += results["duration"]
        categories[category]["files"].append(test_file)
    
    # Отправляем результаты по каждой категории
    for category, results in categories.items():
        # Берем первый файл из категории для определения топика
        test_file_path = results["files"][0] if results["files"] else ""
        
        success = send_test_notification(
            passed=results["passed"],
            failed=results["failed"],
            skipped=results["skipped"],
            errors=results["errors"],
            duration=results["duration"],
            test_file_path=test_file_path,
            category=category,
            report_url=report_url
        )
        
        if success:
            print(f"  ✅ {category}: результаты отправлены")
        else:
            print(f"  ❌ {category}: не удалось отправить результаты")
        
        # Небольшая задержка между отправками
        time.sleep(0.5)
    
    # Очищаем результаты после отправки
    test_results.clear()
    print("✅ Отправка результатов завершена\n")
