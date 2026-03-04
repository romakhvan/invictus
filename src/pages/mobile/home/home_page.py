"""
Page Object: Главный экран приложения (оболочка).

Контент зависит от типа пользователя (новый, с подпиской, с абонементом).
Используйте get_current_home_state() и get_content() для работы с нужным вариантом.
"""

from appium.webdriver import Remote
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from src.pages.mobile.base_mobile_page import BaseMobilePage
from src.pages.mobile.home.home_state import HomeState
from src.pages.mobile.home.content import (
    HomeNewUserContent,
    HomeSubscribedContent,
    HomeMemberContent,
)

# Порядок проверки состояний и соответствующие классы контента.
_STATE_DETECTORS = [
    (HomeState.NEW_USER, HomeNewUserContent),
    (HomeState.SUBSCRIBED, HomeSubscribedContent),
    (HomeState.MEMBER, HomeMemberContent),
]
_DETECT_TIMEOUT = 3


class HomePage(BaseMobilePage):
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
        print(f"✅ Главный экран открыт, состояние: {state.value}")

    def get_current_home_state(self) -> HomeState:
        """
        Определяет текущее состояние главного экрана по видимым маркерам контента.

        Returns:
            HomeState: NEW_USER, SUBSCRIBED, MEMBER или UNKNOWN.
        """
        for state, content_cls in _STATE_DETECTORS:
            try:
                self._wait(_DETECT_TIMEOUT).until(
                    EC.visibility_of_element_located(content_cls.DETECT_LOCATOR)
                )
                return state
            except TimeoutException:
                continue
        return HomeState.UNKNOWN

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
        self.assert_ui()
        return self
