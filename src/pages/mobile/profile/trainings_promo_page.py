"""
Page Object: промо-экран «Персональные тренировки».

Открывается из таба «Профиль» по кнопке «Добавить услугу».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class TrainingsPromoPage(BaseMobilePage):
    """Промо-экран услуги «Персональные тренировки» с описанием и CTA."""

    page_title = "Trainings Promo (Персональные тренировки)"

    SUBSCRIPTION_ONLY_BADGE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Только с абонементом"]',
    )
    PERSONAL_TRAININGS_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Персональные тренировки"]',
    )

    DETECT_LOCATORS = (SUBSCRIPTION_ONLY_BADGE, PERSONAL_TRAININGS_TITLE)

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт промо-экран «Персональные тренировки»."""
        self.wait_visible(
            self.SUBSCRIPTION_ONLY_BADGE,
            "Промо-экран тренировок: бейдж 'Только с абонементом' не найден",
        )
        self.wait_visible(
            self.PERSONAL_TRAININGS_TITLE,
            "Промо-экран тренировок: заголовок 'Персональные тренировки' не найден",
        )
        print("✅ Промо-экран 'Персональные тренировки' открыт")
