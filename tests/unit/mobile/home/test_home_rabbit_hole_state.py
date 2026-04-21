from appium.webdriver.common.appiumby import AppiumBy

import src.pages.mobile.home.home_page as home_page
import src.pages.mobile.home as home
from src.pages.mobile.home import HomePage
from src.pages.mobile.home import HomeState


class _VisibleElement:
    def is_displayed(self):
        return True


def test_home_state_includes_rabbit_hole():
    assert HomeState.RABBIT_HOLE.value == "rabbit_hole"


def test_rabbit_hole_content_uses_combo_training_marker():
    assert home.HomeRabbitHoleContent.DETECT_LOCATOR == (
        AppiumBy.XPATH,
        '//android.widget.TextView[@text="3 КОМБО-ТРЕНИРОВКИ"]',
    )


def test_rabbit_hole_state_is_detected_before_new_user():
    state_order = [state for state, _content_cls in home_page._STATE_DETECTORS]

    assert state_order.index(HomeState.RABBIT_HOLE) < state_order.index(
        HomeState.NEW_USER
    )


def test_home_state_detection_uses_fast_scan_instead_of_sequential_waits():
    class FakeDriver:
        def __init__(self):
            self.implicit_waits = []
            self.find_calls = []

        def implicitly_wait(self, timeout):
            self.implicit_waits.append(timeout)

        def find_elements(self, by, value):
            self.find_calls.append((by, value))
            if (by, value) == home.HomeNewUserContent.DETECT_LOCATOR:
                return [_VisibleElement()]
            return []

    class SlowWaitWasUsed(Exception):
        pass

    page = HomePage.__new__(HomePage)
    page.driver = FakeDriver()
    page._wait = lambda timeout=None: (_ for _ in ()).throw(SlowWaitWasUsed())

    assert page.get_current_home_state() == HomeState.NEW_USER
    assert page.driver.implicit_waits == [0, home_page.IMPLICIT_WAIT]


def test_home_state_does_not_treat_no_subscription_label_as_new_user():
    class FakeDriver:
        def __init__(self):
            self.implicit_waits = []

        def implicitly_wait(self, timeout):
            self.implicit_waits.append(timeout)

        def find_elements(self, by, value):
            if (by, value) == home.HomeNewUserContent.NO_SUBSCRIPTION_LABEL:
                return [_VisibleElement()]
            return []

    page = HomePage.__new__(HomePage)
    page.driver = FakeDriver()

    assert page.get_current_home_state() == HomeState.UNKNOWN
