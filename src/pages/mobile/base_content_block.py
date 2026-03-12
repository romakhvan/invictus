"""
Базовый класс и миксин для контент-блоков (секций) внутри мобильных страниц.

HomeNewUserContent, HomeSubscribedContent и т.п. — не самостоятельные экраны,
а части страницы (HomePage). Наследование от BaseContentBlock явно это отражает.
MobileInteractionMixin вынесен сюда для переиспользования в BaseMobilePage и BaseContentBlock.
"""

from typing import Optional, Tuple, Union, TypeAlias

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator: TypeAlias = Tuple[Union[AppiumBy, str], str]


class MobileInteractionMixin:
    """
    Миксин с методами взаимодействия с UI (клики, ожидания, видимость).
    Используется в BaseMobilePage и BaseContentBlock. Требует self.driver и self.wait.
    """

    def _wait(self, timeout: Optional[int] = None) -> WebDriverWait:
        """Если timeout None — используется дефолтный wait (20s), иначе новый WebDriverWait."""
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
        timeout: int = 20,
        take_screenshot_on_timeout: bool = True,
    ):
        """Ждёт видимости элемента и выбрасывает исключение с понятным сообщением."""
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
        """Ждёт присутствия элемента в DOM (не обязательно видимого)."""
        try:
            wait = self._wait(timeout)
            return wait.until(EC.presence_of_element_located(locator))
        except TimeoutException as e:
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
        self.wait = WebDriverWait(driver, 20)
