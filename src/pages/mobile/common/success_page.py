"""Common success screen shown after completed mobile operations."""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class SuccessPage(BaseMobilePage):
    """Generic success-result screen with a reward/details text."""

    page_title = "Success (Успешное завершение)"

    TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Ура!"]',
    )
    SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Вы получили"]',
    )
    GO_TO_MAIN_BUTTON = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="На главную"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    @staticmethod
    def reward_text_locator(reward_text: str):
        return (
            AppiumBy.XPATH,
            f'//android.widget.TextView[@text="{reward_text}"]',
        )

    def assert_ui(self) -> None:
        """Assert that the common success screen shell is visible."""
        self.wait_visible(self.TITLE, "Заголовок 'Ура!' не найден на success-экране")
        self.wait_visible(self.SUBTITLE, "Текст 'Вы получили' не найден на success-экране")
        self.wait_visible(
            self.GO_TO_MAIN_BUTTON,
            "Кнопка 'На главную' не найдена на success-экране",
        )
        print("✅ Success-экран открыт")

    def assert_reward_text_visible(self, reward_text: str, timeout: int = 10) -> None:
        """Assert the operation-specific success details are visible."""
        self.wait_visible(
            self.reward_text_locator(reward_text),
            f"Текст результата '{reward_text}' не найден на success-экране",
            timeout=timeout,
        )
        print(f"✅ На success-экране отображается результат: {reward_text}")

    def click_go_to_main(self) -> None:
        """Tap the button returning from success screen to home."""
        self.click(self.GO_TO_MAIN_BUTTON)
        print("✅ Нажата кнопка 'На главную'")
