"""
Page Object: таб «Записи».
"""

from typing import TYPE_CHECKING

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException

from src.pages.mobile.shell.base_shell_page import BaseShellPage

if TYPE_CHECKING:
    from src.pages.mobile.bookings.doctors_bookings_page import DoctorsBookingsPage
    from src.pages.mobile.bookings.events_bookings_page import EventsBookingsPage
    from src.pages.mobile.bookings.group_bookings_page import GroupBookingsPage
    from src.pages.mobile.bookings.personal_bookings_page import PersonalBookingsPage


class BookingsPage(BaseShellPage):
    """Раздел «Записи» (список записей/бронирований)."""

    page_title = "Bookings (Записи)"
    DEFAULT_BOOKINGS_CLUB_NAME = "Invictus Fitness Gagarin"

    # Ключевые элементы экрана «Записи»
    TITLE_MY_BOOKINGS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Мои записи"]',
    )
    EMPTY_STATE_TEXT = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Здесь будут ваши записи"]',
    )
    SECTION_PERSONAL_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Персональные"]',
    )
    SECTION_PERSONAL_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Доверьтесь тренеру"]',
    )
    SECTION_GROUP_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Групповые"]',
    )
    SECTION_GROUP_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Расписание и программы"]',
    )
    SECTION_DOCTORS_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Доктора"]',
    )
    SECTION_DOCTORS_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Список довереных докторов"]',
    )
    SECTION_EVENTS_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Ивенты"]',
    )
    SECTION_EVENTS_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Загляните в афишу"]',
    )
    SECTION_FAQ_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Вопросы и ответы"]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """
        Проверяет, что открыт экран «Записи» как таковой:
        заголовок и основные секции. Не завязан на пустое состояние.
        """
        self.wait_visible(
            self.TITLE_MY_BOOKINGS,
            "Заголовок 'Мои записи' не найден на экране 'Записи'",
        )
        self.wait_visible(
            self.SECTION_PERSONAL_TITLE,
            "Заголовок секции 'Персональные' не найден",
        )
        self.wait_visible(
            self.SECTION_GROUP_TITLE,
            "Заголовок секции 'Групповые' не найден",
        )
        self.wait_visible(
            self.SECTION_DOCTORS_TITLE,
            "Заголовок секции 'Доктора' не найден",
        )
        self.wait_visible(
            self.SECTION_EVENTS_TITLE,
            "Заголовок секции 'Ивенты' не найден",
        )
        self.wait_visible(
            self.SECTION_FAQ_TITLE,
            "Заголовок секции 'Вопросы и ответы' не найден",
        )
        print("✅ Экран 'Записи' открыт, основные секции присутствуют")

    def assert_empty_state(self) -> None:
        """
        Проверяет, что отображается пустое состояние (нет записей).

        Используйте в тестах, где явно нужен empty state.
        """
        self.wait_visible(
            self.EMPTY_STATE_TEXT,
            "Ожидался текст пустого состояния 'Здесь будут ваши записи', но он не найден",
        )
        print("✅ Экран 'Записи' в пустом состоянии")

    def _apply_default_club_if_city_selector_opened(self, timeout: int = 1) -> bool:
        """
        Если открылся экран выбора клуба/города — выбрать клуб по умолчанию и применить.

        Returns:
            True, если экран выбора клуба был обнаружен и обработан; иначе False.
        """
        from src.pages.mobile.common.city_selector_page import CitySelectorPage

        selector = CitySelectorPage(self.driver)
        try:
            selector.wait_visible(
                selector.ALL_CITIES_FILTER,
                'Экран выбора клуба/города не найден (ожидался фильтр "Все города")',
                timeout=timeout,
            )
            selector.select_club_and_apply(self.DEFAULT_BOOKINGS_CLUB_NAME)
            return True
        except TimeoutException:
            return False

    def open_personal_section(self) -> "PersonalBookingsPage":
        """
        Открыть секцию «Персональные» в табе «Записи».

        Если после клика появляется промежуточный экран выбора города/клуба,
        метод сам выбирает клуб по умолчанию и продолжает навигацию.
        """
        from src.pages.mobile.bookings.personal_bookings_page import (
            PersonalBookingsPage,
        )

        self.click(self.SECTION_PERSONAL_TITLE)

        personal = PersonalBookingsPage(self.driver)
        try:
            # Если целевая страница открылась сразу — возвращаем её.
            # Это приоритетнее, чем детект промежуточного экрана, потому что
            # некоторые элементы (например фильтры) могут совпадать по тексту.
            personal.wait_visible(
                personal.TAB_TRAINERS,
                "Экран 'Персональные' не открылся (не найден таб 'Тренеры')",
                timeout=1,
            )
            return personal.wait_loaded()
        except TimeoutException:
            pass

        self._apply_default_club_if_city_selector_opened(timeout=1)
        return personal.wait_loaded()

    def open_group_section(self) -> "GroupBookingsPage":
        """
        Открыть секцию «Групповые» в табе «Записи».

        Возвращает страницу групповых записей.
        """
        from src.pages.mobile.bookings.group_bookings_page import (
            GroupBookingsPage,
        )

        self.click(self.SECTION_GROUP_TITLE)
        self._apply_default_club_if_city_selector_opened(timeout=1)
        return GroupBookingsPage(self.driver).wait_loaded()

    def open_doctors_section(self) -> "DoctorsBookingsPage":
        """
        Открыть секцию «Доктора» в табе «Записи».

        Возвращает страницу записей к докторам.
        """
        from src.pages.mobile.bookings.doctors_bookings_page import (
            DoctorsBookingsPage,
        )

        self.click(self.SECTION_DOCTORS_TITLE)
        return DoctorsBookingsPage(self.driver).wait_loaded()

    def open_events_section(self) -> "EventsBookingsPage":
        """
        Открыть секцию «Ивенты» в табе «Записи».

        Возвращает страницу ивентов.
        """
        from src.pages.mobile.bookings.events_bookings_page import (
            EventsBookingsPage,
        )

        self.click(self.SECTION_EVENTS_TITLE)
        return EventsBookingsPage(self.driver).wait_loaded()
