"""
Page Object: экран/лендинг «Health».

Открывается с главной по промо-баннеру «Health, Комплексная забота о себе, ИИ, БАДы, Врачи, Анализы».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class HealthPage(BaseMobilePage):
    """Экран/лендинг Health (комплексная забота о себе)."""

    page_title = "Health"

    # Маркер экрана: заголовок Health на целевом экране.
    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Комплексная забота о здоровье в одном приложении"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран Health."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Экран 'Health' не найден (ожидался заголовок 'Комплексная забота о здоровье в одном приложении')",
        )
        print("✅ Экран 'Health' открыт")

    def wait_loaded(self) -> "HealthPage":
        """Ждёт загрузки экрана Health и возвращает self."""
        self.check_and_recover_app_state()
        return super().wait_loaded()

