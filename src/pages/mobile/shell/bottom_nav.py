"""
Компонент нижней навигации (tabbar).

Общий shell-компонент, доступный на всех экранах внутри main-навигации.
Живёт в shell/ — не привязан к конкретному разделу.

Каждый метод open_* кликает по табу и возвращает Page Object целевого раздела,
уже проверив загрузку (wait_loaded).
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class BottomNav(BaseMobilePage):
    """Компонент нижней навигации (Главная / Записи / Статистика / Профиль)."""

    TAB_MAIN = (AppiumBy.XPATH, '//android.widget.TextView[@text="Главная"]')
    TAB_BOOKINGS = (AppiumBy.XPATH, '//android.widget.TextView[@text="Записи"]')
    TAB_STATS = (AppiumBy.XPATH, '//android.widget.TextView[@text="Статистика"]')
    TAB_PROFILE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Профиль"]')

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def open_main(self):
        """Перейти на таб «Главная» и дождаться загрузки. Возвращает HomePage."""
        from src.pages.mobile.home.home_page import HomePage

        self.click(self.TAB_MAIN)
        return HomePage(self.driver).wait_loaded()

    def open_bookings(self):
        """Перейти на таб «Записи» и дождаться загрузки. Возвращает BookingsPage."""
        from src.pages.mobile.bookings.bookings_page import BookingsPage

        self.click(self.TAB_BOOKINGS)
        return BookingsPage(self.driver).wait_loaded()

    def open_stats(self):
        """Перейти на таб «Статистика» и дождаться загрузки. Возвращает StatsPage."""
        from src.pages.mobile.stats.stats_page import StatsPage

        self.click(self.TAB_STATS)
        return StatsPage(self.driver).wait_loaded()

    def open_profile(self):
        """Перейти на таб «Профиль» и дождаться загрузки. Возвращает ProfilePage."""
        from src.pages.mobile.profile.profile_page import ProfilePage

        self.click(self.TAB_PROFILE)
        return ProfilePage(self.driver).wait_loaded()
