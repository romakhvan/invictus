"""
Контент главного экрана для нового пользователя (нет абонемента, офферы, CTA).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import TimeoutException
from src.pages.mobile.base_content_block import BaseContentBlock

if TYPE_CHECKING:
    from src.pages.mobile.notifications.notifications_page import NotificationsPage


class HomeNewUserContent(BaseContentBlock):
    """Контент главного экрана: новый пользователь без абонемента (секция, не страница)."""

    page_title = "Home (New User)"  # для контекста в сообщениях об ошибках

    # Маркер состояния: уникален для главной нового юзера.
    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "10 ДНЕЙ") and contains(@text, "КОМБО-ТРЕНИРОВКИ") and contains(@text, "2 990")]',
    )

    # Ключевые элементы экрана (включая промо Rabbit Hole)
    NO_SUBSCRIPTION_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[@text="Нет абонемента"]')
    WANT_BONUSES_BTN = (AppiumBy.XPATH, '//android.widget.TextView[@text="Хочу бонусы!"]')
    # Кликабельный контейнер оффера «10 ДНЕЙ...» с content-desc "Расскажите подробнее!"
    TELL_MORE_ENTRYPOINT = (AppiumBy.ACCESSIBILITY_ID, "Расскажите подробнее!")
    OFFER_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="ВОТ ЧТО ВАС ЖДЁТ"]',
    )
    OFFER_PRICE_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "2 990")]')
    DETECT_LOCATORS = (DETECT_LOCATOR, TELL_MORE_ENTRYPOINT)
    # Кнопка в оверлее Rabbit Hole (по частичному тексту «Купить», без привязки к цене)
    RABBIT_HOLE_BUY_BTN = (AppiumBy.XPATH, '//*[contains(@content-desc, "Купить за")]')
    PROGRESS_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[@text="Весь ваш прогресс — в приложении"]')
    PROMO_LABEL = (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, "Акция для новых клиентов")]')
    CLUBS_BTN = (AppiumBy.XPATH, '//android.widget.TextView[@text="Клубы"]')
    # Баннер/entrypoint «Health, Комплексная забота о себе, ИИ, БАДы, Врачи, Анализы»
    HEALTH_ENTRYPOINT = (
        AppiumBy.ACCESSIBILITY_ID,
        "Health, Комплексная забота о себе, ИИ, БАДы, Врачи, Анализы",
    )
    # Entrypoint «Онлайн тренер Gym Buddy» (карточка: заголовок «Gym Buddy» + подпись «Онлайн тренер»)
    GYM_BUDDY_ENTRYPOINT = (AppiumBy.XPATH, '//android.widget.TextView[@text="Gym Buddy"]')
    # Entrypoint «Store» (кликабельный контейнер с content-desc 'Store')
    STORE_ENTRYPOINT = (AppiumBy.ACCESSIBILITY_ID, "Store")
    # Любая карточка клуба внизу главной (по тексту, начинающемуся с 'Invictus ').
    FIRST_CLUB_CARD_TITLE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[starts-with(@text, "Invictus ")]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что отображается контент для нового пользователя."""
        self.wait_visible(
            self.TELL_MORE_ENTRYPOINT,
            "Контент 'новый пользователь' не найден (нет кнопки 'Расскажите подробнее!')",
        )

    def click_tell_more(self) -> None:
        """Нажать «Расскажите подробнее!» (переход к деталям оффера/онбордингу)."""
        # Жмём по кликабельному контейнеру (ViewGroup) с content-desc, чтобы повторить реальное поведение.
        self.click(self.TELL_MORE_ENTRYPOINT)

    @staticmethod
    def _extract_price_text(raw_text: str) -> str:
        """Извлекает цену вида '2 990 ₸' из текста оффера или кнопки."""
        normalized = " ".join((raw_text or "").split())
        match = re.search(r"(\d[\d ]*\d\s*₸)", normalized)
        if not match:
            raise AssertionError(f"Не удалось извлечь цену из текста: '{raw_text}'")
        return " ".join(match.group(1).split())

    def get_offer_price_text(self) -> str:
        """Возвращает цену из Rabbit Hole оффера."""
        try:
            offer_text = self.get_text(self.OFFER_PRICE_LABEL, timeout=2)
            return self._extract_price_text(offer_text)
        except TimeoutException:
            return self.get_buy_button_price_text()

    def get_buy_button_price_text(self) -> str:
        """Возвращает цену из кнопки покупки Rabbit Hole."""
        button = self.find_element(self.RABBIT_HOLE_BUY_BTN)
        raw_text = ""
        try:
            raw_text = (button.get_attribute("content-desc") or "").strip()
        except Exception:
            raw_text = ""
        if not raw_text:
            raw_text = (getattr(button, "text", "") or "").strip()
        return self._extract_price_text(raw_text)

    def assert_rabbit_hole_price_consistency(self) -> str:
        """
        Проверяет, что цена в заголовке оффера и в кнопке покупки совпадает.

        Returns:
            str: согласованная цена для дальнейших шагов сценария.
        """
        offer_price = self.get_offer_price_text()
        button_price = self.get_buy_button_price_text()
        if offer_price != button_price:
            raise AssertionError(
                "Цена в Rabbit Hole оффере не совпадает с ценой на кнопке покупки: "
                f"оффер='{offer_price}', кнопка='{button_price}'"
            )
        print(f"✅ Цена Rabbit Hole согласована: {offer_price}")
        return offer_price

    def open_clubs(self):
        """Открыть экран «Клубы» с главной. Возвращает ClubsPage."""
        from src.pages.mobile.clubs.clubs_page import ClubsPage

        self.click(self.CLUBS_BTN)
        return ClubsPage(self.driver).wait_loaded()

    def open_health(self):
        """Открыть экран/лендинг Health с главной. Возвращает HealthPage."""
        from src.pages.mobile.products.health_page import HealthPage

        self.click(self.HEALTH_ENTRYPOINT)
        return HealthPage(self.driver).wait_loaded()

    def open_gym_buddy(self):
        """Открыть экран «Онлайн тренер Gym Buddy» с главной. Возвращает GymBuddyPage."""
        from src.pages.mobile.products.gym_buddy_page import GymBuddyPage

        self.click(self.GYM_BUDDY_ENTRYPOINT)
        return GymBuddyPage(self.driver).wait_loaded()

    def open_store(self):
        """Открыть экран магазина Store с главной. Возвращает StorePage."""
        from src.pages.mobile.products.store_page import StorePage

        self.click(self.STORE_ENTRYPOINT)
        return StorePage(self.driver).wait_loaded()

    def open_first_club_card(self):
        """
        Открыть экран конкретного клуба по первой карточке клуба внизу главной.
        Выполняет лёгкий скролл вниз, чтобы вывести карточки в видимую область.
        Возвращает ClubDetailsPage.
        """
        from src.pages.mobile.clubs.club_details_page import ClubDetailsPage

        window_size = self.driver.get_window_size()
        width = window_size["width"]
        height = window_size["height"]

        start_x = width // 2
        start_y = int(height * 0.8)
        end_y = int(height * 0.3)

        # Пара свайпов, чтобы гарантированно показать карточки
        for _ in range(2):
            if self.is_visible(self.FIRST_CLUB_CARD_TITLE, timeout=3):
                break
            self.swipe(start_x, start_y, start_x, end_y, 600)

        self.click(self.FIRST_CLUB_CARD_TITLE)
        return ClubDetailsPage(self.driver).wait_loaded()

    def open_bonuses(self):
        """Открыть экран «Бонусы» с главной. Возвращает BonusesPage."""
        from src.pages.mobile.bonuses.bonuses_page import BonusesPage

        self.click(self.WANT_BONUSES_BTN)
        return BonusesPage(self.driver).wait_loaded()

    def open_notifications(self) -> NotificationsPage:
        """Открыть экран «Уведомления» через иконку в правом верхнем углу. Возвращает NotificationsPage."""
        from src.pages.mobile.notifications.notifications_page import NotificationsPage

        notification_locators = [
            (AppiumBy.ACCESSIBILITY_ID, "Уведомления"),
            (AppiumBy.XPATH, '//*[contains(@content-desc, "Уведом")]'),
        ]
        for locator in notification_locators:
            if self.is_visible(locator, timeout=2):
                self.click(locator, timeout=3)
                return NotificationsPage(self.driver).wait_loaded()

        window_size = self.driver.get_window_size()
        self.tap_by_coordinates(
            int(window_size["width"] * 0.94),
            int(window_size["height"] * 0.08),
            duration_ms=100,
            action_name="Открыт экран уведомлений (fallback tap)",
        )
        return NotificationsPage(self.driver).wait_loaded()
