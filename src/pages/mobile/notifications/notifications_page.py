"""Page Object: экран «Уведомления»."""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class NotificationsPage(BaseMobilePage):
    """Экран уведомлений."""

    page_title = "Notifications (Уведомления)"

    # Маркер экрана: заголовок «Уведомления»
    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        "//android.widget.TextView[@text='Уведомления']",
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Уведомления» по заголовку."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            'Экран "Уведомления" не найден (ожидался заголовок "Уведомления")',
        )
        print("✅ Экран 'Уведомления' открыт")

    def wait_loaded(self) -> "NotificationsPage":
        """Ждёт загрузки экрана «Уведомления» и возвращает self."""
        self.check_and_recover_app_state()
        return super().wait_loaded()

