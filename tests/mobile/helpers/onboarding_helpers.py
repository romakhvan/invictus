"""
Хелперы для прохождения онбординга нового клиента до главного экрана.
"""

import time
from typing import TYPE_CHECKING

from selenium.common.exceptions import TimeoutException

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
from src.pages.mobile.home import (
    HomePage,
    HomeState,
    HomeNewUserContent,
    HomeSubscribedContent,
    HomeMemberContent,
)


_HOME_STATE_DETECTORS = [
    (HomeState.NEW_USER, HomeNewUserContent.DETECT_LOCATOR),
    (HomeState.SUBSCRIBED, HomeSubscribedContent.DETECT_LOCATOR),
    (HomeState.MEMBER, HomeMemberContent.DETECT_LOCATOR),
]


def _validate_home_state(home: HomePage, expected_state: HomeState | None) -> HomePage:
    """Проверяет ожидаемое состояние главной и возвращает ту же страницу."""
    if expected_state is None:
        return home

    current_state = home.get_current_home_state()
    if current_state != expected_state:
        raise AssertionError(
            f"После входа ожидалось состояние {expected_state.value}, но получено {current_state.value}"
        )
    return home


def _get_current_home_if_ready(
    driver: "Remote",
    expected_state: HomeState | None = None,
) -> HomePage | None:
    """
    Возвращает HomePage, если приложение уже открылось на главной.

    Это особенно важно для запусков с ``--mobile-no-reset``, когда после рестарта
    новая Appium-сессия может сразу восстановить авторизованную главную вместо Preview.
    """
    home = HomePage(driver)
    current_state = HomeState.UNKNOWN

    detectors = _HOME_STATE_DETECTORS
    if expected_state is not None:
        detectors = sorted(
            _HOME_STATE_DETECTORS,
            key=lambda item: item[0] != expected_state,
        )

    for state, locator in detectors:
        if home.is_visible(locator, timeout=1):
            current_state = state
            break

    if current_state == HomeState.UNKNOWN:
        return None

    if expected_state is not None and current_state != expected_state:
        print(
            "\nℹ️ После запуска уже открыта главная, "
            f"но в состоянии {current_state.value} вместо ожидаемого {expected_state.value}. "
            "Продолжаем сценарий авторизации."
        )
        return None

    print(
        "\nℹ️ После запуска уже открыта главная "
        f"({current_state.value}); повторная авторизация не требуется."
    )
    return home


def run_auth_to_home(driver: "Remote", phone: str, expected_state: HomeState | None = None) -> HomePage:
    """
    Вход в приложение без онбординга: превью → ввод телефона → SMS-код → главная.

    Если после рестарта приложение уже восстановилось на главной или на одном из
    промежуточных auth-экранов, helper продолжит сценарий с найденного шага.

    Args:
        driver: Appium WebDriver
        phone: Номер телефона (10 цифр)
        expected_state: Ожидаемое состояние главной. Если None, состояние не проверяется.

    Returns:
        HomePage: Загруженная главная страница.
    """
    last_error: Exception | None = None

    for attempt in range(2):
        try:
            if attempt > 0:
                print("\n🔁 Повторная попытка авторизации до главного экрана (run_auth_to_home)")

            preview = PreviewPage(driver)
            preview.check_and_recover_app_state()

            home = _get_current_home_if_ready(driver, expected_state=expected_state)
            if home is not None:
                return home

            if preview.is_visible(preview.START_BUTTON, timeout=3):
                preview.wait_loaded()
                preview.skip_preview()
                phone_page = PhoneAuthPage(driver).wait_loaded()
            elif PhoneAuthPage(driver).is_visible(PhoneAuthPage.HEADER, timeout=3):
                print("\nℹ️ Продолжаем авторизацию с экрана ввода телефона")
                phone_page = PhoneAuthPage(driver).wait_loaded()
            elif SmsCodePage(driver).is_visible(SmsCodePage.HEADER, timeout=3):
                print("\nℹ️ Продолжаем авторизацию с экрана ввода SMS-кода")
                sms = SmsCodePage(driver).wait_loaded()
                sms.enter_code()
                sms.click_confirm()
                home = HomePage(driver).wait_loaded()
                return _validate_home_state(home, expected_state)
            else:
                preview = preview.wait_loaded()
                preview.skip_preview()
                phone_page = PhoneAuthPage(driver).wait_loaded()

            phone_page.enter_phone(phone)
            phone_page.click_continue()
            phone_page.handle_code_delivery_modal(method="SMS")

            sms = SmsCodePage(driver).wait_loaded()
            sms.enter_code()
            sms.click_confirm()

            home = HomePage(driver).wait_loaded()
            return _validate_home_state(home, expected_state)

        except (TimeoutException, AssertionError) as exc:
            last_error = exc
            if attempt == 0:
                print(
                    "\n⚠️ Сбой при авторизации до главного экрана. "
                    "Пробуем повторить флоу с превью ещё раз..."
                )
                continue
            raise

    if last_error:
        raise last_error

    raise AssertionError("Авторизация завершилась без результата")


