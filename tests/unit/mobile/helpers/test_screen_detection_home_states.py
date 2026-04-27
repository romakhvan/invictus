from src.pages.mobile.home import HomeState
from src.pages.mobile.home.content import (
    HomeMemberContent,
    HomeNewUserContent,
    HomeRabbitHoleContent,
)
from src.pages.mobile.auth import PreviewPage
from src.pages.mobile.shell.bottom_nav import BottomNav
from tests.mobile.helpers.screen_detection import (
    MobileScreen,
    detect_current_screen,
    home_state_for_screen,
    is_authorized_shell_visible,
)


def test_home_state_for_screen_maps_rabbit_hole_home():
    assert home_state_for_screen(MobileScreen.HOME_RABBIT_HOLE) == HomeState.RABBIT_HOLE


def test_detect_current_screen_prefers_rabbit_hole_fallback_over_new_user_marker():
    visible_locators = {
        HomeRabbitHoleContent.AVAILABLE_UNTIL_LABEL,
        HomeNewUserContent.DETECT_LOCATOR,
    }

    class FakeElement:
        def is_displayed(self):
            return True

    class FakeDriver:
        def __init__(self):
            self.waits = []

        def implicitly_wait(self, timeout):
            self.waits.append(timeout)

        def find_elements(self, by, value):
            if (by, value) in visible_locators:
                return [FakeElement()]
            return []

    driver = FakeDriver()

    assert detect_current_screen(driver) == MobileScreen.HOME_RABBIT_HOLE


def test_detect_current_screen_does_not_treat_no_subscription_label_as_new_user():
    class FakeElement:
        def is_displayed(self):
            return True

    class FakeDriver:
        def __init__(self):
            self.waits = []

        def implicitly_wait(self, timeout):
            self.waits.append(timeout)

        def find_elements(self, by, value):
            if (by, value) == HomeNewUserContent.NO_SUBSCRIPTION_LABEL:
                return [FakeElement()]
            return []

    assert detect_current_screen(FakeDriver()) == MobileScreen.UNKNOWN


def test_detect_current_screen_does_not_treat_profile_subscriptions_as_member_home():
    class FakeElement:
        def is_displayed(self):
            return True

    class FakeDriver:
        def __init__(self):
            self.waits = []

        def implicitly_wait(self, timeout):
            self.waits.append(timeout)

        def find_elements(self, by, value):
            if (
                (by, value) == HomeMemberContent.DETECT_LOCATOR
                and 'contains(@text, "Абонемент")' in value
                and 'not(@text="Абонементы")' not in value
            ):
                return [FakeElement()]
            return []

    assert detect_current_screen(FakeDriver()) == MobileScreen.UNKNOWN


def test_detect_current_screen_detects_new_user_by_tell_more_entrypoint():
    class FakeElement:
        def is_displayed(self):
            return True

    class FakeDriver:
        def __init__(self):
            self.waits = []

        def implicitly_wait(self, timeout):
            self.waits.append(timeout)

        def find_elements(self, by, value):
            if (by, value) == HomeNewUserContent.TELL_MORE_ENTRYPOINT:
                return [FakeElement()]
            return []

    assert detect_current_screen(FakeDriver()) == MobileScreen.HOME_NEW_USER


def test_is_authorized_shell_visible_when_all_main_tabs_are_visible():
    visible_locators = {
        BottomNav.TAB_MAIN,
        BottomNav.TAB_BOOKINGS,
        BottomNav.TAB_STATS,
        BottomNav.TAB_PROFILE,
    }

    class FakeElement:
        def is_displayed(self):
            return True

    class FakeDriver:
        def __init__(self):
            self.waits = []

        def implicitly_wait(self, timeout):
            self.waits.append(timeout)

        def find_elements(self, by, value):
            if (by, value) in visible_locators:
                return [FakeElement()]
            return []

    assert is_authorized_shell_visible(FakeDriver()) is True


def test_is_authorized_shell_visible_false_on_preview_without_tabs():
    class FakeElement:
        def is_displayed(self):
            return True

    class FakeDriver:
        def __init__(self):
            self.waits = []

        def implicitly_wait(self, timeout):
            self.waits.append(timeout)

        def find_elements(self, by, value):
            if (by, value) == PreviewPage.START_BUTTON:
                return [FakeElement()]
            return []

    assert is_authorized_shell_visible(FakeDriver()) is False


def test_is_authorized_shell_visible_false_when_only_some_tabs_are_visible():
    visible_locators = {BottomNav.TAB_MAIN, BottomNav.TAB_STATS}

    class FakeElement:
        def is_displayed(self):
            return True

    class FakeDriver:
        def __init__(self):
            self.waits = []

        def implicitly_wait(self, timeout):
            self.waits.append(timeout)

        def find_elements(self, by, value):
            if (by, value) in visible_locators:
                return [FakeElement()]
            return []

    assert is_authorized_shell_visible(FakeDriver()) is False
