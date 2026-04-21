from src.pages.mobile.home import HomeState
from src.pages.mobile.home.content import HomeNewUserContent, HomeRabbitHoleContent
from tests.mobile.helpers.screen_detection import (
    MobileScreen,
    detect_current_screen,
    home_state_for_screen,
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
