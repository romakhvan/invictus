import pytest
import pymongo
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from src.config.db_config import MONGO_URI_PROD, DB_NAME
from src.utils.mobile_debug_menu import interactive_debug_menu
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
        "--backend-env",
        default="prod",
        choices=["prod", "stage"],
        help="Окружение MongoDB для backend тестов (prod или stage). По умолчанию: prod",
    )
    parser.addoption(
        "--period-days",
        type=int,
        default=7,
        help="Период анализа в днях для backend тестов. По умолчанию: 7",
    )
    parser.addoption(
        "--keepalive",
        action="store_true",
        default=False,
        help="Оставить приложение открытым после завершения тестов (для отладки)"
    )
    parser.addoption(
        "--mobile-no-reset",
        action="store_true",
        default=False,
        help="Не сбрасывать данные мобильного приложения между тестами (Appium no_reset=True)",
    )
    parser.addoption(
        "--mobile-ui-logs",
        action="store_true",
        default=False,
        help="Включить подробные UI-логи Page Objects (WAIT/CLICK/VISIBLE и т.д.)",
    )
    parser.addoption(
        "--onboarding-phone",
        default=None,
        type=str,
        help="Конкретный номер телефона для теста онбординга. Если не указан — ищется свободный автоматически.",
    )
    parser.addoption(
        "--onboarding-phone-kg",
        default=None,
        type=str,
        help="Номер телефона (без кода страны +996) для теста онбординга клиента из Кыргызстана.",
    )


