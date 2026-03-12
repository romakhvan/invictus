"""
Конфигурация фикстур для mobile тестов.
Mobile тесты используют STAGE окружение.
"""

import pytest
import pymongo
import time
from typing import TYPE_CHECKING

from src.config.db_config import MONGO_URI_STAGE, DB_NAME
from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.home import HomePage, HomeState
from src.pages.mobile.profile.profile_page import ProfilePage
from src.repositories.users_repository import (
    get_phone_for_potential_user,
    get_user_role_by_phone,
)
from tests.mobile.helpers.onboarding_helpers import run_auth_to_main
from tests.mobile.helpers.profile_helpers import assert_profile_matches_potential_user

if TYPE_CHECKING:
    from appium.webdriver import Remote


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB STAGE.
    Используется для всех mobile тестов.
    """
    print("\n🔌 Connecting to MongoDB STAGE...")
    client = pymongo.MongoClient(MONGO_URI_STAGE)
    db = client[DB_NAME]
    yield db
    print("\n🧹 Closing Mongo STAGE connection.")
    client.close()


def _get_current_user_role_via_profile(driver, db):
    """
    Сначала пытается перейти на экран «Профиль» (клик по табу).
    Если таббар есть — приложение залогинено: считывает номер с экрана, ищет роль в БД.
    Если таб «Профиль» не найден (например, открыт Preview) — возвращает None.
    """
    try:
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        from src.pages.mobile.shell.bottom_nav import BottomNav

        # Короткий таймаут: если таббар есть (залогинены), таб «Профиль» появится быстро
        wait_probe = WebDriverWait(driver, 6)
        nav = BottomNav(driver)
        wait_probe.until(EC.element_to_be_clickable(nav.TAB_PROFILE))
        nav.click(nav.TAB_PROFILE)
        profile = ProfilePage(driver).wait_loaded()
        phone_ui = profile.get_displayed_phone()
        if not phone_ui:
            return None
        return get_user_role_by_phone(db, phone_ui)
    except Exception:
        return None


@pytest.fixture
def potential_user_on_main_screen(mobile_driver, db):
    """
    Драйвер на главном экране в состоянии NEW_USER под существующим пользователем (role: potential).

    Для каждого вызова фикстуры:
    - перезапускаем приложение (terminate_app + activate_app);
    - если приложение открыто в режиме с таббаром (главная и т.д.): переходим в Профиль,
      считываем номер телефона с экрана, по номеру в БД проверяем роль; если роль potential —
      возвращаем драйвер на главной; если роль другая — пропускаем тест;
    - если перейти в профиль не удалось (не залогинены, экран Preview и т.д.) —
      выполняем вход: превью → телефон → SMS → главная под potential.
    Требует в БД пользователя с role: 'potential' и полем firstName.
    """
    try:
        mobile_driver.terminate_app(MOBILE_APP_PACKAGE)
        time.sleep(1)
        mobile_driver.activate_app(MOBILE_APP_PACKAGE)
        time.sleep(2)
    except Exception:
        pass

    # Проверяем под каким клиентом выполнен вход: Профиль → номер → роль в БД
    role = _get_current_user_role_via_profile(mobile_driver, db)
    if role is not None:
        if role == "potential":
            # Уже на Профиле после _get_current_user_role_via_profile — сверяем без повторного открытия
            profile = ProfilePage(mobile_driver).wait_loaded()
            print("Проверка: сверка данных в профиле с potential-пользователем в БД...")
            assert_profile_matches_potential_user(db, profile)
            home = profile.nav.open_main()  # возврат на главную, wait_loaded уже внутри
            if home.get_current_home_state() != HomeState.NEW_USER:
                pytest.skip(
                    "Вход под potential, но главный экран не в состоянии NEW_USER. "
                    "Возможна рассинхронизация состояния приложения."
                )
            yield mobile_driver
            return
        pytest.skip(
            f"В приложении выполнен вход не под new user (potential). "
            f"Роль текущего пользователя в БД: {role}. "
            "Сбросьте данные приложения или выполните вход под пользователем с role: potential."
        )

    # Не удалось определить пользователя по профилю (не залогинены или другой экран) — вход с нуля
    phone = get_phone_for_potential_user(db)
    if not phone:
        pytest.skip(
            "В БД нет пользователя с role: 'potential' и полем firstName. "
            "Создайте такого пользователя (например, пройдите онбординг в отдельном тесте)."
        )
    run_auth_to_main(mobile_driver, phone)
    # Один раз сверяем профиль с БД; при несовпадении тест упадёт на assert
    home = HomePage(mobile_driver).wait_loaded()
    profile = home.nav.open_profile()
    print("Проверка: сверка данных в профиле с potential-пользователем в БД...")
    assert_profile_matches_potential_user(db, profile)
    profile.nav.open_main()
    yield mobile_driver


# ==================== Автоматический трекинг времени выполнения ====================

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Сохраняем время начала теста."""
    item.test_start_time = time.time()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Выводим время выполнения теста после его завершения."""
    outcome = yield
    report = outcome.get_result()
    
    # Выводим время только после завершения фазы выполнения теста
    if report.when == "call" and hasattr(item, 'test_start_time'):
        execution_time = time.time() - item.test_start_time
        
        if report.passed:
            print(f"\n✅ ТЕСТ ПРОЙДЕН")
        elif report.failed:
            print(f"\n❌ ТЕСТ ПРОВАЛЕН")
        elif report.skipped:
            print(f"\n⏭️  ТЕСТ ПРОПУЩЕН")
        
        print(f"⏱️  Время выполнения: {execution_time:.2f} сек ({execution_time/60:.2f} мин)")


# ==================== Интерактивное меню после выбранных тестов ====================
# Меню вызывается в teardown фикстуры appium_driver (tests/conftest.py), когда
# тест помечен @pytest.mark.interactive_mobile или передан --keepalive.
# Так сессия не закрывается до выхода из меню — команды 1–9 работают.

