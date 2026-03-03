"""
Page Object: Экран завершения онбординга «Профиль готов».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support import expected_conditions as EC

from src.pages.mobile.base_mobile_page import BaseMobilePage


class OnboardingCompletePage(BaseMobilePage):
    """Page Object для экрана «Добро пожаловать, {name}!» / «Профиль готов»."""

    page_title = "Onboarding Complete (Профиль готов)"

    WELCOME_TEXT = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().textContains("Добро пожаловать").className("android.widget.TextView")'
    )
    PROFILE_READY = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("Профиль готов").className("android.widget.TextView")'
    )
    GO_TO_MAIN_BUTTON = (
        AppiumBy.ANDROID_UIAUTOMATOR,
        'new UiSelector().text("На главную").className("android.widget.TextView")'
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет наличие ключевых элементов экрана завершения онбординга."""
        self.ensure_app_is_active()
        self.wait_present(self.WELCOME_TEXT, "Текст приветствия не найден")
        self.wait_present(self.PROFILE_READY, "Текст 'Профиль готов' не найден")
        self.wait_visible(self.GO_TO_MAIN_BUTTON, "Кнопка 'На главную' не найдена")
        print("✅ Экран завершения онбординга открыт, все элементы присутствуют")

    def get_displayed_name(self) -> str:
        """
        Извлекает имя из приветствия «Добро пожаловать, {name}!».

        Returns:
            Имя, отображаемое в приветствии.
        """
        element = self.wait.until(EC.presence_of_element_located(self.WELCOME_TEXT))
        text = element.text  # "Добро пожаловать, Appium!"
        prefix = "Добро пожаловать, "
        suffix = "!"
        if text.startswith(prefix) and text.endswith(suffix):
            return text[len(prefix) : -len(suffix)].strip()
        return text

    def verify_displayed_name(self, expected_name: str) -> bool:
        """
        Проверяет, что в приветствии отображается ожидаемое имя.

        Args:
            expected_name: Имя, введённое на странице имени (например, из NamePage).

        Returns:
            True если отображаемое имя совпадает с ожидаемым.
        """
        displayed = self.get_displayed_name()
        return displayed == expected_name

    def click_go_to_main(self) -> None:
        """Нажать кнопку «На главную»."""
        self.ensure_app_is_active()
        self.click(self.GO_TO_MAIN_BUTTON)
        print("✅ Нажата кнопка 'На главную'")
