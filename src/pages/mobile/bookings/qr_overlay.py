from typing import TYPE_CHECKING

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage

if TYPE_CHECKING:
    from src.pages.mobile.bookings.bookings_page import BookingsPage


class QrOverlay(BaseMobilePage):
    """Оверлей / экран с QR-кодом, который открывается из таба «Записи»."""

    page_title = "QR overlay"

    TITLE_TEXT = "Покажите QR-код администратору клуба"
    SUBTITLE_TEXT = (
        "Это подтверждение личности нужно после регистрации или повторной авторизации "
        "в приложении. В следующий раз турникет пропустит вас сам"
    )

    TITLE = (
        AppiumBy.XPATH,
        f'//android.widget.TextView[@text="{TITLE_TEXT}"]',
    )
    SUBTITLE = (
        AppiumBy.XPATH,
        f'//android.widget.TextView[@text="{SUBTITLE_TEXT}"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверка, что QR-экран действительно открыт (оба текста на месте)."""
        self.wait_visible(
            self.TITLE,
            "Заголовок QR-экрана не найден",
        )
        self.wait_visible(
            self.SUBTITLE,
            "Подзаголовок QR-экрана не найден",
        )

    def wait_opened(self) -> "QrOverlay":
        """Дождаться открытия QR-экрана и вернуть self."""
        return self.wait_loaded()

    def assert_texts_present(self) -> "QrOverlay":
        """Бизнес-проверка: на экране есть оба ожидаемых текста."""
        self.assert_ui()
        print("✅ QR-экран открыт, оба текста отображаются")
        return self

    def close(self) -> "BookingsPage":
        """
        Закрыть QR-экран и вернуться на таб «Записи».
        Пока крестик кликается по фиксированным координатам (инкапсулировано здесь).
        """
        tap_x, tap_y = 100, 170
        self.driver.tap([(tap_x, tap_y)], 100)
        print(f"✅ QR-экран закрыт (тап по координатам {tap_x}, {tap_y})")

        from src.pages.mobile.bookings.bookings_page import BookingsPage

        return BookingsPage(self.driver).wait_loaded()

