"""
Smoke-тест: Заполнение данных нового клиента.

Проверяет:
- Загрузку страницы ввода имени
- Наличие всех UI элементов
- Ввод имени и фамилии
- Активацию кнопки 'Далее'
- Выбор даты рождения
- Выбор пола (Женщина/Мужчина)
- Выбор роста (см)
- Выбор веса (кг)
- Выбор цели тренировок
- Выбор опыта занятий фитнесом
- Выбор частоты тренировок в неделю
- Экран «Профиль готов» и проверка отображаемого имени
"""

import pytest
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.auth import PreviewPage, PhoneAuthPage, SmsCodePage
from src.pages.mobile.onboarding import NamePage, BirthDatePage, GenderPage, HeightPage, WeightPage, FitnessGoalPage, WorkoutExperiencePage, WorkoutFrequencyPage, OnboardingCompletePage


@pytest.mark.mobile
@pytest.mark.smoke
def test_client_name_input(mobile_driver: "Remote"):
    """
    Smoke-тест: Страница ввода имени и фамилии клиента + выбор даты рождения.
    
    Сценарий:
    1. Запуск приложения и пропуск превью
    2. Прохождение авторизации (телефон + SMS-код)
    3. Проверка элементов страницы имени
    4. Заполнение имени и фамилии
    5. Проверка активности кнопки 'Далее'
    6. Переход к странице даты рождения
    7. Проверка элементов страницы даты рождения
    8. Выбор даты через свайп
    9. Переход к странице выбора пола
    10. Выбор пола и нажатие 'Далее'
    11. Страница выбора роста — выбор значения и 'Далее'
    12. Страница выбора веса — выбор значения и 'Далее'
    """
    driver = mobile_driver
    
    print("\n" + "=" * 80)
    print("SMOKE-ТЕСТ: Заполнение данных нового клиента — Страница имени")
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
    phone.enter_phone("7001234568")
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