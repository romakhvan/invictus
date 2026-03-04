"""
Хелперы для прохождения онбординга нового клиента до главного экрана.
"""

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.pages.mobile.auth import PreviewPage, PhoneAuthPage, SmsCodePage
from src.pages.mobile.onboarding import (
    NamePage,
    BirthDatePage,
    GenderPage,
    HeightPage,
    WeightPage,
    FitnessGoalPage,
    WorkoutExperiencePage,
    WorkoutFrequencyPage,
    OnboardingCompletePage,
)
from src.pages.mobile.home import HomePage, HomeState


def run_auth_to_main(driver: "Remote", phone: str) -> None:
    """
    Вход в приложение без онбординга: превью → ввод телефона → SMS-код → главная.

    По завершении драйвер на главном экране (ожидается состояние NEW_USER для potential).
    Используется для тестов навигации под существующим пользователем (role: potential).

    Args:
        driver: Appium WebDriver
        phone: Номер телефона (10 цифр), существующий в БД (например potential)
    """
    preview = PreviewPage(driver).wait_loaded()
    preview.skip_preview()

    phone_page = PhoneAuthPage(driver).wait_loaded()
    phone_page.enter_phone(phone)
    phone_page.click_continue()
    phone_page.handle_code_delivery_modal(method="SMS")

    sms = SmsCodePage(driver).wait_loaded()
    sms.enter_code()
    sms.click_confirm()

    home = HomePage(driver).wait_loaded()
    if home.get_current_home_state() != HomeState.NEW_USER:
        raise AssertionError(
            "После входа ожидалось состояние главного экрана NEW_USER (potential)"
        )


def run_full_onboarding_to_main(driver: "Remote", test_phone: str) -> None:
    """
    Выполняет полный флоу онбординга: превью → авторизация → все шаги онбординга → главная.

    По завершении драйвер находится на главном экране в состоянии NEW_USER.
    Не выполняет проверки (assert) — только шаги до главной.

    Args:
        driver: Appium WebDriver
        test_phone: Номер телефона для авторизации (10 цифр)
    """
    preview = PreviewPage(driver).wait_loaded()
    preview.skip_preview()

    phone = PhoneAuthPage(driver).wait_loaded()
    phone.enter_phone(test_phone)
    phone.click_continue()
    phone.handle_code_delivery_modal(method="SMS")

    sms = SmsCodePage(driver).wait_loaded()
    sms.enter_code()
    sms.click_confirm()

    name_page = NamePage(driver).wait_loaded()
    name_page.enter_full_name("Appium", "Test")
    name_page.click_next()

    birth_date_page = BirthDatePage(driver).wait_loaded()
    for _ in range(3):
        birth_date_page.swipe_date_picker()
        time.sleep(0.5)
    birth_date_page.click_next()

    gender_page = GenderPage(driver).wait_loaded()
    gender_page.select_female()
    gender_page.click_next()

    height_page = HeightPage(driver).wait_loaded()
    height_page.select_height_cm(165)
    time.sleep(0.3)
    height_page.click_next()

    weight_page = WeightPage(driver).wait_loaded()
    weight_page.select_weight_kg(55)
    time.sleep(0.3)
    weight_page.click_next()

    fitness_goal_page = FitnessGoalPage(driver).wait_loaded()
    fitness_goal_page.select_weight_loss()
    time.sleep(0.3)
    fitness_goal_page.click_next()

    workout_exp_page = WorkoutExperiencePage(driver).wait_loaded()
    workout_exp_page.select_no()
    time.sleep(0.3)
    workout_exp_page.click_next()

    frequency_page = WorkoutFrequencyPage(driver).wait_loaded()
    frequency_page.select_once_per_week()
    time.sleep(0.3)
    frequency_page.click_next()

    complete_page = OnboardingCompletePage(driver).wait_loaded()
    complete_page.click_go_to_main()

    home = HomePage(driver).wait_loaded()
    if home.get_current_home_state() != HomeState.NEW_USER:
        raise AssertionError(
            "Ожидалось состояние главного экрана NEW_USER после онбординга"
        )
