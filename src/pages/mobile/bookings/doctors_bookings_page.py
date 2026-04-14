"""
Page Object: раздел записей к докторам внутри таба «Записи».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage


class DoctorsBookingsPage(BaseShellPage):
    """Экран выбора специальности врача («Доктора» → «Выберите специальность»)."""

    page_title = "Bookings — Доктора"

    # Заголовок рендерится как android.view.View, не android.widget.TextView
    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.view.View[@text="Выберите специальность"]',
    )

    # Табы
    TAB_FOR_ADULT = (AppiumBy.ACCESSIBILITY_ID, "Для взрослого")
    TAB_FOR_CHILD = (AppiumBy.ACCESSIBILITY_ID, "Для ребёнка")

    # Поиск специальности
    SEARCH_INPUT = (AppiumBy.CLASS_NAME, "android.widget.EditText")

    # Список специальностей (скролл-контейнер)
    SPECIALTIES_LIST = (AppiumBy.CLASS_NAME, "android.widget.ScrollView")
    DEFAULT_SPECIALTY_NAME = "3D УЗИ плода"

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет ключевые элементы экрана выбора специальности."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Заголовок 'Выберите специальность' не найден",
        )
        self.wait_visible(
            self.TAB_FOR_ADULT,
            "Таб 'Для взрослого' не найден",
        )
        self.wait_visible(
            self.TAB_FOR_CHILD,
            "Таб 'Для ребёнка' не найден",
        )
        self.wait_visible(
            self.SEARCH_INPUT,
            "Поле поиска специальности не найдено",
        )
        self.wait_visible(
            self.SPECIALTIES_LIST,
            "Список специальностей не найден",
        )
        print("✅ Экран 'Выберите специальность' открыт, основные элементы присутствуют")

    @staticmethod
    def _specialty_option(specialty_name: str):
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{specialty_name}"]')

    def select_specialty(
        self,
        specialty_name: str = DEFAULT_SPECIALTY_NAME,
    ) -> "DoctorsSchedulePage":
        """Выбрать специальность и перейти на страницу записи к врачу."""
        from src.pages.mobile.bookings.doctors_schedule_page import DoctorsSchedulePage

        self.click(self._specialty_option(specialty_name))
        return DoctorsSchedulePage(self.driver).wait_loaded()
