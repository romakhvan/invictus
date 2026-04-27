import types

from selenium.common.exceptions import TimeoutException

from src.pages.mobile.profile.profile_page import ProfilePage


def test_profile_page_recognition_uses_only_subscriptions_section():
    page = object.__new__(ProfilePage)
    waited_locators = []

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    page.wait_visible = types.MethodType(wait_visible, page)

    page.assert_ui()

    assert waited_locators == [ProfilePage.SECTION_SUBSCRIPTIONS]


def test_profile_logout_clicks_logout_action_when_account_actions_block_visible():
    page = object.__new__(ProfilePage)
    checked_locators = []
    clicked_locators = []
    swipes = []

    def is_visible(self, locator, timeout=None):
        checked_locators.append((locator, timeout))
        return locator in ProfilePage.ACCOUNT_ACTIONS_BLOCK_LOCATORS

    def click(self, locator, timeout=None):
        clicked_locators.append((locator, timeout))

    def swipe_by_w3c_actions(self, start_x, start_y, end_x, end_y):
        swipes.append((start_x, start_y, end_x, end_y))

    page.is_visible = types.MethodType(is_visible, page)
    page.click = types.MethodType(click, page)
    page.swipe_by_w3c_actions = types.MethodType(swipe_by_w3c_actions, page)

    page.logout()

    assert checked_locators == [
        (ProfilePage.ACCOUNT_ACTIONS_SECTION, 1),
        (ProfilePage.LOGOUT_ACTION, 1),
        (ProfilePage.DELETE_ACCOUNT_ACTION, 1),
    ]
    assert clicked_locators == [(ProfilePage.LOGOUT_ACTION, 5)]
    assert swipes == []


def test_profile_logout_scrolls_until_account_actions_block_visible():
    page = object.__new__(ProfilePage)
    clicked_locators = []
    swipes = []

    def is_visible(self, locator, timeout=None):
        return len(swipes) >= 1 and locator in ProfilePage.ACCOUNT_ACTIONS_BLOCK_LOCATORS

    def click(self, locator, timeout=None):
        clicked_locators.append((locator, timeout))

    def swipe_by_w3c_actions(self, start_x, start_y, end_x, end_y):
        swipes.append((start_x, start_y, end_x, end_y))

    page.is_visible = types.MethodType(is_visible, page)
    page.click = types.MethodType(click, page)
    page.swipe_by_w3c_actions = types.MethodType(swipe_by_w3c_actions, page)

    page.logout()

    assert swipes == [
        (
            ProfilePage.PROFILE_SCROLL_DOWN_START_X,
            ProfilePage.PROFILE_SCROLL_DOWN_START_Y,
            ProfilePage.PROFILE_SCROLL_DOWN_END_X,
            ProfilePage.PROFILE_SCROLL_DOWN_END_Y,
        )
    ]
    assert clicked_locators == [(ProfilePage.LOGOUT_ACTION, 5)]


def test_profile_logout_requires_account_actions_and_delete_markers():
    page = object.__new__(ProfilePage)
    clicked_locators = []

    def is_visible(self, locator, timeout=None):
        return locator == ProfilePage.LOGOUT_ACTION

    def click(self, locator, timeout=None):
        clicked_locators.append((locator, timeout))

    page.is_visible = types.MethodType(is_visible, page)
    page.click = types.MethodType(click, page)

    try:
        page.logout(max_swipes=0)
    except TimeoutException as exc:
        assert "Account actions block is not visible" in str(exc)
    else:
        raise AssertionError("Expected logout to fail without mandatory block markers.")

    assert clicked_locators == []


def test_profile_logout_raises_when_block_not_visible_after_swipes():
    page = object.__new__(ProfilePage)
    checked_locators = []
    swipes = []

    def is_visible(self, locator, timeout=None):
        checked_locators.append((locator, timeout))
        return False

    def swipe_by_w3c_actions(self, start_x, start_y, end_x, end_y):
        swipes.append((start_x, start_y, end_x, end_y))

    page.is_visible = types.MethodType(is_visible, page)
    page.swipe_by_w3c_actions = types.MethodType(swipe_by_w3c_actions, page)

    try:
        page.logout(max_swipes=2)
    except TimeoutException as exc:
        assert "Account actions block is not visible" in str(exc)
    else:
        raise AssertionError("Expected logout to fail when account actions block is not visible.")

    assert checked_locators == [
        (ProfilePage.ACCOUNT_ACTIONS_SECTION, 1),
        (ProfilePage.ACCOUNT_ACTIONS_SECTION, 1),
        (ProfilePage.ACCOUNT_ACTIONS_SECTION, 1),
    ]
    assert swipes == [
        (
            ProfilePage.PROFILE_SCROLL_DOWN_START_X,
            ProfilePage.PROFILE_SCROLL_DOWN_START_Y,
            ProfilePage.PROFILE_SCROLL_DOWN_END_X,
            ProfilePage.PROFILE_SCROLL_DOWN_END_Y,
        ),
        (
            ProfilePage.PROFILE_SCROLL_DOWN_START_X,
            ProfilePage.PROFILE_SCROLL_DOWN_START_Y,
            ProfilePage.PROFILE_SCROLL_DOWN_END_X,
            ProfilePage.PROFILE_SCROLL_DOWN_END_Y,
        ),
    ]
