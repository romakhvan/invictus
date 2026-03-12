"""
Page Object: таб «Профиль».
"""

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

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

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Профиль»."""
        self.wait_visible(
            self.SECTION_SUBSCRIPTIONS,
            "Секция 'Абонементы' не найдена на экране 'Профиль'",
        )
        self.wait_visible(
            self.CTA_BUY_SUBSCRIPTION,
            "Кнопка 'Купить абонемент' не найдена",
        )
        self.wait_visible(
            self.SECTION_MY_SERVICES,
            "Секция 'Мои услуги' не найдена",
        )
        print("✅ Экран 'Профиль' открыт, все элементы присутствуют")

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
