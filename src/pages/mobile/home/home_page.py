"""
Page Object: Главный экран приложения (оболочка).

Контент зависит от типа пользователя (новый, с подпиской, с абонементом).
Используйте get_current_home_state() и get_content() для работы с нужным вариантом.
"""

import time

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.config.app_config import IMPLICIT_WAIT
from src.pages.mobile.shell.base_shell_page import BaseShellPage
from src.pages.mobile.home.home_state import HomeState
from src.pages.mobile.home.content import (
    HomeNewUserContent,
    HomeRabbitHoleContent,
    HomeSubscribedContent,
    HomeMemberContent,
)

# Порядок проверки состояний и соответствующие классы контента.
_STATE_DETECTORS = [
    (HomeState.RABBIT_HOLE, HomeRabbitHoleContent),
    (HomeState.NEW_USER, HomeNewUserContent),
    (HomeState.SUBSCRIBED, HomeSubscribedContent),
    (HomeState.MEMBER, HomeMemberContent),
]
_WAIT_LOADED_TIMEOUT = 10
_STATE_SCAN_INTERVAL = 0.2
_NOTIFICATION_PERMISSION_ALLOW = (AppiumBy.ID, "com.android.permissioncontroller:id/permission_allow_button")


def _dismiss_notification_permission_if_present(driver: Remote) -> bool:
    """Закрывает системный диалог разрешения уведомлений, если он открыт."""
    try:
        driver.implicitly_wait(0)
        for el in driver.find_elements(*_NOTIFICATION_PERMISSION_ALLOW):
            if el.is_displayed():
                el.click()
                print("ℹ️ Закрыт диалог разрешения уведомлений")
                return True
        return False
    except Exception:
        return False
    finally:
        driver.implicitly_wait(IMPLICIT_WAIT)


def _detect_locators(content_cls):
    return getattr(content_cls, "DETECT_LOCATORS", (content_cls.DETECT_LOCATOR,))


def _has_visible_element(driver: Remote, locator) -> bool:
    by, value = locator
    for element in driver.find_elements(by, value):
        try:
            if element.is_displayed():
                return True
        except Exception:
            continue
    return False


class HomePage(BaseShellPage):
    """
    Оболочка главного экрана: общая валидация и определение типа контента.
    Конкретные элементы и действия — в классах *Content.
    """

    page_title = "Home (Главный экран)"

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что отображается один из известных вариантов главного экрана."""
        state = self.get_current_home_state()
        if state == HomeState.UNKNOWN:
            raise AssertionError(
                "Главный экран не распознан: ни один из маркеров состояний (new user / subscribed / member) не найден. "
                "Уточните DETECT_LOCATOR в content-классах."
            )
        print(f"✅ Главный экран открыт, состояние: {state.value}, все элементы присутствуют")

    def get_current_home_state(self) -> HomeState:
        """
        Определяет текущее состояние главного экрана по видимым маркерам контента.

        Returns:
            HomeState: NEW_USER, SUBSCRIBED, MEMBER или UNKNOWN.
        """
        try:
            self.driver.implicitly_wait(0)
            for state, content_cls in _STATE_DETECTORS:
                if any(
                    _has_visible_element(self.driver, locator)
                    for locator in _detect_locators(content_cls)
                ):
                    return state
            return HomeState.UNKNOWN
        finally:
            self.driver.implicitly_wait(IMPLICIT_WAIT)

    def get_content(self):
        """
        Возвращает объект контента для текущего состояния главного экрана.

        Returns:
            HomeNewUserContent | HomeSubscribedContent | HomeMemberContent

        Raises:
            ValueError: Если состояние не удалось определить (UNKNOWN).
        """
        state = self.get_current_home_state()
        if state == HomeState.UNKNOWN:
            raise ValueError(
                "Не удалось определить тип главного экрана. Проверьте DETECT_LOCATOR в content-классах."
            )
        for s, content_cls in _STATE_DETECTORS:
            if s == state:
                return content_cls(self.driver)
        raise ValueError(f"Нет класса контента для состояния {state}")

    def wait_loaded(self) -> "HomePage":
        """Ждёт загрузки главного экрана (любого из известных состояний) и возвращает self."""
        if self.page_title:
            self.print_page_header(self.page_title)
        deadline = time.monotonic() + _WAIT_LOADED_TIMEOUT
        while self.get_current_home_state() == HomeState.UNKNOWN:
            if time.monotonic() >= deadline:
                break
            _dismiss_notification_permission_if_present(self.driver)
            time.sleep(_STATE_SCAN_INTERVAL)
        self.assert_ui()
        return self
