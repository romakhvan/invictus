import types

from src.pages.mobile.stats.stats_page import StatsPage


def test_stats_page_accepts_actual_statistics_state():
    page = object.__new__(StatsPage)
    visible_locators = {
        StatsPage.ACTUAL_STATS_STREAK_LABEL,
        StatsPage.ACTUAL_STATS_WEEK_FILTER,
        StatsPage.ACTUAL_STATS_MONTH_FILTER,
        StatsPage.ACTUAL_STATS_YEAR_FILTER,
        StatsPage.ACTUAL_STATS_HOURS_LABEL,
    }
    waited_locators = []

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    def is_visible(self, locator, *_args, **_kwargs):
        return locator in visible_locators

    page.wait_visible = types.MethodType(wait_visible, page)
    page.is_visible = types.MethodType(is_visible, page)

    page.assert_ui()

    assert StatsPage.TITLE_MY_STATS in waited_locators
    assert StatsPage.ACTUAL_STATS_WEEK_FILTER in waited_locators
    assert StatsPage.ACTUAL_STATS_HOURS_LABEL in waited_locators


def test_stats_page_accepts_actual_statistics_month_state():
    page = object.__new__(StatsPage)
    visible_locators = {
        StatsPage.ACTUAL_STATS_STREAK_LABEL,
        StatsPage.ACTUAL_STATS_WEEK_FILTER,
        StatsPage.ACTUAL_STATS_MONTH_FILTER,
        StatsPage.ACTUAL_STATS_YEAR_FILTER,
        StatsPage.ACTUAL_STATS_TIME_IN_GYM_LABEL,
    }
    waited_locators = []

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    def is_visible(self, locator, *_args, **_kwargs):
        return locator in visible_locators

    page.wait_visible = types.MethodType(wait_visible, page)
    page.is_visible = types.MethodType(is_visible, page)

    page.assert_ui()

    assert StatsPage.TITLE_MY_STATS in waited_locators
    assert StatsPage.ACTUAL_STATS_HOURS_LABEL not in waited_locators
    assert StatsPage.ACTUAL_STATS_TIME_IN_GYM_LABEL in waited_locators


def test_stats_page_asserts_inbody_entrypoint_visible():
    page = object.__new__(StatsPage)
    waited_locators = []

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    page.wait_visible = types.MethodType(wait_visible, page)

    page.assert_inbody_entrypoint_visible()

    assert waited_locators == [StatsPage.INBODY_ENTRYPOINT]


def test_stats_page_selects_month_period():
    page = object.__new__(StatsPage)
    clicked_locators = []
    waited_locators = []
    expected_period_locator = page._current_month_period_locator()

    def click(self, locator, *_args, **_kwargs):
        clicked_locators.append(locator)

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    page.click = types.MethodType(click, page)
    page.wait_visible = types.MethodType(wait_visible, page)

    result = page.select_month_period()

    assert result is page
    assert clicked_locators == [StatsPage.ACTUAL_STATS_MONTH_FILTER]
    assert StatsPage.ACTUAL_STATS_HOURS_LABEL not in waited_locators
    assert StatsPage.ACTUAL_STATS_TIME_IN_GYM_LABEL in waited_locators
    assert expected_period_locator in waited_locators


def test_stats_page_selects_week_period_with_hours_marker():
    page = object.__new__(StatsPage)
    clicked_locators = []
    waited_locators = []

    def click(self, locator, *_args, **_kwargs):
        clicked_locators.append(locator)

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    page.click = types.MethodType(click, page)
    page.wait_visible = types.MethodType(wait_visible, page)

    result = page.select_week_period()

    assert result is page
    assert clicked_locators == [StatsPage.ACTUAL_STATS_WEEK_FILTER]
    assert StatsPage.ACTUAL_STATS_HOURS_LABEL in waited_locators
    assert StatsPage.WEEK_PERIOD_RANGE in waited_locators


def test_stats_page_selects_year_period():
    page = object.__new__(StatsPage)
    clicked_locators = []
    waited_locators = []
    expected_period_locator = page._current_year_period_locator()

    def click(self, locator, *_args, **_kwargs):
        clicked_locators.append(locator)

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    page.click = types.MethodType(click, page)
    page.wait_visible = types.MethodType(wait_visible, page)

    result = page.select_year_period()

    assert result is page
    assert clicked_locators == [StatsPage.ACTUAL_STATS_YEAR_FILTER]
    assert StatsPage.ACTUAL_STATS_HOURS_LABEL not in waited_locators
    assert StatsPage.ACTUAL_STATS_TIME_IN_GYM_LABEL in waited_locators
    assert expected_period_locator in waited_locators


def test_stats_page_opens_datepicker_from_visible_period_header():
    page = object.__new__(StatsPage)
    clicked_locators = []
    waited_locators = []
    month_period_locator = page._current_month_period_locator()

    def click(self, locator, *_args, **_kwargs):
        clicked_locators.append(locator)

    def wait_visible(self, locator, *_args, **_kwargs):
        waited_locators.append(locator)
        return object()

    def is_visible(self, locator, *_args, **_kwargs):
        return locator == month_period_locator

    page.click = types.MethodType(click, page)
    page.wait_visible = types.MethodType(wait_visible, page)
    page.is_visible = types.MethodType(is_visible, page)

    result = page.open_datepicker()

    assert result is page
    assert clicked_locators == [month_period_locator]
    assert waited_locators == [month_period_locator]
