"""
Page Object: универсальная страница подтверждения/оплаты.
"""

import re

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage


class PaymentConfirmationPage(BaseMobilePage):
    """Универсальная страница подтверждения перед оплатой."""

    page_title = "Payment Confirmation (Подтверждение)"

    HEADER = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Подтверждение"]',
    )
    PAYMENT_METHOD_LABEL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Способ оплаты"]',
    )
    TOTAL_LABEL = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Итого"]',
    )
    TERMS_TEXT = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "Соглашаюсь с условиями публичной оферты")]',
    )
    PAY_BUTTON = (
        AppiumBy.XPATH,
        '//android.widget.TextView[contains(@text, "Оплатить")]',
    )
    TERMS_CHECKBOX_BOUNDS = (36, 1959, 108, 2031)

    def __init__(self, driver: Remote):
        super().__init__(driver)

    @staticmethod
    def product_title_locator(product_text: str):
        return (
            AppiumBy.XPATH,
            f'//android.widget.TextView[contains(@text, "{product_text}")]',
        )

    @staticmethod
    def club_name_locator(club_name: str):
        return (
            AppiumBy.XPATH,
            f'//android.widget.TextView[@text="{club_name}"]',
        )

    @staticmethod
    def payment_method_locator(method_name: str):
        return (
            AppiumBy.XPATH,
            f'//android.widget.TextView[@text="{method_name}"]',
        )

    @staticmethod
    def total_amount_locator(amount_text: str):
        return (
            AppiumBy.XPATH,
            f'//android.widget.TextView[@text="{amount_text}"]',
        )

    @staticmethod
    def _normalize_amount_text(amount_text: str) -> str:
        normalized = " ".join((amount_text or "").replace("\xa0", " ").split())
        match = re.search(r"(\d[\d ]*\d\s*₸)", normalized)
        if not match:
            return normalized
        return " ".join(match.group(1).split())

    def assert_ui(self) -> None:
        """Проверяет, что открыта универсальная страница подтверждения оплаты."""
        self.wait_visible(self.HEADER, "Не найден заголовок 'Подтверждение'")
        self.wait_visible(
            self.PAYMENT_METHOD_LABEL,
            "Не найден блок 'Способ оплаты'",
        )
        self.wait_visible(self.TOTAL_LABEL, "Не найден блок 'Итого'")
        self.wait_visible(self.PAY_BUTTON, "Не найдена кнопка 'Оплатить'")
        print("✅ Открыта универсальная страница подтверждения оплаты")

    def assert_payment_summary_visible(self) -> None:
        """Проверяет наличие общих элементов сводки оплаты."""
        self.wait_visible(self.TERMS_TEXT, "Не найден текст согласия с офертой")

    def assert_product_title_visible(self, product_text: str) -> None:
        """Проверяет название продукта на странице оплаты."""
        self.wait_visible(
            self.product_title_locator(product_text),
            f"Не найден продукт '{product_text}' на странице оплаты",
        )

    def assert_selected_club_visible(self, club_name: str) -> None:
        """Проверяет выбранный клуб на странице оплаты."""
        self.wait_visible(
            self.club_name_locator(club_name),
            f"Не найден выбранный клуб '{club_name}' на странице оплаты",
        )

    def assert_payment_method_visible(self, method_name: str) -> None:
        """Проверяет способ оплаты на странице оплаты."""
        self.wait_visible(
            self.payment_method_locator(method_name),
            f"Не найден способ оплаты '{method_name}' на странице оплаты",
        )

    def select_payment_method(self, method_name: str) -> None:
        """Выбирает способ оплаты по названию из списка доступных методов."""
        current_method = self.assert_any_payment_method_visible()
        self.click(self.payment_method_locator(current_method))
        self.click(self.payment_method_locator(method_name))
        self.assert_payment_method_visible(method_name)
        print(f"✅ Выбран способ оплаты: {method_name}")

    def assert_any_payment_method_visible(self) -> str:
        """
        Проверяет, что на странице отображается какой-либо способ оплаты.

        Returns:
            str: текст найденного способа оплаты.
        """
        payment_label = self.wait_visible(
            self.PAYMENT_METHOD_LABEL,
            "Не найден блок 'Способ оплаты'",
        )
        total_label = self.wait_visible(
            self.TOTAL_LABEL,
            "Не найден блок 'Итого'",
        )

        payment_label_location = payment_label.location or {}
        payment_label_size = payment_label.size or {}
        total_label_location = total_label.location or {}

        payment_label_y = int(payment_label_location.get("y", 0))
        payment_label_height = int(payment_label_size.get("height", 0))
        total_label_y = int(total_label_location.get("y", 0))

        text_elements = self.find_elements((AppiumBy.CLASS_NAME, "android.widget.TextView"))
        candidates: list[tuple[int, str]] = []

        for element in text_elements:
            try:
                if not element.is_displayed():
                    continue
                text = (element.text or "").strip()
                if not text or text in {"Способ оплаты", "Итого"}:
                    continue
                location = element.location or {}
                y = int(location.get("y", 0))
                if y <= payment_label_y:
                    continue
                if y >= total_label_y:
                    continue
                if y - payment_label_y > max(280, payment_label_height + 220):
                    continue
                if len(text) <= 1:
                    continue
                candidates.append((y, text))
            except Exception:
                continue

        if not candidates:
            raise AssertionError("На странице оплаты не найден текст способа оплаты")

        candidates.sort(key=lambda item: item[0])
        method_name = candidates[0][1]
        print(f"✅ Отображается способ оплаты: {method_name}")
        return method_name

    def assert_total_amount_visible(self, amount_text: str) -> None:
        """Проверяет итоговую сумму на странице оплаты."""
        expected_amount = self._normalize_amount_text(amount_text)
        text_elements = self.find_elements((AppiumBy.CLASS_NAME, "android.widget.TextView"))

        for element in text_elements:
            try:
                if not element.is_displayed():
                    continue
                text = (element.text or "").strip()
                if not text:
                    continue
                current_amount = self._normalize_amount_text(text)
                if current_amount == expected_amount:
                    print(f"✅ Отображается итоговая сумма: {current_amount}")
                    return
            except Exception:
                continue

        raise AssertionError(
            f"Не найдена итоговая сумма '{expected_amount}' на странице оплаты"
        )

    def accept_terms(self) -> None:
        """
        Ставит галочку согласия с офертой.

        На текущем экране оплаты чекбокс не имеет стабильного locator,
        поэтому используем tap по центру известного bounds чекбокса.
        """
        self.wait_visible(
            self.TERMS_TEXT,
            "Не найден текст согласия с офертой для установки галочки",
        )
        left, top, right, bottom = self.TERMS_CHECKBOX_BOUNDS
        tap_x = (left + right) // 2
        tap_y = (top + bottom) // 2

        self.tap_by_coordinates(
            tap_x,
            tap_y,
            duration_ms=100,
            action_name="Установлена галочка согласия с офертой",
        )

    def click_pay(self) -> None:
        """Нажать кнопку оплаты."""
        self.click(self.PAY_BUTTON)
        print("✅ Нажата кнопка 'Оплатить'")
