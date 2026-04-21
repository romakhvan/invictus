"""
Page Object: экран «Клубы» (список клубов).

Открывается с главной по кнопке «Клубы» и с других экранов приложения.
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.common.club_filter_component import ClubFilterComponent
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
    PURCHASE_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Покупка тренировок"]',
    )
    CHOOSE_CITY_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Выберите город"]',
    )
    ANY_INVICTUS_CLUB_CARD = (
        AppiumBy.XPATH,
        '//android.widget.TextView[starts-with(@text, "Invictus")]',
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
        '//android.widget.TextView[starts-with(@text, "Invictus GO ")]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)
        self._club_filter = ClubFilterComponent(driver)

    @property
    def club_filter(self) -> ClubFilterComponent:
        return self._club_filter

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Клубы»."""
        if self.is_visible(self.FILTER_ALL_CITIES, timeout=3):
            self.wait_visible(
                self.FILTER_ALL_CITIES,
                "Экран 'Клубы': фильтр 'Все города' не найден",
            )

            any_club_visible = (
                self.is_visible(self.CLUB_INVICTUS_GO, timeout=5)
                or self.is_visible(self.CLUB_INVICTUS_FITNESS, timeout=5)
                or self.is_visible(self.CLUB_INVICTUS_GIRLS, timeout=5)
                or self.is_visible(self.ANY_INVICTUS_CLUB_CARD, timeout=5)
            )
            if not any_club_visible:
                raise AssertionError(
                    "Экран 'Клубы' открыт, но ни один из ожидаемых клубов "
                    "('Invictus GO', 'Invictus Fitness', 'Invictus Girls') не найден."
                )

            print("✅ Экран 'Клубы' открыт: фильтр и клубы видимы")
            return

        self.wait_visible(
            self.PURCHASE_TITLE,
            "Экран выбора клуба для покупки не найден (не найден заголовок 'Покупка тренировок')",
        )
        self.wait_visible(
            self.CHOOSE_CITY_TITLE,
            "Экран выбора клуба для покупки не найден (не найден заголовок 'Выберите город')",
        )
        self.wait_visible(
            self.ANY_INVICTUS_CLUB_CARD,
            "На экране выбора клуба для покупки не найден ни один клуб Invictus",
        )
        print("✅ Открыт экран выбора клуба для покупки тренировок")

    def assert_purchase_trainings_variant_open(self) -> None:
        """Проверяет вариант экрана клубов для покупки тренировок."""
        self.wait_visible(
            self.PURCHASE_TITLE,
            "Не найден заголовок 'Покупка тренировок'",
        )
        self.wait_visible(
            self.CHOOSE_CITY_TITLE,
            "Не найден заголовок 'Выберите город'",
        )
        self.wait_visible(
            self.ANY_INVICTUS_CLUB_CARD,
            "Не найден ни один клуб Invictus на экране покупки тренировок",
        )

    def assert_invictus_go_club_present(self) -> None:
        """
        Проверяет, что на экране есть хотя бы одна карточка клуба 'Invictus GO *'.
        Суффикс после 'Invictus GO ' может меняться (Baitursynov и др.).
        """
        self.wait_visible(
            self.CLUB_CARD_INVICTUS_GO,
            "Ожидалась карточка клуба 'Invictus GO *', но она не найдена",
        )

    def click_first_invictus_go_card(self) -> str:
        """
        Нажимает первую сверху видимую карточку клуба Invictus GO.

        Returns:
            str: заголовок выбранной карточки.
        """
        self.assert_invictus_go_club_present()

        elements = []
        for element in self.find_elements(self.CLUB_CARD_INVICTUS_GO):
            try:
                if not element.is_displayed():
                    continue
                text = (element.text or "").strip()
                location = element.location or {}
                elements.append((int(location.get("y", 0)), text, element))
            except Exception:
                continue

        if not elements:
            raise AssertionError("Не найдена ни одна видимая карточка клуба Invictus GO для выбора")

        elements.sort(key=lambda item: item[0])
        _, club_name, club_element = elements[0]
        club_element.click()
        print(f"✅ Выбрана первая карточка клуба сверху: {club_name}")
        return club_name

    def wait_loaded(self) -> "ClubsPage":
        """
        Ждёт загрузки экрана «Клубы» с проверкой, что приложение активно.

        Returns:
            ClubsPage: загруженная страница.
        """
        # Восстанавливаем состояние приложения, если оно свернулось/потеряло фокус.
        self.check_and_recover_app_state()
        return super().wait_loaded()
