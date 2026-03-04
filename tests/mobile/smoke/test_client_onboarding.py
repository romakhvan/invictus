"""
Smoke-тест: полный флоу онбординга нового клиента (auth → onboarding → главная).

Проверяет:
- Запуск приложения и превью
- Авторизацию (телефон + SMS-код)
- Загрузку и элементы страницы ввода имени
- Ввод имени и фамилии, активацию кнопки «Далее»
- Выбор даты рождения, пола, роста, веса
- Выбор цели тренировок, опыта и частоты занятий
- Экран «Профиль готов» и проверку отображаемого имени
- Главный экран нового пользователя (состояние «Нет абонемента»)
"""

import pytest
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.auth import PreviewPage, PhoneAuthPage, SmsCodePage
from src.pages.mobile.onboarding import NamePage, BirthDatePage, GenderPage, HeightPage, WeightPage, FitnessGoalPage, WorkoutExperiencePage, WorkoutFrequencyPage, OnboardingCompletePage
from src.pages.mobile.home import HomePage, HomeState
from src.repositories.users_repository import get_available_test_phone

# Базовый номер для поиска свободного (префикс 700 для тестов)
ONBOARDING_TEST_PHONE_BASE = "7001234564"


@pytest.mark.mobile
@pytest.mark.smoke
def test_new_client_onboarding_full_flow(mobile_driver: "Remote", db):
    """
    Smoke-тест: полный онбординг нового клиента от входа до главного экрана.

    Сценарий:
    1. Запуск приложения и пропуск превью
    2. Авторизация (телефон + SMS-код)
    3. Страница имени — заполнение, проверка кнопки «Далее»
    4. Дата рождения, пол, рост, вес
    5. Цель тренировок, опыт занятий, частота тренировок
    6. Экран «Профиль готов» — проверка имени, переход на главную
    7. Главный экран нового пользователя (состояние «Нет абонемента»)
    """
    driver = mobile_driver

    test_phone = get_available_test_phone(db, base_phone=ONBOARDING_TEST_PHONE_BASE)
    if not test_phone:
        pytest.skip(
            f"Не найден свободный номер в диапазоне от {ONBOARDING_TEST_PHONE_BASE} "
            "(все заняты в БД). Тест онбординга требует новый номер."
        )
    print(f"📱 Используется свободный номер: {test_phone}")

    print("\n" + "=" * 80)
    print("SMOKE-ТЕСТ: Полный онбординг нового клиента (auth → onboarding → главная)")
    print("=" * 80 + "\n")
    
    # Шаг 1: Проверка запуска
    assert driver.current_package == MOBILE_APP_PACKAGE, \
        f"Неверный package: ожидался {MOBILE_APP_PACKAGE}, получен {driver.current_package}"
    print(f"✅ Приложение запущено: {driver.current_package}")
    
    # Шаг 2: Пропуск превью
    preview = PreviewPage(driver).wait_loaded()
    preview.skip_preview()
    
    # Шаг 3: Авторизация - ввод телефона
    phone = PhoneAuthPage(driver).wait_loaded()
    phone.enter_phone(test_phone)
    phone.click_continue()
    
    # Обработка модалки выбора способа получения кода (если появится)
    phone.handle_code_delivery_modal(method="SMS")
    
    print("✅ Номер телефона введен, переход к SMS-коду")
    
    # Шаг 4: Авторизация - ввод SMS-кода
    sms = SmsCodePage(driver).wait_loaded()
    sms.enter_code()
    sms.click_confirm()
    print("✅ SMS-код введен, переход к заполнению данных")
    
    # Шаг 5: Проверка страницы ввода имени
    name_page = NamePage(driver).wait_loaded()
    
    # Шаг 6: Заполнение имени и фамилии
    test_name = "Appium"
    test_surname = "Test"
    name_page.enter_full_name(test_name, test_surname)
    
    # Шаг 7: Проверка кнопки 'Далее'
    assert name_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна"
    print("✅ Кнопка 'Далее' активна")
    
    # Шаг 8: Переход к странице выбора даты рождения
    name_page.click_next()
    
    
    # Шаг 9: Проверка страницы выбора даты рождения
    birth_date_page = BirthDatePage(driver).wait_loaded()
    
    # Шаг 10: Выбор даты рождения через свайп
    birth_date_page.swipe_date_picker()
    # NB: В шагах с выбором даты рождения часто требуется короткая пауза для анимации скроллера/обновления кнопки.
    time.sleep(0.5)
    birth_date_page.swipe_date_picker()
    time.sleep(0.5)
    birth_date_page.swipe_date_picker()
    print("✅ Дата рождения выбрана")
    
    # Шаг 11: Проверка и нажатие кнопки 'Далее'
    assert birth_date_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна"
    print("✅ Кнопка 'Далее' активна на странице даты рождения")
    
    birth_date_page.click_next()
    print("✅ Нажата кнопка 'Далее'")

    # Шаг 12: Проверка страницы выбора пола
    gender_page = GenderPage(driver).wait_loaded()
    gender_page.select_female()
    assert gender_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна после выбора пола"
    print("✅ Кнопка 'Далее' активна на странице выбора пола")
    gender_page.click_next()
    print("✅ Онбординг: имя → дата рождения → пол пройден")

    # Шаг 13: Страница выбора роста
    height_page = HeightPage(driver).wait_loaded()
    height_page.select_height_cm(165)
    time.sleep(0.3)
    assert height_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна после выбора роста"
    print("✅ Кнопка 'Далее' активна на странице роста")
    height_page.click_next()
    print("✅ Онбординг: имя → дата → пол → рост пройден")

    # Шаг 14: Страница выбора веса
    weight_page = WeightPage(driver).wait_loaded()
    weight_page.select_weight_kg(55)
    time.sleep(0.3)
    assert weight_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна после выбора веса"
    print("✅ Кнопка 'Далее' активна на странице веса")
    weight_page.click_next()
    print("✅ Онбординг: имя → дата → пол → рост → вес пройден")

    # Шаг 15: Страница выбора цели тренировок
    fitness_goal_page = FitnessGoalPage(driver).wait_loaded()
    fitness_goal_page.select_weight_loss()
    time.sleep(0.3)
    assert fitness_goal_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна после выбора цели"
    print("✅ Кнопка 'Далее' активна на странице цели тренировок")
    fitness_goal_page.click_next()
    print("✅ Онбординг: имя → дата → пол → рост → вес → цель тренировок пройден")

    # Шаг 16: Страница выбора опыта занятий
    workout_exp_page = WorkoutExperiencePage(driver).wait_loaded()
    workout_exp_page.select_no()
    time.sleep(0.3)
    assert workout_exp_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна после выбора опыта"
    print("✅ Кнопка 'Далее' активна на странице опыта занятий")
    workout_exp_page.click_next()
    print("✅ Онбординг: ... → цель тренировок → опыт занятий пройден")

    # Шаг 17: Страница выбора частоты тренировок
    frequency_page = WorkoutFrequencyPage(driver).wait_loaded()
    frequency_page.select_once_per_week()
    time.sleep(0.3)
    assert frequency_page.is_next_button_enabled(), "Кнопка 'Далее' должна быть активна после выбора частоты"
    print("✅ Кнопка 'Далее' активна на странице частоты тренировок")
    frequency_page.click_next()
    print("✅ Онбординг: ... → опыт занятий → частота тренировок пройден")

    # Шаг 18: Экран завершения онбординга — проверка имени и переход на главную
    complete_page = OnboardingCompletePage(driver).wait_loaded()
    assert complete_page.verify_displayed_name(test_name), (
        f"На экране 'Профиль готов' должно отображаться имя '{test_name}', "
        f"получено: '{complete_page.get_displayed_name()}'"
    )
    print(f"✅ На экране завершения отображается имя: {test_name}")
    complete_page.click_go_to_main()
    print("✅ Онбординг завершён, переход на главную")

    # Шаг 19: Главный экран нового пользователя
    home = HomePage(driver).wait_loaded()
    assert home.get_current_home_state() == HomeState.NEW_USER, (
        "После онбординга должен отображаться главный экран нового пользователя (Нет абонемента)"
    )
    home_content = home.get_content()
    home_content.assert_ui()
    print("✅ Главный экран нового пользователя отображается корректно")