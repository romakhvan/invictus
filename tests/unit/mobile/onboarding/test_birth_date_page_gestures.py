import types

from src.pages.mobile.onboarding.birth_date_page import BirthDatePage


def test_birth_date_swipe_date_picker_delegates_to_common_w3c_swipe():
    page = object.__new__(BirthDatePage)
    swipes = []

    def swipe_by_w3c_actions(self, start_x, start_y, end_x, end_y):
        swipes.append((start_x, start_y, end_x, end_y))

    page.swipe_by_w3c_actions = types.MethodType(swipe_by_w3c_actions, page)

    page.swipe_date_picker()

    assert swipes == [(933, 1004, 922, 1687)]
