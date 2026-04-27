"""
Page Object: экран «Личная информация».

Открывается из таба «Профиль» → Настройки → Личная информация.
"""

from __future__ import annotations

import re
from datetime import datetime

from appium.webdriver import Remote
from appium.webdriver.common.appiumby import AppiumBy

from src.pages.mobile.base_mobile_page import BaseMobilePage

_GENDER_DB_TO_UI: dict[str, str] = {
    "male": "Мужской",
    "female": "Женский",
}


class PersonalInfoPage(BaseMobilePage):
    """Экран личной информации пользователя (имя, телефон, дата рождения, пол)."""

    page_title = "Personal Info (Личная информация)"

    DETECT_LOCATOR = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Чтобы изменить данные, обратитесь к администратору клуба"]',
    )

    FIELD_FIRST_NAME = (AppiumBy.XPATH, '//android.widget.TextView[@text="Имя"]')
    FIELD_LAST_NAME = (AppiumBy.XPATH, '//android.widget.TextView[@text="Фамилия"]')
    FIELD_PHONE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Номер телефона"]')
    FIELD_BIRTH_DATE = (AppiumBy.XPATH, '//android.widget.TextView[@text="Дата рождения"]')
    FIELD_GENDER = (AppiumBy.XPATH, '//android.widget.TextView[@text="Пол"]')

    # Значение даты рождения: следующий sibling после метки «Дата рождения»
    BIRTH_DATE_VALUE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Дата рождения"]/following-sibling::android.widget.TextView[1]',
    )
    # Значение пола: следующий sibling после метки «Пол»
    GENDER_VALUE = (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="Пол"]/following-sibling::android.widget.TextView[1]',
    )

    def __init__(self, driver: Remote):
        super().__init__(driver)

    def assert_ui(self) -> None:
        """Проверяет, что открыт экран «Личная информация»."""
        self.wait_visible(
            self.DETECT_LOCATOR,
            "Экран 'Личная информация': подсказка об изменении данных не найдена",
        )
        print("✅ Экран 'Личная информация' открыт")

    def get_displayed_birth_date(self) -> str:
        """Возвращает отображаемую дату рождения в формате DD.MM.YYYY."""
        try:
            return (self.get_text(self.BIRTH_DATE_VALUE, timeout=5) or "").strip()
        except Exception:
            # Если sibling не работает — ищем любой элемент с форматом даты
            for el in self.find_elements(
                (AppiumBy.XPATH, '//android.widget.TextView[contains(@text, ".")]')
            ):
                text = (el.text or "").strip()
                if re.match(r"\d{2}\.\d{2}\.\d{4}", text):
                    return text
            return ""

    def get_displayed_gender(self) -> str:
        """Возвращает отображаемый пол ('Мужской' / 'Женский')."""
        try:
            return (self.get_text(self.GENDER_VALUE, timeout=5) or "").strip()
        except Exception:
            for val in _GENDER_DB_TO_UI.values():
                if self.is_visible(
                    (AppiumBy.XPATH, f'//android.widget.TextView[@text="{val}"]'), timeout=3
                ):
                    return val
            return ""

    def assert_data_matches_db(self, user: dict) -> None:
        """
        Сверяет отображаемые данные личной информации с записью из коллекции users.

        Проверяет дату рождения и пол — поля, уникальные для этого экрана.
        Имя и телефон проверяются на экране «Профиль» через assert_profile_data_matches_db.

        Args:
            user: документ из коллекции users (birthDate, gender).
        """
        self._assert_birth_date_matches(user.get("birthDate"))
        self._assert_gender_matches(user.get("gender"))

    def _assert_birth_date_matches(self, db_birth_date: datetime | None) -> None:
        if db_birth_date is None:
            print("ℹ️ Дата рождения отсутствует в БД — пропуск проверки")
            return

        expected = db_birth_date.strftime("%d.%m.%Y")
        displayed = self.get_displayed_birth_date()

        assert displayed == expected, (
            f"Дата рождения на экране '{displayed}' не совпадает с БД '{expected}'"
        )
        print(f"✅ Дата рождения совпадает с БД: {displayed}")

    def _assert_gender_matches(self, db_gender: str | None) -> None:
        if db_gender is None:
            print("ℹ️ Пол отсутствует в БД — пропуск проверки")
            return

        expected_ui = _GENDER_DB_TO_UI.get(db_gender.lower(), "")
        if not expected_ui:
            print(f"ℹ️ Неизвестное значение пола в БД '{db_gender}' — пропуск проверки")
            return

        displayed = self.get_displayed_gender()
        assert displayed == expected_ui, (
            f"Пол на экране '{displayed}' не совпадает с БД '{db_gender}' → '{expected_ui}'"
        )
        print(f"✅ Пол совпадает с БД: {displayed}")
