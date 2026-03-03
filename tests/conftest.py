import pytest
import pymongo
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from src.config.db_config import MONGO_URI_PROD, DB_NAME
from src.utils.telegram_notifier import send_test_notification
from src.utils.ui_helpers import take_screenshot

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


# ==================== Pytest командная строка ====================

def pytest_addoption(parser):
    """Добавляем кастомные опции командной строки."""
    parser.addoption(
        "--keepalive",
        action="store_true",
        default=False,
        help="Оставить приложение открытым после завершения тестов (для отладки)"
    )


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

def _interactive_debug_menu(driver):
    """
    Интерактивное меню для отладки с диагностикой локаторов.
    
    Args:
        driver: Appium WebDriver объект
    """
    from appium.webdriver.common.appiumby import AppiumBy
    import os
    from datetime import datetime
    
    while True:
        print("\n" + "=" * 80)
        print("🔧 ИНТЕРАКТИВНОЕ МЕНЮ ОТЛАДКИ")
        print("=" * 80)
        print("📱 Приложение продолжает работать на устройстве")
        print("\n🛠️  Доступные команды:")
        print("  1 - 📋 Диагностика текущего экрана (все элементы)")
        print("  2 - 📸 Сделать скриншот")
        print("  3 - 🔍 Показать page source (XML)")
        print("  4 - ℹ️  Показать package/activity")
        print("  5 - 📝 Показать все TextView элементы")
        print("  6 - 🔄 Проверить и активировать приложение")
        print("  0 - ❌ Завершить и закрыть приложение")
        print("=" * 80)
        
        try:
            choice = input("\n⌨️  Введите номер команды: ").strip()
            
            if choice == "0":
                print("\n⏹️  Завершение...")
                break
            
            elif choice == "1":
                # Диагностика экрана
                print("\n🔍 Запуск диагностики текущего экрана...")
                try:
                    diag_dir = "diagnostics"
                    os.makedirs(diag_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"diag_keepalive_{timestamp}.txt"
                    filepath = os.path.join(diag_dir, filename)
                    
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("=" * 80 + "\n")
                        f.write("🔍 ДИАГНОСТИКА ЭКРАНА (KEEPALIVE MODE)\n")
                        f.write("=" * 80 + "\n")
                        f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("=" * 80 + "\n\n")
                        
                        # Package и Activity
                        try:
                            f.write(f"📱 Application Info:\n")
                            f.write(f"   Package:  {driver.current_package}\n")
                            f.write(f"   Activity: {driver.current_activity}\n\n")
                        except Exception as e:
                            f.write(f"⚠️ Package/Activity: {e}\n\n")
                        
                        # Все TextView элементы
                        try:
                            text_views = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                            f.write("─" * 80 + "\n")
                            f.write(f"📝 TEXT ELEMENTS (TextView): {len(text_views)} найдено\n")
                            f.write("─" * 80 + "\n\n")
                            
                            for idx, tv in enumerate(text_views[:30], 1):
                                try:
                                    text = tv.text
                                    res_id = tv.get_attribute("resource-id")
                                    visible = tv.is_displayed()
                                    enabled = tv.is_enabled()
                                    
                                    if text or res_id:
                                        f.write(f"{idx}. TextView:\n")
                                        if text:
                                            f.write(f"   text: '{text}'\n")
                                        if res_id:
                                            f.write(f"   resource-id: {res_id}\n")
                                        f.write(f"   visible: {visible}, enabled: {enabled}\n\n")
                                except:
                                    pass
                        except Exception as e:
                            f.write(f"⚠️ TextView elements: {e}\n\n")
                        
                        # Все Button элементы
                        try:
                            buttons = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
                            f.write("─" * 80 + "\n")
                            f.write(f"🔘 BUTTON ELEMENTS: {len(buttons)} найдено\n")
                            f.write("─" * 80 + "\n\n")
                            
                            for idx, btn in enumerate(buttons, 1):
                                try:
                                    text = btn.text
                                    res_id = btn.get_attribute("resource-id")
                                    enabled = btn.is_enabled()
                                    
                                    f.write(f"{idx}. Button:\n")
                                    if text:
                                        f.write(f"   text: '{text}'\n")
                                    if res_id:
                                        f.write(f"   resource-id: {res_id}\n")
                                    f.write(f"   enabled: {enabled}\n\n")
                                except:
                                    pass
                        except Exception as e:
                            f.write(f"⚠️ Button elements: {e}\n\n")
                        
                        # EditText элементы
                        try:
                            edit_texts = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
                            if edit_texts:
                                f.write("─" * 80 + "\n")
                                f.write(f"✏️  EDITTEXT ELEMENTS: {len(edit_texts)} найдено\n")
                                f.write("─" * 80 + "\n\n")
                                
                                for idx, et in enumerate(edit_texts, 1):
                                    try:
                                        text = et.text
                                        res_id = et.get_attribute("resource-id")
                                        hint = et.get_attribute("hint")
                                        
                                        f.write(f"{idx}. EditText:\n")
                                        if text:
                                            f.write(f"   text: '{text}'\n")
                                        if hint:
                                            f.write(f"   hint: '{hint}'\n")
                                        if res_id:
                                            f.write(f"   resource-id: {res_id}\n\n")
                                    except:
                                        pass
                        except Exception as e:
                            f.write(f"⚠️ EditText elements: {e}\n\n")
                    
                    print(f"✅ Диагностика сохранена: {filepath}")
                    
                    # Автоматически открываем файл
                    import platform
                    import subprocess
                    system = platform.system()
                    try:
                        if system == "Windows":
                            os.startfile(filepath)
                        elif system == "Darwin":
                            subprocess.run(["open", filepath])
                        elif system == "Linux":
                            subprocess.run(["xdg-open", filepath])
                        print("📂 Файл открыт автоматически")
                    except:
                        print(f"📂 Откройте файл вручную: {filepath}")
                        
                except Exception as e:
                    print(f"❌ Ошибка диагностики: {e}")
            
            elif choice == "2":
                # Скриншот
                print("\n📸 Создание скриншота...")
                try:
                    screenshots_dir = "screenshots/debug"
                    os.makedirs(screenshots_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = os.path.join(screenshots_dir, f"keepalive_{timestamp}.png")
                    driver.save_screenshot(filepath)
                    print(f"✅ Скриншот сохранен: {filepath}")
                except Exception as e:
                    print(f"❌ Ошибка при создании скриншота: {e}")
            
            elif choice == "3":
                # Page source
                print("\n🔍 Получение page source...")
                try:
                    page_source_dir = "diagnostics"
                    os.makedirs(page_source_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = os.path.join(page_source_dir, f"page_source_{timestamp}.xml")
                    
                    source = driver.page_source
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(source)
                    
                    print(f"✅ Page source сохранен: {filepath}")
                    print(f"   Размер: {len(source)} символов")
                    
                    # Пробуем открыть
                    try:
                        import platform
                        import subprocess
                        system = platform.system()
                        if system == "Windows":
                            os.startfile(filepath)
                        elif system == "Darwin":
                            subprocess.run(["open", filepath])
                        elif system == "Linux":
                            subprocess.run(["xdg-open", filepath])
                        print("📂 Файл открыт автоматически")
                    except:
                        print(f"📂 Откройте файл вручную: {filepath}")
                        
                except Exception as e:
                    print(f"❌ Ошибка получения page source: {e}")
            
            elif choice == "4":
                # Package/Activity
                print("\n📱 Информация о приложении:")
                try:
                    print(f"   Package:  {driver.current_package}")
                    print(f"   Activity: {driver.current_activity}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
            
            elif choice == "5":
                # Все TextView
                print("\n📝 Поиск TextView элементов...")
                try:
                    text_views = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
                    print(f"\n✅ Найдено TextView элементов: {len(text_views)}\n")
                    
                    for idx, tv in enumerate(text_views[:20], 1):
                        try:
                            text = tv.text
                            res_id = tv.get_attribute("resource-id")
                            visible = tv.is_displayed()
                            
                            if text or res_id:
                                print(f"{idx}. TextView:")
                                if text:
                                    print(f"   text: '{text}'")
                                if res_id:
                                    print(f"   resource-id: {res_id}")
                                print(f"   visible: {visible}\n")
                        except:
                            pass
                    
                    if len(text_views) > 20:
                        print(f"... и еще {len(text_views) - 20} элементов")
                        print("💡 Используйте команду '1' для полной диагностики в файл")
                        
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
            
            elif choice == "6":
                # Проверка и активация приложения
                print("\n🔄 Проверка состояния приложения...")
                try:
                    from src.config.app_config import MOBILE_APP_PACKAGE
                    
                    # Проверяем блокировку устройства
                    try:
                        is_locked = driver.is_locked()
                        if is_locked:
                            print("⚠️ Устройство заблокировано, разблокируем...")
                            driver.unlock()
                            import time
                            time.sleep(0.5)
                            print("✅ Устройство разблокировано")
                        else:
                            print("✅ Устройство разблокировано")
                    except Exception as e:
                        print(f"⚠️ Не удалось проверить блокировку: {e}")
                    
                    # Проверяем package
                    current_package = driver.current_package
                    current_activity = driver.current_activity
                    
                    print(f"\n📱 Текущее состояние:")
                    print(f"   Package:  {current_package}")
                    print(f"   Activity: {current_activity}")
                    print(f"   Ожидается: {MOBILE_APP_PACKAGE}")
                    
                    if current_package == MOBILE_APP_PACKAGE:
                        print("\n✅ Приложение активно и в фокусе")
                    else:
                        print(f"\n⚠️ Приложение не в фокусе!")
                        print(f"   Активируем {MOBILE_APP_PACKAGE}...")
                        driver.activate_app(MOBILE_APP_PACKAGE)
                        import time
                        time.sleep(1.5)
                        
                        # Проверяем повторно
                        new_package = driver.current_package
                        if new_package == MOBILE_APP_PACKAGE:
                            print(f"✅ Приложение успешно активировано")
                        else:
                            print(f"❌ Не удалось активировать приложение")
                            print(f"   Текущий package: {new_package}")
                    
                except Exception as e:
                    print(f"❌ Ошибка проверки состояния: {e}")
            
            else:
                print("❌ Неизвестная команда. Используйте 0-6")
                
        except (KeyboardInterrupt, EOFError):
            print("\n⏹️  Завершение...")
            break


@pytest.fixture(scope="function")
def appium_driver(request):
    """Фикстура для Appium драйвера (на каждый тест)."""
    if not APPIUM_AVAILABLE:
        pytest.skip("Appium не установлен. Установите: pip install Appium-Python-Client selenium")
    driver = AppiumDriver()
    driver.start(no_reset=False)  # Сбрасываем приложение к начальному состоянию
    yield driver
    
    # Если указан флаг --keepalive, оставляем приложение открытым для отладки
    if request.config.getoption("--keepalive"):
        driver_obj = driver.get_driver()
        _interactive_debug_menu(driver_obj)
    # driver.close() закомментирован - сессия завершится автоматически при выходе


@pytest.fixture(scope="function")
def mobile_driver(appium_driver):
    """Фикстура для получения Appium WebDriver объекта."""
    driver = appium_driver.get_driver()
    
    # ОПЦИОНАЛЬНО: Программный перезапуск приложения перед каждым тестом
    # Может быть избыточен, если используется no_reset=False в драйвере
    # Включите если нужен явный terminate + activate перед каждым тестом
    ENABLE_APP_RESTART = False  # Измените на True для принудительного перезапуска
    
    if ENABLE_APP_RESTART:
        try:
            from src.config.app_config import MOBILE_APP_PACKAGE, MOBILE_APP_ACTIVITY
            import time
            
            # Закрываем приложение
            driver.terminate_app(MOBILE_APP_PACKAGE)
            time.sleep(1)  # Даем время на завершение
            
            # Запускаем заново через activity
            driver.activate_app(MOBILE_APP_PACKAGE)
            time.sleep(2)  # Даем время на запуск
            
            # Проверяем, что приложение запустилось
            current_package = driver.current_package
            if current_package != MOBILE_APP_PACKAGE:
                print(f"⚠️ Приложение не запустилось, пробуем через start_activity...")
                driver.start_activity(MOBILE_APP_PACKAGE, MOBILE_APP_ACTIVITY)
                time.sleep(2)
            
            print("🔄 Приложение перезапущено")
        except Exception as e:
            print(f"⚠️ Не удалось перезапустить приложение: {e}")
    
    yield driver


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


# ==================== Автоматические скриншоты ====================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Автоматический скриншот при падении mobile тестов.
    
    Вызывается для каждой фазы теста (setup, call, teardown).
    Если тест упал и используется mobile_driver - делаем скриншот.
    """
    outcome = yield
    report = outcome.get_result()
    
    # Только для mobile тестов и только при ошибке в основной фазе
    if report.when == "call" and report.failed:
        if "mobile_driver" in item.fixturenames:
            driver = item.funcargs.get("mobile_driver")
            if driver:
                try:
                    test_name = item.name.replace("[", "_").replace("]", "_")
                    screenshot_path = take_screenshot(
                        driver,
                        f"error_{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    )
                    print(f"\n📸 Скриншот ошибки: {screenshot_path}")
                except Exception as e:
                    print(f"\n⚠️ Не удалось сделать скриншот: {e}")
