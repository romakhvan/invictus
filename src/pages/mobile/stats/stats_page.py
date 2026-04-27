"""
Page Object: таб «Статистика».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.shell.base_shell_page import BaseShellPage
from src.utils.date_utils import current_month_str, current_week_range_str, current_year_str


class StatsPage(BaseShellPage):
    """Раздел «Статистика» (прогресс и аналитика тренировок)."""

    page_title = "Stats (Статистика)"
    # Ключевые элементы экрана «Статистика»
    TITLE_MY_STATS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Моя статистика"]',
    )
    EMPTY_STATE_LINE1 = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Тут появятся время в зале и история посещений"]',
    )
    EMPTY_STATE_LINE2 = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Ходите на тренировки, а потом заглядывайте сюда"]',
    )
    CTA_SELECT_SUBSCRIPTION = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Выбрать абонемент"]',
    )
    INBODY_ENTRYPOINT = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="InBody"]',
    )
    STATISTICS_SEGMENT = (
        AppiumBy.XPATH,
        '(//android.widget.TextView[@text="Статистика"])[1]',
    )
    ACTUAL_STATS_STREAK_LABEL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="НЕДЕЛИ ПОДРЯД"]',
    )
    ACTUAL_STATS_WEEK_FILTER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Неделя"]',
    )
    ACTUAL_STATS_MONTH_FILTER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Месяц"]',
    )
    ACTUAL_STATS_YEAR_FILTER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Год"]',
    )
    ACTUAL_STATS_HOURS_LABEL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Часы"]',
    )
    ACTUAL_STATS_TIME_IN_GYM_LABEL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Время в зале"]',
    )
    ACTUAL_STATS_VISITS_LABEL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Посещения"]',
    )
    WEEK_PERIOD_RANGE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, " - ")]',
    )
    CURRENT_PERIOD_RANGE = WEEK_PERIOD_RANGE

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def _current_week_period_locator(self):
        """Locator for the week header shown in Week mode, e.g. '27 апреля - 03 мая'."""
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{current_week_range_str()}"]')

    def _current_month_period_locator(self):
        """Locator for the month header shown in Month mode, e.g. 'апрель 2026'."""
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{current_month_str()}"]')

    def _current_year_period_locator(self):
        """Locator for the year header shown in Year mode, e.g. '2026'."""
        return (AppiumBy.XPATH, f'//android.widget.TextView[@text="{current_year_str()}"]')

    def _visible_period_locator(self):
        """Return the currently visible period header locator."""
        period_locators = (
            self._current_month_period_locator(),
            self._current_year_period_locator(),
            self.WEEK_PERIOD_RANGE,
        )
        for locator in period_locators:
            if self.is_visible(locator, timeout=1):
                return locator
        return self.WEEK_PERIOD_RANGE

    def _wait_visible_actual_stats_metric(self) -> None:
        """Wait for the metric marker used by the currently selected Stats period."""
        if self.is_visible(self.ACTUAL_STATS_HOURS_LABEL, timeout=1):
            self.wait_visible(
                self.ACTUAL_STATS_HOURS_LABEL,
                "Метрика 'Часы' не найдена на экране статистики клиента",
            )
            self.wait_visible(
                self._current_week_period_locator(),
                "Диапазон дат текущей недели не найден на экране статистики клиента",
            )
            return

        self.wait_visible(
            self.ACTUAL_STATS_VISITS_LABEL,
            "Метрика 'Посещения' не найдена на экране статистики клиента",
        )

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Статистика» в одном из поддержанных состояний."""
        self.wait_visible(
            self.TITLE_MY_STATS,
            "Заголовок 'Моя статистика' не найден на экране 'Статистика'",
        )
        if self.is_visible(self.EMPTY_STATE_LINE1, timeout=3):
            self.wait_visible(
                self.CTA_SELECT_SUBSCRIPTION,
                "Кнопка 'Выбрать абонемент' не найдена",
            )
            print("✅ Экран 'Статистика' открыт: пустое состояние статистики")
            return

        if self.is_visible(self.ACTUAL_STATS_STREAK_LABEL, timeout=3):
            self.wait_visible(
                self.ACTUAL_STATS_WEEK_FILTER,
                "Фильтр 'Неделя' не найден на экране статистики клиента",
            )
            self.wait_visible(
                self.ACTUAL_STATS_MONTH_FILTER,
                "Фильтр 'Месяц' не найден на экране статистики клиента",
            )
            self.wait_visible(
                self.ACTUAL_STATS_YEAR_FILTER,
                "Фильтр 'Год' не найден на экране статистики клиента",
            )
            self._wait_visible_actual_stats_metric()
            print("✅ Экран 'Статистика' открыт: статистика клиента")
            return

        raise AssertionError(
            "Экран 'Статистика' открыт, но не найдено ни пустое состояние, "
            "ни состояние InBody, ни статистика клиента"
        )

    def open_subscription_selection(self):
        """Нажать CTA «Выбрать абонемент» и открыть экран выбора клуба/абонемента."""
        from src.pages.mobile.clubs.clubs_page import ClubsPage

        if not self.is_visible(self.CTA_SELECT_SUBSCRIPTION, timeout=2):
            self.click(self.STATISTICS_SEGMENT)
            self.wait_visible(
                self.EMPTY_STATE_LINE1,
                "Текст пустого состояния статистики не найден после переключения сегмента",
            )

        self.click(self.CTA_SELECT_SUBSCRIPTION)
        return ClubsPage(self.driver).wait_loaded()

    def assert_inbody_entrypoint_visible(self) -> "StatsPage":
        """Verify that the InBody entrypoint is visible without opening it."""
        self.wait_visible(
            self.INBODY_ENTRYPOINT,
            "Entrypoint 'InBody' is not visible on the Stats screen",
        )
        return self

    def select_month_period(self) -> "StatsPage":
        """Switch the actual statistics period to Month."""
        self.click(self.ACTUAL_STATS_MONTH_FILTER)
        self.wait_visible(
            self.ACTUAL_STATS_VISITS_LABEL,
            "Metric 'Посещения' is not visible after selecting the Month period",
        )
        self.wait_visible(
            self._current_month_period_locator(),
            "Month header is not visible after selecting the Month period",
        )
        return self

    def select_week_period(self) -> "StatsPage":
        """Switch the actual statistics period to Week."""
        self.click(self.ACTUAL_STATS_WEEK_FILTER)
        self.wait_visible(
            self.ACTUAL_STATS_HOURS_LABEL,
            "Metric 'Часы' is not visible after selecting the Week period",
        )
        self.wait_visible(
            self._current_week_period_locator(),
            "Week date range is not visible after selecting the Week period",
        )
        return self

    def select_year_period(self) -> "StatsPage":
        """Switch the actual statistics period to Year."""
        self.click(self.ACTUAL_STATS_YEAR_FILTER)
        self.wait_visible(
            self.ACTUAL_STATS_VISITS_LABEL,
            "Metric 'Посещения' is not visible after selecting the Year period",
        )
        self.wait_visible(
            self._current_year_period_locator(),
            "Year header is not visible after selecting the Year period",
        )
        return self

    def open_datepicker(self) -> "StatsPage":
        """Open the datepicker by tapping the current statistics date range."""
        period_locator = self._visible_period_locator()
        self.wait_visible(
            period_locator,
            "Current Stats date range is not visible",
        )
        self.click(period_locator)
        return self

    def open_inbody(self):
        """Открыть модуль InBody из раздела «Статистика»."""
        from src.pages.mobile.stats.inbody_page import InBodyPage

        self.click(self.INBODY_ENTRYPOINT)
        return InBodyPage(self.driver).wait_loaded()
