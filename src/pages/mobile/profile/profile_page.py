"""
Page Object: таб «Профиль».
"""

import time

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.clubs.clubs_page import ClubsPage
from src.pages.mobile.notifications.notifications_page import NotificationsPage
from src.pages.mobile.profile.guest_visits_page import GuestVisitsPage
from src.pages.mobile.profile.partner_discounts_page import PartnerDiscountsPage
from src.pages.mobile.profile.personal_info_page import PersonalInfoPage
from src.pages.mobile.profile.promo_code_page import PromoCodePage
from src.pages.mobile.profile.trainings_promo_page import TrainingsPromoPage
from src.pages.mobile.shell.base_shell_page import BaseShellPage


class ProfilePage(BaseShellPage):
    """Раздел «Профиль» (личный кабинет пользователя)."""

    page_title = "Profile (Профиль)"

    # Ключевые элементы экрана «Профиль»
    SECTION_SUBSCRIPTIONS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Абонементы"]',
    )
    CTA_BUY_SUBSCRIPTION = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Купить абонемент"]',
    )
    SECTION_PARTNER_DISCOUNTS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Скидки от партнёров"]',
    )
    SECTION_PARTNER_SUBTITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Получайте больше выгоды"]',
    )
    LINK_WATCH = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Смотреть"]',
    )
    SECTION_MY_SERVICES = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Мои услуги"]',
    )
    CTA_ADD_SERVICE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Добавить услугу"]',
    )
    CTA_USE_PROMO = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Использовать промокод"]',
    )
    CTA_GUEST_VISITS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Гостевые посещения"]',
    )
    CTA_NOTIFICATIONS = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Уведомления"]',
    )
    CTA_PERSONAL_INFO = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Личная информация"]',
    )
    ACCOUNT_ACTIONS_SECTION = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Действия с аккаунтом"]',
    )
    LOGOUT_ACTION = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Выйти из аккаунта"]',
    )
    DELETE_ACCOUNT_ACTION = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Удалить аккаунт"]',
    )
    ACCOUNT_ACTIONS_BLOCK_LOCATORS = (
        ACCOUNT_ACTIONS_SECTION,
        LOGOUT_ACTION,
        DELETE_ACCOUNT_ACTION,
    )
    PROFILE_SCROLL_DOWN_START_X = 933
    PROFILE_SCROLL_DOWN_START_Y = 1687
    PROFILE_SCROLL_DOWN_END_X = 922
    PROFILE_SCROLL_DOWN_END_Y = 1004

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Профиль»."""
        self.wait_visible(
            self.SECTION_SUBSCRIPTIONS,
            "Секция 'Абонементы' не найдена на экране 'Профиль'",
        )
        print("✅ Экран 'Профиль' открыт, секция 'Абонементы' присутствует")

    def get_displayed_name(self) -> str:
        """Возвращает текст имени/фамилии из профиля (первый TextView с +7 идёт как телефон)."""
        text_views = self.driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
        for el in text_views:
            if not el.is_displayed():
                continue
            t = (el.text or "").strip()
            if not t or t.startswith("+7") or t in (
                "Профиль", "Абонементы", "Купить абонемент", "Скидки от партнёров",
                "Получайте больше выгоды", "Смотреть", "Мои услуги", "Добавить услугу",
                "Использовать промокод",
            ):
                continue
            return t
        return ""

    def get_displayed_phone(self) -> str:
        """
        Возвращает текст номера телефона из профиля.
        Ищет по @text и по content-desc (React Native часто кладёт текст в content-desc).
        """
        # 1) TextView с text, начинающимся с +7
        locator_text = (
            AppiumBy.XPATH,
            "//android.widget.TextView[starts-with(@text, '+7')]",
        )
        try:
            value = (self.get_text(locator_text, timeout=8) or "").strip()
            if value:
                return value
        except Exception:
            pass
        # 2) Любой элемент с content-desc, начинающимся с +7
        try:
            locator_desc = (
                AppiumBy.XPATH,
                "//*[starts-with(@content-desc, '+7')]",
            )
            value = (self.get_text(locator_desc, timeout=3) or "").strip()
            if value:
                return value
        except Exception:
            pass
        # 3) Перебор видимых элементов с текстом/content-desc, похожим на номер
        for xpath in [
            "//*[starts-with(@text, '+7') or starts-with(@text, '8')]",
            "//*[starts-with(@content-desc, '+7') or starts-with(@content-desc, '8')]",
        ]:
            try:
                for el in self.driver.find_elements(AppiumBy.XPATH, xpath):
                    if not el.is_displayed():
                        continue
                    raw = el.text or el.get_attribute("content-desc") or ""
                    s = (raw or "").strip()
                    if s and ("+7" in s or (s.startswith("8") and sum(c.isdigit() for c in s) >= 10)):
                        return s
            except Exception:
                continue
        return ""

    def open_buy_subscription(self) -> ClubsPage:
        """Нажимает 'Купить абонемент' и возвращает экран выбора клуба."""
        self.click(self.CTA_BUY_SUBSCRIPTION)
        return ClubsPage(self.driver).wait_loaded()

    def open_partner_discounts(self) -> PartnerDiscountsPage:
        """Нажимает 'Смотреть' в секции партнёрских скидок и возвращает экран партнёров."""
        self.click(self.LINK_WATCH)
        return PartnerDiscountsPage(self.driver).wait_loaded()

    def open_add_service(self) -> TrainingsPromoPage:
        """Нажимает 'Добавить услугу' и возвращает промо-экран персональных тренировок."""
        self.click(self.CTA_ADD_SERVICE)
        return TrainingsPromoPage(self.driver).wait_loaded()

    def open_promo_code(self) -> PromoCodePage:
        """Нажимает 'Использовать промокод' и возвращает экран ввода промокода."""
        self._scroll_profile_down_to_account_actions()
        self.click(self.CTA_USE_PROMO)
        return PromoCodePage(self.driver).wait_loaded()

    def open_guest_visits(self) -> GuestVisitsPage:
        """Нажимает 'Гостевые посещения' и возвращает экран гостевых посещений."""
        self.click(self.CTA_GUEST_VISITS)
        return GuestVisitsPage(self.driver).wait_loaded()

    def open_notifications(self) -> NotificationsPage:
        """Нажимает 'Уведомления' и возвращает экран уведомлений."""
        self._scroll_profile_down_to_account_actions()
        self.click(self.CTA_NOTIFICATIONS)
        return NotificationsPage(self.driver).wait_loaded()

    def open_personal_info(self) -> PersonalInfoPage:
        """Нажимает 'Личная информация' и возвращает экран личных данных."""
        self._scroll_profile_down_to_account_actions()
        self.click(self.CTA_PERSONAL_INFO)
        return PersonalInfoPage(self.driver).wait_loaded()

    def logout(self) -> None:
        """Выходит из текущего профиля через UI."""
        for _ in range(3):
            self._scroll_profile_down_to_account_actions()
            time.sleep(0.5)
        self.click(self.LOGOUT_ACTION)

    def _scroll_profile_down_to_account_actions(self) -> None:
        self.swipe_by_w3c_actions(
            self.PROFILE_SCROLL_DOWN_START_X,
            self.PROFILE_SCROLL_DOWN_START_Y,
            self.PROFILE_SCROLL_DOWN_END_X,
            self.PROFILE_SCROLL_DOWN_END_Y,
        )

    def assert_profile_data_matches_db(
        self, expected_first_name: str, expected_phone: str
    ) -> None:
        """
        Проверяет соответствие имени и номера телефона на экране данным из БД.
        Имя: проверяется вхождение firstName в текст на экране (частичное совпадение).
        Телефон: полное совпадение в формате UI (+7 XXX XXX XX XX).
        """
        def _xpath_contains(substring: str) -> str:
            escaped = (substring or "").replace('"', "&quot;")
            return f'//android.widget.TextView[contains(@text, "{escaped}")]'

        def _xpath_exact(text: str) -> str:
            escaped = (text or "").replace('"', "&quot;")
            return f'//android.widget.TextView[@text="{escaped}"]'

        self.wait_visible(
            (AppiumBy.XPATH, _xpath_contains(expected_first_name)),
            f"На экране не найдено имя с частью из БД (firstName): '{expected_first_name}'",
        )
        self.wait_visible(
            (AppiumBy.XPATH, _xpath_exact(expected_phone)),
            f"Телефон на экране не совпадает с БД: ожидалось '{expected_phone}'",
        )
        print("✅ Имя и телефон на экране соответствуют данным из БД")
