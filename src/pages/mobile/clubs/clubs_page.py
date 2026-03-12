"""
Page Object: экран «Клубы» (список клубов).

Открывается с главной по кнопке «Клубы» и с других экранов приложения.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class ClubsPage(BaseMobilePage):
    """Экран списка клубов."""

    page_title = "Clubs (Клубы)"

    # Ключевые элементы экрана
    # Фильтр по городам в верхней части экрана
    FILTER_ALL_CITIES = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Все города"]',
    )

    # табы‑фильтры»/«фильтры клубов
    CLUB_INVICTUS_GO = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Invictus GO"]',
    )
    CLUB_INVICTUS_FITNESS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Invictus Fitness"]',
    )
    CLUB_INVICTUS_GIRLS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Invictus Girls"]',
    )

    # Карточка клуба Invictus GO: текст начинается с "Invictus GO "
    CLUB_CARD_INVICTUS_GO = (
        AppiumBy.XPATH,
        '//android.widget.TextView[starts-with(@text, "Invictus GO1 ")]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Клубы»."""
        # Основной маркер — фильтр «Все города»
        self.wait_visible(
            self.FILTER_ALL_CITIES,
            "Экран 'Клубы': фильтр 'Все города' не найден",
        )

        # Дополнительно убеждаемся, что видна хотя бы одна карточка клуба
        any_club_visible = (
            self.is_visible(self.CLUB_INVICTUS_GO, timeout=5)
            or self.is_visible(self.CLUB_INVICTUS_FITNESS, timeout=5)
            or self.is_visible(self.CLUB_INVICTUS_GIRLS, timeout=5)
        )
        if not any_club_visible:
            raise AssertionError(
                "Экран 'Клубы' открыт, но ни один из ожидаемых клубов "
                "('Invictus GO', 'Invictus Fitness', 'Invictus Girls') не найден."
            )

        print("✅ Экран 'Клубы' открыт: фильтр и клубы видимы")

    def assert_invictus_go_club_present(self) -> None:
        """
        Проверяет, что на экране есть хотя бы одна карточка клуба 'Invictus GO *'.
        Суффикс после 'Invictus GO ' может меняться (Baitursynov и др.).
        """
        self.wait_visible(
            self.CLUB_CARD_INVICTUS_GO,
            "Ожидалась карточка клуба 'Invictus GO *', но она не найдена",
        )

    def wait_loaded(self) -> "ClubsPage":
        """
        Ждёт загрузки экрана «Клубы» с проверкой, что приложение активно.

        Returns:
            ClubsPage: загруженная страница.
        """
        # Восстанавливаем состояние приложения, если оно свернулось/потеряло фокус.
        self.check_and_recover_app_state()
        return super().wait_loaded()
