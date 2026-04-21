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
    from src.pages.mobile.bookings.doctors_schedule_page import DoctorsSchedulePage
    from src.pages.mobile.bookings.events_bookings_page import EventsBookingsPage
    from src.pages.mobile.bookings.faq_bookings_page import FaqBookingsPage
    from src.pages.mobile.bookings.group_bookings_page import GroupBookingsPage
    from src.pages.mobile.bookings.personal_bookings_page import PersonalBookingsPage


class BookingsPage(BaseShellPage):
    """Раздел «Записи» (список записей/бронирований)."""

    page_title = "Bookings (Записи)"
    DEFAULT_BOOKINGS_CLUB_NAME = "Invictus Fitness Gagarin"
    DEFAULT_DOCTORS_CITY_NAME = "Алматы"
    DEFAULT_DOCTORS_SPECIALTY_NAME = "3D УЗИ плода"

    # Ключевые элементы экрана «Записи»
    TITLE_MY_BOOKINGS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Куда хотите пойти?"]',
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

    # Табы переключения вида («Все возможности» / «Записи»)
    TAB_ALL_ACTIVITIES = (AppiumBy.ACCESSIBILITY_ID, "Все возможности")
    TAB_RECORDS = (AppiumBy.ACCESSIBILITY_ID, "Записи")
    TAB_SCHEDULE = TAB_RECORDS

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
        from src.pages.mobile.common.club_filter_component import ClubFilterComponent

        selector = ClubFilterComponent(self.driver)
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

    def _apply_default_doctors_city_if_selector_opened(self, timeout: int = 1) -> bool:
        """
        Если для раздела «Доктора» открылся список городов, выбрать город
        по умолчанию и продолжить навигацию.
        """
        from src.pages.mobile.common.club_filter_component import ClubFilterComponent

        selector = ClubFilterComponent(self.driver)
        if selector.get_state(timeout=timeout) != "cities_list":
            return False

        selector.select_default_city(self.DEFAULT_DOCTORS_CITY_NAME)
        return True

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

    def open_doctors_section(self) -> "DoctorsSchedulePage":
        """
        Открыть секцию «Доктора» в табе «Записи».

        Возвращает страницу записи к врачу.
        """
        from src.pages.mobile.bookings.doctors_bookings_page import (
            DoctorsBookingsPage,
        )
        from src.pages.mobile.bookings.doctors_schedule_page import (
            DoctorsSchedulePage,
        )

        self.click(self.SECTION_DOCTORS_TITLE)
        doctors = DoctorsBookingsPage(self.driver)
        doctors_schedule = DoctorsSchedulePage(self.driver)

        try:
            doctors_schedule.wait_visible(
                doctors_schedule.DETECT_LOCATOR,
                "Экран 'Запись к врачу' не открылся сразу",
                timeout=1,
            )
            return doctors_schedule.wait_loaded()
        except TimeoutException:
            pass

        try:
            doctors.wait_visible(
                doctors.DETECT_LOCATOR,
                "Экран 'Доктора' не открылся сразу (не найден заголовок 'Выберите специальность')",
                timeout=1,
            )
            doctors.wait_loaded()
            return doctors.select_specialty(self.DEFAULT_DOCTORS_SPECIALTY_NAME)
        except TimeoutException:
            pass

        if self._apply_default_doctors_city_if_selector_opened(timeout=1):
            try:
                doctors_schedule.wait_visible(
                    doctors_schedule.DETECT_LOCATOR,
                    "Экран 'Запись к врачу' не открылся после выбора города",
                    timeout=2,
                )
                return doctors_schedule.wait_loaded()
            except TimeoutException:
                doctors.wait_loaded()
                return doctors.select_specialty(self.DEFAULT_DOCTORS_SPECIALTY_NAME)

        try:
            doctors_schedule.wait_visible(
                doctors_schedule.DETECT_LOCATOR,
                "Экран 'Запись к врачу' не открылся",
                timeout=2,
            )
            return doctors_schedule.wait_loaded()
        except TimeoutException:
            doctors.wait_loaded()
            return doctors.select_specialty(self.DEFAULT_DOCTORS_SPECIALTY_NAME)

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

    def open_faq_section(self) -> "FaqBookingsPage":
        """
        Открыть секцию «Вопросы и ответы» в табе «Записи».

        Возвращает страницу FAQ.
        """
        from src.pages.mobile.bookings.faq_bookings_page import FaqBookingsPage

        self.click(self.SECTION_FAQ_TITLE)
        return FaqBookingsPage(self.driver).wait_loaded()

    def switch_to_all_activities_tab(self) -> "BookingsPage":
        """Переключиться на таб «Все возможности»."""
        self.click(self.TAB_ALL_ACTIVITIES)
        self.wait_visible(
            self.SECTION_PERSONAL_TITLE,
            "Секции не появились после переключения на таб 'Все возможности'",
        )
        return self

    def switch_to_schedule_tab(self) -> "BookingsPage":
        """Переключиться на таб «Записи»."""
        self.click(self.TAB_SCHEDULE)
        self.wait_invisible(
            self.SECTION_PERSONAL_TITLE,
            "Секции не исчезли после переключения на таб 'Записи'",
        )
        return self
