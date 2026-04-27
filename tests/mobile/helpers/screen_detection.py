"""Fast current-screen detection for mobile flows."""

from enum import Enum
from typing import TYPE_CHECKING

from src.config.app_config import IMPLICIT_WAIT
from src.pages.mobile.auth import PhoneAuthPage, PreviewPage, SmsCodePage
from src.pages.mobile.home import HomeState
from src.pages.mobile.home.content import (
    HomeMemberContent,
    HomeNewUserContent,
    HomeRabbitHoleContent,
    HomeSubscribedContent,
)
from src.pages.mobile.shell.bottom_nav import BottomNav

if TYPE_CHECKING:
    from appium.webdriver import Remote


class MobileScreen(Enum):
    PREVIEW = "preview"
    PHONE_AUTH = "phone_auth"
    SMS_CODE = "sms_code"
    HOME_RABBIT_HOLE = "home_rabbit_hole"
    HOME_NEW_USER = "home_new_user"
    HOME_SUBSCRIBED = "home_subscribed"
    HOME_MEMBER = "home_member"
    UNKNOWN = "unknown"


def _detect_locators(content_cls):
    return getattr(content_cls, "DETECT_LOCATORS", (content_cls.DETECT_LOCATOR,))


_SCREEN_DETECTORS = [
    (MobileScreen.PREVIEW, (PreviewPage.START_BUTTON,)),
    (MobileScreen.PHONE_AUTH, (PhoneAuthPage.HEADER,)),
    (MobileScreen.SMS_CODE, (SmsCodePage.HEADER,)),
    (MobileScreen.HOME_RABBIT_HOLE, _detect_locators(HomeRabbitHoleContent)),
    (MobileScreen.HOME_NEW_USER, _detect_locators(HomeNewUserContent)),
    (MobileScreen.HOME_SUBSCRIBED, _detect_locators(HomeSubscribedContent)),
    (MobileScreen.HOME_MEMBER, _detect_locators(HomeMemberContent)),
]

_HOME_SCREEN_STATES = {
    MobileScreen.HOME_RABBIT_HOLE: HomeState.RABBIT_HOLE,
    MobileScreen.HOME_NEW_USER: HomeState.NEW_USER,
    MobileScreen.HOME_SUBSCRIBED: HomeState.SUBSCRIBED,
    MobileScreen.HOME_MEMBER: HomeState.MEMBER,
}


def home_state_for_screen(screen: MobileScreen) -> HomeState | None:
    """Return the HomeState represented by a detected home screen."""
    return _HOME_SCREEN_STATES.get(screen)


def _has_visible_element(driver: "Remote", locator) -> bool:
    by, value = locator
    elements = driver.find_elements(by, value)
    for element in elements:
        try:
            if element.is_displayed():
                return True
        except Exception:
            continue
    return False


def is_authorized_shell_visible(driver: "Remote") -> bool:
    """
    Return whether the authorized mobile shell tabbar is visible.

    This detects the app mode, not a specific Home state. All four text tabs
    must be visible so partial auth/navigation states are not treated as ready.
    """
    tab_locators = (
        BottomNav.TAB_MAIN,
        BottomNav.TAB_BOOKINGS,
        BottomNav.TAB_STATS,
        BottomNav.TAB_PROFILE,
    )
    try:
        driver.implicitly_wait(0)
        return all(_has_visible_element(driver, locator) for locator in tab_locators)
    finally:
        driver.implicitly_wait(IMPLICIT_WAIT)


def detect_current_screen(driver: "Remote") -> MobileScreen:
    """
    Detect the currently visible high-level mobile screen without long waits.

    Appium sessions in this project use an implicit wait. For screen probing we
    temporarily set it to zero so missing locators do not cost seconds each.
    """
    try:
        driver.implicitly_wait(0)
        for screen, locators in _SCREEN_DETECTORS:
            for locator in locators:
                if _has_visible_element(driver, locator):
                    return screen
        return MobileScreen.UNKNOWN
    finally:
        driver.implicitly_wait(IMPLICIT_WAIT)
