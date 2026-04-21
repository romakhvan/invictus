"""
Smoke-тест: полный флоу онбординга нового клиента.
"""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from appium.webdriver import Remote

from src.config.app_config import MOBILE_APP_PACKAGE
from src.pages.mobile.home import HomeState
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)
from tests.mobile.helpers.onboarding_helpers import run_full_onboarding_to_main


@pytest.mark.mobile
@pytest.mark.smoke
def test_new_client_onboarding_full_flow(mobile_driver: "Remote", db, onboarding_phone):
    """
    Smoke-тест: полный онбординг нового клиента от входа до главного экрана.
    """
    driver = mobile_driver

    selector = MobileTestUserSelector(db)
    context = selector.select_or_skip(
        scenario=MobileTestUserScenario.ONBOARDING_NEW_USER,
        override_phone=onboarding_phone,
    )

    test_phone = context.phone
    print(f"📱 Используется номер для онбординга: {test_phone}")

    assert driver.current_package == MOBILE_APP_PACKAGE, (
        f"Неверный package: ожидался {MOBILE_APP_PACKAGE}, получен {driver.current_package}"
    )

    home = run_full_onboarding_to_main(driver, test_phone)
    assert home.get_current_home_state() == HomeState.NEW_USER
    home.get_content().assert_ui()
