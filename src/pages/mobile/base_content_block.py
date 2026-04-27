"""
Базовый класс и миксин для контент-блоков (секций) внутри мобильных страниц.

HomeNewUserContent, HomeSubscribedContent и т.п. — не самостоятельные экраны,
а части страницы (HomePage). Наследование от BaseContentBlock явно это отражает.
MobileInteractionMixin вынесен сюда для переиспользования в BaseMobilePage и BaseContentBlock.
"""

from typing import Optional, Tuple, Union, TypeAlias
import os

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator: TypeAlias = Tuple[Union[AppiumBy, str], str]


class MobileInteractionMixin:
    """
    Миксин с методами взаимодействия с UI (клики, ожидания, видимость).
    Используется в BaseMobilePage и BaseContentBlock. Требует self.driver и self.wait.
    """

    def _wait(self, timeout: Optional[int] = None) -> WebDriverWait:
        """Если timeout None — используется дефолтный wait (10s), иначе новый WebDriverWait."""
        if timeout is None:
            return self.wait
        return WebDriverWait(self.driver, timeout)

    def _context_name(self) -> str:
        """Имя текущего контекста (страница/блок) для логов."""
        return (
            getattr(self, "page_title", None)
            or getattr(self, "content_title", None)
            or self.__class__.__name__
        )

    def _log_ui(self, message: str) -> None:
        """Единый формат детального UI-лога."""
        if not self._is_ui_logging_enabled():
            return
        print(f"🧭 [{self._context_name()}] {message}")

    @staticmethod
    def _is_ui_logging_enabled() -> bool:
        """Флаг подробных UI-логов (включается через pytest --mobile-ui-logs)."""
        return os.getenv("MOBILE_UI_LOGS", "0").lower() in {"1", "true", "yes", "on"}

    def _element_snapshot(self, element) -> str:
        """Краткая диагностическая информация об элементе."""
        try:
            text = (element.text or "").strip()
        except Exception:
            text = ""
        try:
            content_desc = (element.get_attribute("content-desc") or "").strip()
        except Exception:
            content_desc = ""
        try:
            resource_id = (element.get_attribute("resource-id") or "").strip()
        except Exception:
            resource_id = ""
        try:
            enabled = element.is_enabled()
        except Exception:
            enabled = "?"
        try:
            displayed = element.is_displayed()
        except Exception:
            displayed = "?"
        return (
            f"text='{text}' | content-desc='{content_desc}' | "
            f"resource-id='{resource_id}' | displayed={displayed} | enabled={enabled}"
        )

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
        locator_str = self._locator_str(locator)
        wait_timeout = timeout if timeout is not None else 10
        self._log_ui(f"WAIT CLICKABLE ({wait_timeout}s): {locator_str}")
        wait = self._wait(timeout)
        element = wait.until(EC.element_to_be_clickable(locator))
        self._log_ui(f"ELEMENT CLICKABLE: {self._element_snapshot(element)}")
        self._log_ui(f"CLICK: {locator_str}")
        element.click()
        self._log_ui(f"CLICK DONE: {locator_str}")

    def send_keys(self, locator: Locator, text: str, timeout: Optional[int] = None):
        """Ввод текста в поле."""
        locator_str = self._locator_str(locator)
        wait_timeout = timeout if timeout is not None else 10
        self._log_ui(f"WAIT PRESENT ({wait_timeout}s): {locator_str}")
        wait = self._wait(timeout)
        element = wait.until(EC.presence_of_element_located(locator))
        self._log_ui(f"ELEMENT FOUND: {self._element_snapshot(element)}")
        self._log_ui(f"SEND_KEYS: {locator_str} | value='{text}'")
        element.clear()
        element.send_keys(text)
        self._log_ui(f"SEND_KEYS DONE: {locator_str}")

    def get_text(self, locator: Locator, timeout: Optional[int] = None) -> str:
        """Получить текст элемента."""
        locator_str = self._locator_str(locator)
        wait_timeout = timeout if timeout is not None else 10
        self._log_ui(f"WAIT PRESENT ({wait_timeout}s): {locator_str}")
        wait = self._wait(timeout)
        element = wait.until(EC.presence_of_element_located(locator))
        value = element.text
        self._log_ui(f"GET_TEXT: {locator_str} -> '{value}'")
        return value

    def is_visible(self, locator: Locator, timeout: Optional[int] = None) -> bool:
        """Проверка видимости элемента."""
        locator_str = self._locator_str(locator)
        wait_timeout = timeout if timeout is not None else 5
        self._log_ui(f"CHECK VISIBLE ({wait_timeout}s): {locator_str}")
        try:
            wait = self._wait(timeout if timeout is not None else 5)
            element = wait.until(EC.visibility_of_element_located(locator))
            self._log_ui(f"VISIBLE: {locator_str} | {self._element_snapshot(element)}")
            return True
        except TimeoutException:
            self._log_ui(f"NOT VISIBLE: {locator_str}")
            return False

    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 1000):
        """Свайп по экрану."""
        self.driver.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe_by_w3c_actions(self, start_x: int, start_y: int, end_x: int, end_y: int) -> None:
        """W3C touch swipe, useful when driver.swipe is unstable on a screen."""
        self._log_ui(f"W3C SWIPE: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(
            self.driver,
            mouse=PointerInput(interaction.POINTER_TOUCH, "touch"),
        )
        actions.w3c_actions.pointer_action.move_to_location(start_x, start_y)
        actions.w3c_actions.pointer_action.pointer_down()
        actions.w3c_actions.pointer_action.move_to_location(end_x, end_y)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def tap_by_coordinates(
        self,
        x: int,
        y: int,
        duration_ms: int = 100,
        action_name: str = "Тап по координатам",
    ) -> None:
        """Универсальный tap по координатам для сложных/нестабильных UI-элементов."""
        self.driver.tap([(x, y)], duration_ms)
        print(f"✅ {action_name} ({x}, {y})")

    def hide_keyboard(self) -> bool:
        """Пытается скрыть клавиатуру и возвращает, удалось ли это сделать."""
        try:
            self.driver.hide_keyboard()
            self._log_ui("HIDE KEYBOARD")
            return True
        except Exception as exc:
            self._log_ui(f"HIDE KEYBOARD SKIPPED: {type(exc).__name__}")
            return False

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
        page = getattr(self, "page_title", None) or getattr(self, "content_title", None) or self.__class__.__name__
        error_text = f"[{page}] TIMEOUT {timeout}s: {msg}\nLocator: {locator_str}"
        if take_screenshot_on_timeout:
            try:
                from datetime import datetime
                from src.utils.ui_helpers import take_screenshot
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_page = str(page).replace(" ", "_").replace("(", "").replace(")", "")
                path = take_screenshot(self.driver, f"timeout_{safe_page}_{ts}.png")
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
        timeout: int = 10,
        take_screenshot_on_timeout: bool = True,
    ):
        """Ждёт видимости элемента и выбрасывает исключение с понятным сообщением."""
        locator_str = self._locator_str(locator)
        self._log_ui(f"WAIT VISIBLE ({timeout}s): {locator_str}")
        try:
            wait = self._wait(timeout)
            element = wait.until(EC.visibility_of_element_located(locator))
            self._log_ui(f"VISIBLE DONE: {locator_str} | {self._element_snapshot(element)}")
            return element
        except TimeoutException as e:
            self._log_ui(f"VISIBLE TIMEOUT ({timeout}s): {locator_str} | {error_message}")
            self._raise_timeout_with_context(
                locator, error_message, timeout, take_screenshot_on_timeout, cause=e
            )

    def wait_invisible(
        self,
        locator: Locator,
        error_message: str = "Element is still visible",
        timeout: int = 10,
    ):
        """Ждёт, пока элемент станет невидимым (или исчезнет из DOM)."""
        locator_str = self._locator_str(locator)
        self._log_ui(f"WAIT INVISIBLE ({timeout}s): {locator_str}")
        try:
            wait = self._wait(timeout)
            wait.until(EC.invisibility_of_element_located(locator))
            self._log_ui(f"INVISIBLE DONE: {locator_str}")
        except TimeoutException as e:
            self._log_ui(f"INVISIBLE TIMEOUT ({timeout}s): {locator_str} | {error_message}")
            self._raise_timeout_with_context(locator, error_message, timeout, cause=e)

    def wait_clickable(
        self,
        locator: Locator,
        error_message: str = "Element is not clickable",
        timeout: int = 10,
        take_screenshot_on_timeout: bool = True,
    ):
        """Ждёт, пока элемент станет кликабельным, и возвращает его."""
        locator_str = self._locator_str(locator)
        self._log_ui(f"WAIT CLICKABLE ({timeout}s): {locator_str}")
        try:
            wait = self._wait(timeout)
            element = wait.until(EC.element_to_be_clickable(locator))
            self._log_ui(f"CLICKABLE DONE: {locator_str} | {self._element_snapshot(element)}")
            return element
        except TimeoutException as e:
            self._log_ui(f"CLICKABLE TIMEOUT ({timeout}s): {locator_str} | {error_message}")
            self._raise_timeout_with_context(
                locator, error_message, timeout, take_screenshot_on_timeout, cause=e
            )

    def wait_present(
        self,
        locator: Locator,
        error_message: str = "Element not found",
        timeout: int = 10,
        take_screenshot_on_timeout: bool = True,
    ):
        """Ждёт присутствия элемента в DOM (не обязательно видимого)."""
        locator_str = self._locator_str(locator)
        self._log_ui(f"WAIT PRESENT ({timeout}s): {locator_str}")
        try:
            wait = self._wait(timeout)
            element = wait.until(EC.presence_of_element_located(locator))
            self._log_ui(f"PRESENT DONE: {locator_str} | {self._element_snapshot(element)}")
            return element
        except TimeoutException as e:
            self._log_ui(f"PRESENT TIMEOUT ({timeout}s): {locator_str} | {error_message}")
            self._raise_timeout_with_context(
                locator, error_message, timeout, take_screenshot_on_timeout, cause=e
            )


class BaseContentBlock(MobileInteractionMixin):
    """
    Базовый класс для контент-блоков (секций) внутри страницы.

    Не самостоятельный экран: нет своего lifecycle (wait_loaded), нет перехода на другую страницу.
    Используется для HomeNewUserContent, HomeSubscribedContent, HomeMemberContent и т.п.
    Для контекста в сообщениях об ошибках можно задать атрибут content_title или page_title.
    """

    content_title: Optional[str] = None  # опционально, для сообщений об ошибках

    def __init__(self, driver: Remote):
        self.driver: Remote = driver
        self.wait = WebDriverWait(driver, 10)
