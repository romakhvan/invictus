"""
Page Object: экран описания конкретного клуба.

Открывается с главной по клику на карточку клуба внизу главного экрана
или из списка клубов.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class ClubDetailsPage(BaseMobilePage):
    """Экран с деталями конкретного клуба (описание, адрес, и т.п.)."""

    page_title = "Club Details (Клуб)"

    # Маркер экрана: любой заголовок, содержащий 'Invictus'.
    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "Invictus")]',
    )
    # Секция описания зала.
    ABOUT_HALL_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[@text="О зале"]')
    # Цена абонемента (меняется; проверяем только наличие символа валюты '₸').
    PRICE_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "на год")]')
    # CTA‑кнопка «Выбрать абонемент».
    CHOOSE_MEMBERSHIP_BUTTON = (
        AppiumBy.ACCESSIBILITY_ID,
        "Выбрать абонемент",
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран конкретного клуба."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Экран деталей клуба не найден (ожидался заголовок, содержащий 'Invictus')",
        )
        self.wait_visible(
            self.ABOUT_HALL_LABEL,
            "Экран деталей клуба: секция 'О зале' не найдена",
        )
        self.wait_visible(
            self.PRICE_LABEL,
            "Экран деталей клуба: цена абонемента (с символом '₸') не найдена",
        )
        self.wait_visible(
            self.CHOOSE_MEMBERSHIP_BUTTON,
            "Экран деталей клуба: кнопка 'Выбрать абонемент' не найдена",
        )
        print("✅ Экран деталей клуба открыт")

    def click_choose_membership(self) -> None:
        """Нажать кнопку «Выбрать абонемент» на экране клуба."""
        self.click(self.CHOOSE_MEMBERSHIP_BUTTON)
        print("✅ Нажата кнопка 'Выбрать абонемент' на экране клуба")

    def wait_loaded(self) -> "ClubDetailsPage":
        """Ждёт загрузки экрана деталей клуба и возвращает self."""
        self.check_and_recover_app_state()
        return super().wait_loaded()

