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
from src.utils.ui_helpers import click_element_with_fallback


class BottomNav(BaseMobilePage):
    """Компонент нижней навигации (Главная / Записи / QR / Статистика / Профиль)."""

    TAB_MAIN = (AppiumBy.XPATH, '//android.widget.TextView[@text="Главная"]')
    TAB_BOOKINGS = (AppiumBy.XPATH, '//android.widget.TextView[@text="Записи"]')
    # Кнопка сканирования QR — иконка без текста.
    # Используем точный XPath из инспектора, а сам клик выполняем через click_element_with_fallback
    # (прямой клик → родительский кликабельный элемент → координаты центра).
    QR_SCAN_XPATH: str = (
        '//android.widget.FrameLayout[@resource-id="android:id/content"]/android.widget.FrameLayout'
        '/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup'
        '/android.view.ViewGroup[2]/android.view.ViewGroup/android.view.ViewGroup[1]/android.widget.FrameLayout'
        '/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup'
        '/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]'
        '/android.widget.FrameLayout/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup'
        '/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[2]/android.view.View'
        '/android.view.ViewGroup/android.view.ViewGroup/com.horcrux.svg.SvgView/com.horcrux.svg.GroupView'
        '/com.horcrux.svg.GroupView/com.horcrux.svg.PathView'
    )
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

    def click_qr_scan(self) -> "BottomNav":
        """Клик по кнопке сканирования QR (иконка без текста). Возвращает self."""
        click_element_with_fallback(
            self.driver,
            self.wait,
            self.QR_SCAN_XPATH,
            element_name="кнопка QR",
            timeout=20,
        )
        return self

    def open_qr(self):
        """
        Открыть QR-экран из таббара и дождаться его открытия.
        Возвращает Page Object QR-оверлея.
        """
        from src.pages.mobile.bookings.qr_overlay import QrOverlay

        self.click_qr_scan()
        return QrOverlay(self.driver).wait_opened()