def run_auth_to_main(driver: "Remote", phone: str) -> None:
    """
    Вход в приложение без онбординга: превью → ввод телефона → SMS-код → главная.

    По завершении драйвер на главном экране (ожидается состояние NEW_USER для potential).
    Используется для тестов навигации под существующим пользователем (role: potential).

    Делает до двух попыток: если по пути приложение свернулось и после восстановления
    мы снова оказываемся на превью, флоу авторизации запускается заново.

    Args:
        driver: Appium WebDriver
        phone: Номер телефона (10 цифр), существующий в БД (например potential)
    """
    run_auth_to_home(driver, phone, expected_state=HomeState.NEW_USER)
    return

    last_error: Exception | None = None

    for attempt in range(2):
        try:
            if attempt > 0:
                print("\n🔁 Повторная попытка авторизации до главного экрана (run_auth_to_main)")

            # Всегда начинаем флоу с превью: если приложение перезапустилось,
            # PreviewPage(wait_loaded) просто откроется ещё раз.
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

            # Успешная авторизация — выходим из функции
            return

        except (TimeoutException, AssertionError) as exc:
            last_error = exc
            # Если это первая попытка — пробуем ещё раз с нуля.
            if attempt == 0:
                print(
                    "\n⚠️ Сбой при авторизации до главного экрана "
                    "(возможно, приложение перезапустилось или свернулось). Пробуем ещё раз..."
                )
                continue
            # Вторая неудачная попытка — пробрасываем ошибку дальше.
            raise

    # Теоретически сюда не дойдём, но на всякий случай
    if last_error:
        raise last_error


def run_full_onboarding_to_main(
    driver: "Remote",
    test_phone: str,
    *,
    country_name: str | None = None,
    first_name: str = "Appium",
    last_name: str = "Test",
) -> HomePage:
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
    if country_name:
        phone.select_country_and_enter(country_name, test_phone)
    else:
        phone.enter_phone(test_phone)
    phone.click_continue()
    phone.handle_code_delivery_modal(method="SMS")

    sms = SmsCodePage(driver).wait_loaded()
    sms.enter_code()
    sms.click_confirm()

    name_page = NamePage(driver).wait_loaded()
    name_page.enter_full_name(first_name, last_name)
    name_page.wait_clickable(name_page.NEXT_BUTTON, "Кнопка 'Далее' на шаге имени не активировалась")
    name_page.click_next()

    birth_date_page = BirthDatePage(driver).wait_loaded()
    for _ in range(3):
        birth_date_page.swipe_date_picker()
        time.sleep(0.5)
    birth_date_page.wait_clickable(
        birth_date_page.NEXT_BUTTON,
        "Кнопка 'Далее' на шаге даты рождения не активировалась",
    )
    birth_date_page.click_next()

    gender_page = GenderPage(driver).wait_loaded()
    gender_page.select_female()
    gender_page.wait_clickable(gender_page.NEXT_BUTTON, "Кнопка 'Далее' на шаге пола не активировалась")
    gender_page.click_next()

    height_page = HeightPage(driver).wait_loaded()
    height_page.select_height_cm(165)
    height_page.wait_clickable(height_page.NEXT_BUTTON, "Кнопка 'Далее' на шаге роста не активировалась")
    height_page.click_next()

    weight_page = WeightPage(driver).wait_loaded()
    weight_page.select_weight_kg(55)
    weight_page.wait_clickable(weight_page.NEXT_BUTTON, "Кнопка 'Далее' на шаге веса не активировалась")
    weight_page.click_next()

    fitness_goal_page = FitnessGoalPage(driver).wait_loaded()
    fitness_goal_page.select_weight_loss()
    fitness_goal_page.wait_clickable(
        fitness_goal_page.NEXT_BUTTON,
        "Кнопка 'Далее' на шаге цели не активировалась",
    )
    fitness_goal_page.click_next()

    workout_exp_page = WorkoutExperiencePage(driver).wait_loaded()
    workout_exp_page.select_no()
    workout_exp_page.wait_clickable(
        workout_exp_page.NEXT_BUTTON,
        "Кнопка 'Далее' на шаге опыта не активировалась",
    )
    workout_exp_page.click_next()

    frequency_page = WorkoutFrequencyPage(driver).wait_loaded()
    frequency_page.select_once_per_week()
    frequency_page.wait_clickable(
        frequency_page.NEXT_BUTTON,
        "Кнопка 'Далее' на шаге частоты не активировалась",
    )
    frequency_page.click_next()

    complete_page = OnboardingCompletePage(driver).wait_loaded()
    assert complete_page.verify_displayed_name(first_name), (
        f"Ожидалось имя '{first_name}' на экране завершения, "
        f"получено '{complete_page.get_displayed_name()}'"
    )
    complete_page.click_go_to_main()

    home = HomePage(driver).wait_loaded()
    if home.get_current_home_state() != HomeState.NEW_USER:
        raise AssertionError(
            "Ожидалось состояние главного экрана NEW_USER после онбординга"
        )
    return home