def pytest_configure(config):
    """Синхронизирует флаги pytest с runtime-настройками логирования."""
    os.environ["MOBILE_UI_LOGS"] = "1" if config.getoption("--mobile-ui-logs") else "0"


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

    def _collect_and_save_elements(
        driver,
        class_name: str,
        element_name: str,
        file_prefix: str,
        filter_prompt: str,
        value_attr: str,
        ui_selector_method: str,
        value_label: str,
        file_title: str,
    ) -> None:
        """Collect elements of a given class, show them, and save generated locators to a file."""
        try:
            search_substr = input(
                f"🔎 Фильтр по {filter_prompt} (Enter — без фильтра): "
            ).strip().lower()

            elements = driver.find_elements(AppiumBy.CLASS_NAME, class_name)
            print(f"\n✅ Найдено {element_name} элементов: {len(elements)}\n")

            usable_locators = []

            for el in elements:
                try:
                    res_id = (el.get_attribute("resource-id") or "").strip()
                    if value_attr == "text":
                        value = (el.text or "").strip()
                    else:
                        value = (el.get_attribute(value_attr) or "").strip()

                    content_desc = (el.get_attribute("content-desc") or "").strip()
                    clickable = (el.get_attribute("clickable") or "").strip()
                    enabled = (el.get_attribute("enabled") or "").strip()
                    bounds = (el.get_attribute("bounds") or "").strip()

                    visible = el.is_displayed()

                    if not (value or res_id or content_desc):
                        continue

                    if search_substr:
                        haystack = " ".join(
                            [
                                value.lower(),
                                res_id.lower(),
                                content_desc.lower(),
                            ]
                        )
                        if search_substr not in haystack:
                            continue

                    locator_repr = None
                    if res_id:
                        locator_repr = f'AppiumBy.ID("{res_id}")'
                    elif content_desc:
                        locator_repr = f'AppiumBy.ACCESSIBILITY_ID, "{content_desc}"'
                    elif value:
                        safe_value = value.replace('"', '\\"')
                        locator_repr = (
                            'AppiumBy.ANDROID_UIAUTOMATOR('
                            f'\'new UiSelector().{ui_selector_method}("{safe_value}")\''
                            ')'
                        )

                    usable_locators.append(
                        {
                            "value": value,
                            "res_id": res_id,
                            "content_desc": content_desc,
                            "clickable": clickable,
                            "enabled": enabled,
                            "bounds": bounds,
                            "visible": visible,
                            "locator": locator_repr,
                        }
                    )
                except Exception:
                    continue

            if not usable_locators:
                print(f"⚠️ Подходящие {element_name} не найдены.")
                return

            usable_locators.sort(
                key=lambda x: (
                    not x["res_id"],
                    x["res_id"] or x["content_desc"] or x["value"] or "",
                )
            )

            for idx, item in enumerate(usable_locators[:20], 1):
                print(f"{idx}. {element_name}:")
                if item["value"]:
                    print(f"   {value_label}: '{item['value']}'")
                if item.get("content_desc"):
                    print(f"   content-desc: '{item['content_desc']}'")
                if item["res_id"]:
                    print(f"   resource-id: {item['res_id']}")
                if item.get("bounds"):
                    print(f"   bounds: {item['bounds']}")
                if item.get("clickable"):
                    print(f"   clickable: {item['clickable']}")
                if item.get("enabled"):
                    print(f"   enabled: {item['enabled']}")
                print(f"   visible: {item['visible']}")
                if item["locator"]:
                    print(f"   locator: {item['locator']}\n")
                else:
                    print("   locator: (не удалось сгенерировать)\n")

            if len(usable_locators) > 20:
                print(f"... и еще {len(usable_locators) - 20} элементов")
                print("💡 Полный список доступен в файле с локаторами")

            try:
                diagnostics_dir = "diagnostics"
                os.makedirs(diagnostics_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = os.path.join(
                    diagnostics_dir, f"{file_prefix}_{timestamp}.txt"
                )

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {file_title}\n")
                    f.write(f"# Всего элементов: {len(usable_locators)}\n")
                    if search_substr:
                        f.write(f"# Фильтр: {search_substr}\n")
                    f.write("\n")

                    for idx, item in enumerate(usable_locators, 1):
                        f.write(f"{idx}. {element_name}\n")
                        if item["value"]:
                            f.write(f"   {value_label}: '{item['value']}'\n")
                        if item.get("content_desc"):
                            f.write(f"   content-desc: '{item['content_desc']}'\n")
                        if item["res_id"]:
                            f.write(f"   resource-id: {item['res_id']}\n")
                        if item.get("bounds"):
                            f.write(f"   bounds: {item['bounds']}\n")
                        if item.get("clickable"):
                            f.write(f"   clickable: {item['clickable']}\n")
                        if item.get("enabled"):
                            f.write(f"   enabled: {item['enabled']}\n")
                        f.write(f"   visible: {item['visible']}\n")
                        if item["locator"]:
                            f.write(f"   locator = {item['locator']}\n")
                        f.write("\n")

                print(f"\n💾 Локаторы сохранены в файл: {filepath}")
                print("📂 Откройте файл и скопируйте нужные выражения в Page Object'ы")
            except Exception as e:
                print(f"⚠️ Не удалось сохранить локаторы в файл: {e}")

        except Exception as e:
            print(f"❌ Ошибка: {e}")

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
        print("  7 - 🔘 Показать все Button элементы")
        print("  8 - 🖼 Показать все ImageView элементы")
        print("  9 - 👆 Показать кликабельные элементы (все по clickable=true)")
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
                # Все TextView + сохранение локаторов в файл
                print("\n📝 Поиск TextView элементов...")
                _collect_and_save_elements(
                    driver=driver,
                    class_name="android.widget.TextView",
                    element_name="TextView",
                    file_prefix="locators_textview",
                    filter_prompt="тексту/ID",
                    value_attr="text",
                    ui_selector_method="text",
                    value_label="text",
                    file_title="Сгенерированные локаторы для TextView",
                )
            
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
            
            elif choice == "7":
                # Все Button + сохранение локаторов в файл
                print("\n📝 Поиск Button элементов...")
                _collect_and_save_elements(
                    driver=driver,
                    class_name="android.widget.Button",
                    element_name="Button",
                    file_prefix="locators_button",
                    filter_prompt="тексту/ID",
                    value_attr="text",
                    ui_selector_method="text",
                    value_label="text",
                    file_title="Сгенерированные локаторы для Button",
                )
            
            elif choice == "8":
                # Все ImageView + сохранение локаторов в файл
                print("\n📝 Поиск ImageView элементов...")
                _collect_and_save_elements(
                    driver=driver,
                    class_name="android.widget.ImageView",
                    element_name="ImageView",
                    file_prefix="locators_imageview",
                    filter_prompt="content-desc/ID",
                    value_attr="content-desc",
                    ui_selector_method="description",
                    value_label="content-desc",
                    file_title="Сгенерированные локаторы для ImageView",
                )
            
            elif choice == "9":
                # Все кликабельные элементы (//*[@clickable='true'])
                print("\n👆 Поиск кликабельных элементов...")
                try:
                    search_substr = input(
                        "🔎 Фильтр по тексту/desc/ID (Enter — без фильтра): "
                    ).strip().lower()

                    elements = driver.find_elements(
                        AppiumBy.XPATH, "//*[@clickable='true']"
                    )
                    print(f"\n✅ Найдено кликабельных элементов: {len(elements)}\n")

                    items = []
                    for el in elements:
                        try:
                            cls = (el.get_attribute("className") or el.tag_name or "").strip()
                            text = (el.text or "").strip()
                            content_desc = (el.get_attribute("content-desc") or "").strip()
                            res_id = (el.get_attribute("resource-id") or "").strip()
                            bounds = (el.get_attribute("bounds") or "").strip()

                            if search_substr:
                                haystack = " ".join(
                                    [cls.lower(), text.lower(), content_desc.lower(), res_id.lower()]
                                )
                                if search_substr not in haystack:
                                    continue

                            locator_repr = None
                            if res_id:
                                locator_repr = f'AppiumBy.ID("{res_id}")'
                            elif content_desc:
                                locator_repr = f'AppiumBy.ACCESSIBILITY_ID, "{content_desc}"'
                            elif text and "TextView" in cls:
                                safe = text.replace('"', '\\"')
                                locator_repr = (
                                    'AppiumBy.ANDROID_UIAUTOMATOR('
                                    f'\'new UiSelector().text("{safe}")\''
                                    ')'
                                )

                            items.append({
                                "class": cls,
                                "text": text,
                                "content_desc": content_desc,
                                "resource_id": res_id,
                                "bounds": bounds,
                                "locator": locator_repr,
                            })
                        except Exception:
                            continue

                    if not items:
                        print("⚠️ Кликабельные элементы не найдены (или не прошли фильтр).")
                        continue

                    for idx, it in enumerate(items[:20], 1):
                        print(f"{idx}. class: {it['class']}")
                        if it["text"]:
                            print(f"   text: '{it['text']}'")
                        if it["content_desc"]:
                            print(f"   content-desc: '{it['content_desc']}'")
                        if it["resource_id"]:
                            print(f"   resource-id: {it['resource_id']}")
                        if it["bounds"]:
                            print(f"   bounds: {it['bounds']}")
                        if it["locator"]:
                            print(f"   locator: {it['locator']}")
                        print()

                    if len(items) > 20:
                        print(f"... и еще {len(items) - 20} элементов")
                        print("💡 Полный список в файле с локаторами")

                    diagnostics_dir = "diagnostics"
                    os.makedirs(diagnostics_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filepath = os.path.join(
                        diagnostics_dir, f"locators_clickable_{timestamp}.txt"
                    )
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write("# Кликабельные элементы (clickable=true)\n")
                        f.write(f"# Всего: {len(items)}\n")
                        if search_substr:
                            f.write(f"# Фильтр: {search_substr}\n")
                        f.write("\n")
                        for idx, it in enumerate(items, 1):
                            f.write(f"{idx}. class: {it['class']}\n")
                            if it["text"]:
                                f.write(f"   text: '{it['text']}'\n")
                            if it["content_desc"]:
                                f.write(f"   content-desc: '{it['content_desc']}'\n")
                            if it["resource_id"]:
                                f.write(f"   resource-id: {it['resource_id']}\n")
                            if it["bounds"]:
                                f.write(f"   bounds: {it['bounds']}\n")
                            if it["locator"]:
                                f.write(f"   locator = {it['locator']}\n")
                            f.write("\n")
                    print(f"\n💾 Сохранено в файл: {filepath}")
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
            
            else:
                print("❌ Неизвестная команда. Используйте 0-9")
                
        except (KeyboardInterrupt, EOFError):
            print("\n⏹️  Завершение...")
            break


@pytest.fixture(scope="function")
def appium_driver(request):
    """Фикстура для Appium драйвера (на каждый тест)."""
    if not APPIUM_AVAILABLE:
        pytest.skip("Appium не установлен. Установите: pip install Appium-Python-Client selenium")
    driver = AppiumDriver()

    mobile_no_reset: bool = request.config.getoption("--mobile-no-reset")
    if mobile_no_reset:
        driver.start(no_reset=True, full_reset=False)
    else:
        driver.start(no_reset=False)  # Сбрасываем приложение к начальному состоянию
    yield driver

    # Интерактивное меню до закрытия драйвера: сессия остаётся активной для отладки
    show_menu = request.config.getoption("--keepalive") or request.node.get_closest_marker("interactive_mobile")
    if show_menu:
        driver_obj = driver.get_driver()
        try:
            interactive_debug_menu(driver_obj)
        except (KeyboardInterrupt, EOFError):
            print("\n[interactive] Меню прервано пользователем")
    driver.close()


@pytest.fixture(scope="function")
def mobile_driver(appium_driver):
    """Фикстура для получения Appium WebDriver объекта."""
    driver = appium_driver.get_driver()
    
    # Опциональный программный перезапуск приложения перед каждым тестом.
    # По умолчанию выключен: AppiumDriver.start(...) уже запускает приложение.
    # Двойной запуск (start + terminate/activate) замедляет тесты и может вносить флак.
    ENABLE_APP_RESTART = False
    
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

TELEGRAM_ENABLED = False  # переключить в True чтобы включить отправку

# Глобальное хранилище результатов тестов по категориям
test_results = {}


def pytest_runtest_logreport(report):
    """
    Хук pytest для сбора результатов каждого теста.
    Вызывается для каждой фазы теста (setup, call, teardown).
    Выводит в консоль результат и время выполнения каждого теста.
    """
    if report.when == "call":  # Учитываем только фазу выполнения теста
        # Получаем путь к файлу теста
        test_file = report.nodeid.split("::")[0] if "::" in report.nodeid else "unknown"
        test_name = report.nodeid.split("::")[-1] if "::" in report.nodeid else report.nodeid

        # Вывод результата и времени выполнения (требование project rules)
        status = "PASSED" if report.passed else ("SKIPPED" if report.skipped else "FAILED")
        duration_s = report.duration if report.duration is not None else 0.0
        print(f"\nTEST {status}: {test_name} — {duration_s:.1f}s")

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
    if not TELEGRAM_ENABLED:
        return

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
