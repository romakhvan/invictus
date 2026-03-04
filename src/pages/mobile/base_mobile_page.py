"""
Базовый класс для мобильных Page Objects (Appium).
"""

# Импорт класса Remote из appium.webdriver предоставляет тип WebDriver для управления мобильным приложением (Appium).
from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from src.pages.base_page import BasePage
from typing import Optional, Union, Dict, Tuple, TypeAlias

Locator: TypeAlias = Tuple[Union[AppiumBy, str], str]
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class BaseMobilePage(BasePage):
    """Базовый класс для мобильных страниц."""
    
    page_title: Optional[str] = None  # Переопределяется в дочерних классах
    
    def __init__(self, driver: Remote):
        """
        Инициализация мобильной страницы.
        
        Args:
            driver: Appium WebDriver объект
        """
        super().__init__(driver=driver)
        self.driver: Remote = driver
        self.wait = WebDriverWait(driver, 20)

    def _wait(self, timeout: Optional[int] = None) -> WebDriverWait:
        """Если timeout None — используется дефолтный wait (20s), иначе создаётся новый WebDriverWait."""
        if timeout is None:
            return self.wait
        return WebDriverWait(self.driver, timeout)
    
    def find_element(self, locator: Locator):
        """Найти элемент."""
        by, value = locator
        return self.driver.find_element(by, value)
    
    def find_elements(self, locator: Locator):
        """Найти элементы."""
        by, value = locator
        return self.driver.find_elements(by, value)
    
    def click(self, locator: Locator, timeout: Optional[int] = None):
        """Клик по элементу."""
        wait = self._wait(timeout)
        element = wait.until(EC.element_to_be_clickable(locator))
        element.click()
    
    def send_keys(self, locator: Locator, text: str, timeout: Optional[int] = None):
        """Ввод текста в поле."""
        wait = self._wait(timeout)
        element = wait.until(EC.presence_of_element_located(locator))
        element.clear()
        element.send_keys(text)
    
    @staticmethod
    def print_page_header(page_title: str) -> None:
        """
        Выводит красивый заголовок страницы в консоль.
        
        Args:
            page_title: Название страницы для отображения
        """
        print("\n" + "─" * 80)
        print(f"📱 Page: {page_title}")
        print("─" * 80)
    
    def ensure_app_is_active(self, expected_package: Optional[str] = None) -> bool:
        """
        Проверяет, что приложение в фокусе, и активирует его если свернулось.
        Полезно вызывать перед критическими действиями.

        Returns:
            True если приложение пришлось активировать (было свёрнуто).
            После реактивации вызывающий код должен перепроверить страницу (assert_ui / wait_loaded).
        """
        try:
            from src.config.app_config import MOBILE_APP_PACKAGE
            target_package = expected_package or MOBILE_APP_PACKAGE

            current_package = self.driver.current_package

            if current_package != target_package:
                print(f"⚠️ Приложение свернулось (текущий: {current_package})")
                print(f"   Активируем: {target_package}")
                self.driver.activate_app(target_package)
                import time
                time.sleep(1.5)  # Даем время на анимацию открытия
                print(f"✅ Приложение активировано")
                return True
            return False
        except Exception as e:
            print(f"⚠️ Не удалось проверить/активировать приложение: {e}")
            return False
    
    def wake_and_unlock(self) -> None:
        """
        Разблокирует устройство если оно заблокировано.
        Полезно при длительных тестах если устройство может уйти в сон.
        """
        try:
            if self.driver.is_locked():
                print("⚠️ Устройство заблокировано, разблокируем...")
                self.driver.unlock()
                import time
                time.sleep(0.5)
                print("✅ Устройство разблокировано")
        except Exception as e:
            print(f"⚠️ Не удалось разблокировать устройство: {e}")
    
    def check_and_recover_app_state(self, expected_package: Optional[str] = None) -> bool:
        """
        Полная проверка и восстановление состояния приложения.
        Комбинирует разблокировку устройства и активацию приложения.
        
        Args:
            expected_package: Ожидаемый package (по умолчанию из конфига)
        
        Returns:
            bool: True если приложение в порядке, False если были проблемы
        """
        had_issues = False
        
        # Шаг 1: Разблокировать устройство
        try:
            if self.driver.is_locked():
                print("⚠️ Устройство заблокировано")
                self.wake_and_unlock()
                had_issues = True
        except Exception as e:
            print(f"⚠️ Ошибка проверки блокировки: {e}")
        
        # Шаг 2: Проверить фокус приложения
        try:
            from src.config.app_config import MOBILE_APP_PACKAGE
            target_package = expected_package or MOBILE_APP_PACKAGE
            current_package = self.driver.current_package
            
            if current_package != target_package:
                print(f"⚠️ Приложение не в фокусе")
                self.ensure_app_is_active(target_package)
                had_issues = True
        except Exception as e:
            print(f"⚠️ Ошибка проверки приложения: {e}")
            had_issues = True
        
        if had_issues:
            print("🔄 Состояние приложения восстановлено")
        
        return not had_issues
    
    def get_text(self, locator: Locator, timeout: Optional[int] = None) -> str:
        """Получить текст элемента."""
        wait = self._wait(timeout)
        element = wait.until(EC.presence_of_element_located(locator))
        return element.text
    
    def is_visible(self, locator: Locator, timeout: Optional[int] = None) -> bool:
        """Проверка видимости элемента."""
        try:
            wait = self._wait(timeout if timeout is not None else 5)
            wait.until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 1000):
        """Свайп по экрану."""
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)
    
    @staticmethod
    def _locator_str(locator: Locator) -> str:
        """Строковое представление локатора для сообщений об ошибках."""
        by, value = locator
        by_name = getattr(by, "name", str(by))
        return f"{by_name} | {value}"

    def _raise_timeout_with_context(
        self,
        locator: Locator,
        msg: str,
        timeout: int,
        take_screenshot_on_timeout: bool = True,
        cause: Optional[Exception] = None,
    ) -> None:
        """Формирует детальное сообщение при таймауте и по возможности делает скриншот."""
        locator_str = self._locator_str(locator)
        page = getattr(self, "page_title", None) or self.__class__.__name__
        error_text = (
            f"[{page}] TIMEOUT {timeout}s: {msg}\nLocator: {locator_str}"
        )
        if take_screenshot_on_timeout:
            try:
                from datetime import datetime
                from src.utils.ui_helpers import take_screenshot
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_page = page.replace(" ", "_").replace("(", "").replace(")", "")
                path = take_screenshot(
                    self.driver,
                    f"timeout_{safe_page}_{ts}.png"
                )
                error_text += f"\nScreenshot: {path}"
            except Exception:
                pass
        exc = TimeoutException(error_text)
        if cause is not None:
            raise exc from cause
        raise exc

    def wait_visible(
        self,
        locator: Locator,
        error_message: str = "Element not found",
        timeout: int = 20,
        take_screenshot_on_timeout: bool = True,
    ):
        """
        Ждёт видимости элемента и выбрасывает исключение с понятным сообщением.
        
        Args:
            locator: Tuple (By, value)
            error_message: Сообщение об ошибке (что ожидали)
            timeout: Таймаут ожидания
            take_screenshot_on_timeout: Делать скриншот при таймауте
        
        Raises:
            TimeoutException: С детальным сообщением (страница, локатор, скриншот)
        """
        try:
            wait = self._wait(timeout)
            return wait.until(EC.visibility_of_element_located(locator))
        except TimeoutException as e:
            self._raise_timeout_with_context(
                locator, error_message, timeout, take_screenshot_on_timeout, cause=e
            )

    def wait_present(
        self,
        locator: Locator,
        error_message: str = "Element not found",
        timeout: int = 20,
        take_screenshot_on_timeout: bool = True,
    ):
        """
        Ждёт присутствия элемента в DOM (не обязательно видимого).
        
        Args:
            locator: Tuple (By, value)
            error_message: Сообщение об ошибке (что ожидали)
            timeout: Таймаут ожидания
            take_screenshot_on_timeout: Делать скриншот при таймауте
        
        Raises:
            TimeoutException: С детальным сообщением (страница, локатор, скриншот)
        """
        try:
            wait = self._wait(timeout)
            return wait.until(EC.presence_of_element_located(locator))
        except TimeoutException as e:
            self._raise_timeout_with_context(
                locator, error_message, timeout, take_screenshot_on_timeout, cause=e
            )

    def wait_loaded(self):
        """
        Ждёт загрузки страницы и возвращает self для chaining.
        Должен быть переопределён в дочерних классах.
        
        Returns:
            self для цепочки вызовов
        
        Raises:
            AssertionError: Если страница не загрузилась
        """
        # Выводим заголовок страницы если он определён
        if self.page_title:
            self.print_page_header(self.page_title)
        
        try:
            self.assert_ui()
        except TimeoutException:
            raise  # Детальное сообщение (страница, локатор, скриншот) уже в исключении
        except Exception as e:
            raise AssertionError(f"❌ Страница не загрузилась: {e}") from e
        return self
    
    def assert_ui(self):
        """
        Проверяет наличие всех ключевых элементов страницы.
        Должен быть переопределён в дочерних классах.
        
        Raises:
            AssertionError: Если какой-то элемент не найден
        """
        pass
    
    def is_loaded(self) -> bool:
        """
        Устаревший метод. Используйте wait_loaded() вместо него.
        Базовая проверка загрузки (можно переопределить).
        """
        return True
    
    def diagnose_page_elements(self, elements_dict: Dict[str, Tuple]) -> Dict[str, dict]:
        """
        Диагностирует все элементы страницы и возвращает их статус.
        
        Args:
            elements_dict: словарь вида {"element_name": (By.ID, "locator_value")}
        
        Returns:
            dict с информацией о каждом элементе:
            - found: найден ли элемент
            - visible: виден ли элемент
            - enabled: активен ли элемент
            - text: текст элемента
            - location: координаты элемента
            - size: размер элемента
            - error: текст ошибки если элемент не найден
        """
        results = {}
        
        for name, locator in elements_dict.items():
            by, value = locator
            try:
                element = self.driver.find_element(by, value)
                results[name] = {
                    "found": True,
                    "visible": element.is_displayed(),
                    "enabled": element.is_enabled(),
                    "text": element.text if element.text else "",
                    "location": element.location,
                    "size": element.size
                }
            except Exception as e:
                results[name] = {
                    "found": False,
                    "error": f"{type(e).__name__}: {str(e)}"
                }
        
        return results
    
    def print_page_diagnosis(self, elements_dict: Dict[str, Tuple]) -> None:
        """
        Выводит диагностику всех элементов в читаемом виде.
        
        Args:
            elements_dict: словарь вида {"element_name": (By.ID, "locator_value")}
        """
        results = self.diagnose_page_elements(elements_dict)
        
        print(f"\n{'='*70}")
        print(f"📋 PAGE DIAGNOSIS: {self.__class__.__name__}")
        print(f"{'='*70}")
        
        found_count = sum(1 for info in results.values() if info.get("found"))
        total_count = len(results)
        print(f"✅ Found: {found_count}/{total_count} elements\n")
        
        for name, info in results.items():
            if info.get("found"):
                print(f"✓ {name}:")
                print(f"  • visible:  {info['visible']}")
                print(f"  • enabled:  {info['enabled']}")
                print(f"  • text:     '{info['text']}'")
                print(f"  • location: {info['location']}")
                print(f"  • size:     {info['size']}")
            else:
                print(f"✗ {name}: NOT FOUND")
                print(f"  • error: {info['error']}")
            print()
        
        print(f"{'='*70}\n")
    
    def diagnose_current_screen(self, context: str = "") -> str:
        """
        Универсальная диагностика текущего экрана.
        Сохраняет информацию в файл и автоматически открывает его.
        
        Args:
            context: Контекст вызова (например, "После модалки SMS", "Перед вводом имени")
        
        Returns:
            Путь к файлу с диагностикой
        """
        import os
        from datetime import datetime
        import subprocess
        import platform
        
        # Создаем папку для диагностики
        diag_dir = "diagnostics"
        os.makedirs(diag_dir, exist_ok=True)
        
        # Формируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        page_name = self.__class__.__name__
        context_safe = context.replace(" ", "_").replace("/", "_") if context else "general"
        filename = f"diag_{page_name}_{context_safe}_{timestamp}.txt"
        filepath = os.path.join(diag_dir, filename)
        
        # Собираем всю информацию в буфер
        output_lines = []
        output_lines.append("=" * 80)
        output_lines.append(f"🔍 ДИАГНОСТИКА ЭКРАНА")
        output_lines.append("=" * 80)
        output_lines.append(f"Страница: {page_name}")
        if context:
            output_lines.append(f"Контекст: {context}")
        output_lines.append(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output_lines.append("=" * 80)
        output_lines.append("")
        
        # Текущий package и activity
        try:
            output_lines.append(f"📱 Application Info:")
            output_lines.append(f"   Package:  {self.driver.current_package}")
            output_lines.append(f"   Activity: {self.driver.current_activity}")
            output_lines.append("")
        except Exception as e:
            output_lines.append(f"⚠️ Не удалось получить package/activity: {e}")
            output_lines.append("")
        
        # Все видимые TextView элементы с полными атрибутами
        from appium.webdriver.common.appiumby import AppiumBy
        try:
            text_views = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
            output_lines.append("─" * 80)
            output_lines.append(f"📝 TEXT ELEMENTS (TextView): {len(text_views)} найдено")
            output_lines.append("─" * 80)
            
            visible_elements = []
            for tv in text_views[:20]:  # Первые 20 элементов
                try:
                    if tv.is_displayed():
                        element_info = {
                            'text': tv.text or '',
                            'resource_id': tv.get_attribute('resource-id') or '',
                            'content_desc': tv.get_attribute('content-desc') or '',
                            'class': tv.get_attribute('class') or '',
                            'enabled': tv.get_attribute('enabled') or '',
                            'clickable': tv.get_attribute('clickable') or '',
                            'bounds': tv.get_attribute('bounds') or ''
                        }
                        # Добавляем только если есть хоть какая-то полезная информация
                        if element_info['text'] or element_info['resource_id'] or element_info['content_desc']:
                            visible_elements.append(element_info)
                except:
                    pass
            
            if visible_elements:
                for idx, elem in enumerate(visible_elements, 1):
                    output_lines.append(f"\n[{idx}] Text: '{elem['text']}'")
                    if elem['resource_id']:
                        output_lines.append(f"    Resource ID: {elem['resource_id']}")
                        output_lines.append(f"    ✅ Локатор: AppiumBy.ID, '{elem['resource_id']}'")
                    if elem['content_desc']:
                        output_lines.append(f"    Content-desc: {elem['content_desc']}")
                        output_lines.append(f"    ✅ Локатор: AppiumBy.ACCESSIBILITY_ID, '{elem['content_desc']}'")
                    if elem['text']:
                        output_lines.append(f"    ✅ Локатор: AppiumBy.XPATH, '//android.widget.TextView[@text=\"{elem['text']}\"]'")
                    output_lines.append(f"    Clickable: {elem['clickable']} | Enabled: {elem['enabled']}")
            else:
                output_lines.append("⚠️ Нет видимых элементов с полезной информацией")
            output_lines.append("")
        except Exception as e:
            output_lines.append(f"⚠️ Ошибка при поиске TextView: {e}")
            output_lines.append("")
        
        # Кнопки (Button)
        try:
            buttons = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
            visible_buttons = [b for b in buttons[:10] if b.is_displayed()]
            if visible_buttons:
                output_lines.append("─" * 80)
                output_lines.append(f"🔘 BUTTONS: {len(visible_buttons)} видимых")
                output_lines.append("─" * 80)
                for idx, btn in enumerate(visible_buttons, 1):
                    try:
                        text = btn.text or ''
                        res_id = btn.get_attribute('resource-id') or ''
                        content_desc = btn.get_attribute('content-desc') or ''
                        output_lines.append(f"\n[{idx}] Text: '{text}'")
                        if res_id:
                            output_lines.append(f"    Resource ID: {res_id}")
                            output_lines.append(f"    ✅ Локатор: AppiumBy.ID, '{res_id}'")
                        if content_desc:
                            output_lines.append(f"    Content-desc: {content_desc}")
                            output_lines.append(f"    ✅ Локатор: AppiumBy.ACCESSIBILITY_ID, '{content_desc}'")
                        if text:
                            output_lines.append(f"    ✅ Локатор: AppiumBy.XPATH, '//android.widget.Button[@text=\"{text}\"]'")
                    except:
                        pass
                output_lines.append("")
        except Exception as e:
            output_lines.append(f"⚠️ Ошибка при поиске Button: {e}")
            output_lines.append("")
        
        # Поля ввода (EditText)
        try:
            edit_texts = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.EditText")
            visible_edits = [e for e in edit_texts[:10] if e.is_displayed()]
            if visible_edits:
                output_lines.append("─" * 80)
                output_lines.append(f"✏️ INPUT FIELDS (EditText): {len(visible_edits)} видимых")
                output_lines.append("─" * 80)
                for idx, et in enumerate(visible_edits, 1):
                    try:
                        text = et.text or ''
                        res_id = et.get_attribute('resource-id') or ''
                        hint = et.get_attribute('hint') or ''
                        output_lines.append(f"\n[{idx}] Text: '{text}' | Hint: '{hint}'")
                        if res_id:
                            output_lines.append(f"    Resource ID: {res_id}")
                            output_lines.append(f"    ✅ Локатор: AppiumBy.ID, '{res_id}'")
                        if hint:
                            output_lines.append(f"    Hint: {hint}")
                    except:
                        pass
                output_lines.append("")
        except Exception as e:
            output_lines.append(f"⚠️ Ошибка при поиске EditText: {e}")
            output_lines.append("")
        
        # ViewGroups с content-desc (часто используются для кнопок в React Native)
        try:
            view_groups = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.view.ViewGroup")
            clickable_groups = []
            for vg in view_groups[:30]:
                try:
                    content_desc = vg.get_attribute('content-desc') or ''
                    clickable = vg.get_attribute('clickable') == 'true'
                    if vg.is_displayed() and content_desc and clickable:
                        clickable_groups.append({
                            'content_desc': content_desc,
                            'resource_id': vg.get_attribute('resource-id') or ''
                        })
                except:
                    pass
            
            if clickable_groups:
                output_lines.append("─" * 80)
                output_lines.append(f"👆 CLICKABLE VIEWGROUPS (React Native buttons): {len(clickable_groups)}")
                output_lines.append("─" * 80)
                for idx, vg in enumerate(clickable_groups[:10], 1):
                    output_lines.append(f"\n[{idx}] Content-desc: '{vg['content_desc']}'")
                    output_lines.append(f"    ✅ Локатор: AppiumBy.ACCESSIBILITY_ID, '{vg['content_desc']}'")
                    if vg['resource_id']:
                        output_lines.append(f"    Resource ID: {vg['resource_id']}")
                        output_lines.append(f"    ✅ Локатор: AppiumBy.ID, '{vg['resource_id']}'")
                output_lines.append("")
        except Exception as e:
            output_lines.append(f"⚠️ Ошибка при поиске ViewGroup: {e}")
            output_lines.append("")
        
        # Скриншот
        output_lines.append("─" * 80)
        output_lines.append("📸 SCREENSHOT")
        output_lines.append("─" * 80)
        try:
            from src.utils.ui_helpers import take_screenshot
            screenshot_path = take_screenshot(
                self.driver,
                f"diag_{page_name}_{context_safe}.png"
            )
            output_lines.append(f"Сохранен: {screenshot_path}")
        except Exception as e:
            output_lines.append(f"⚠️ Не удалось сделать скриншот: {e}")
        output_lines.append("")
        
        # Записываем в файл
        output_lines.append("=" * 80)
        output_lines.append("Конец диагностики")
        output_lines.append("=" * 80)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        # Выводим краткую информацию в консоль
        print(f"\n📋 Диагностика сохранена: {filepath}")
        
        # Автоматически открываем файл
        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(filepath)
            elif system == "Darwin":  # macOS
                subprocess.run(['open', filepath])
            else:  # Linux
                subprocess.run(['xdg-open', filepath])
            print("✅ Файл открыт в редакторе")
        except Exception as e:
            print(f"⚠️ Не удалось автоматически открыть файл: {e}")
        
        return filepath

