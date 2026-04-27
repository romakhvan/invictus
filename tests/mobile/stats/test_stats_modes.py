"""Checks Stats tab entrypoints and controls in no-stats and with-stats modes."""

from typing import TYPE_CHECKING, Callable

import pytest

from src.pages.mobile.clubs.clubs_page import ClubsPage
from src.pages.mobile.stats.inbody_page import InBodyPage
from src.pages.mobile.stats.stats_page import StatsPage
from src.repositories.mobile_test_users_repository import (
    MobileTestUserScenario,
    MobileTestUserSelector,
)
from tests.mobile.helpers.session_helpers import ensure_test_user_session

if TYPE_CHECKING:
    from appium.webdriver import Remote


def _check_no_stats_entrypoints(stats: StatsPage) -> None:
    """No-stats mode exposes InBody and opens subscription selection from Stats."""
    stats.assert_inbody_entrypoint_visible()

    inbody = stats.open_inbody()
    assert isinstance(inbody, InBodyPage), (
        f"Stats entrypoint 'open_inbody' returned {type(inbody).__name__}, "
        "expected InBodyPage."
    )

    stats = inbody.nav.open_stats()
    assert isinstance(stats, StatsPage)

    clubs_page = stats.open_subscription_selection()
    assert isinstance(clubs_page, ClubsPage), (
        "Stats entrypoint 'open_subscription_selection' returned "
        f"{type(clubs_page).__name__}, expected ClubsPage."
    )


def _check_with_stats_controls(stats: StatsPage) -> None:
    """With-stats mode exposes InBody and lets users switch stats periods."""
    stats.assert_inbody_entrypoint_visible()
    stats.select_month_period().assert_ui()
    stats.select_year_period().assert_ui()
    stats.open_datepicker()


@pytest.mark.mobile
@pytest.mark.parametrize(
    "user_scenario,stats_check",
    [
        (
            MobileTestUserScenario.POTENTIAL_USER,
            _check_no_stats_entrypoints,
        ),
        (
            MobileTestUserScenario.RABBIT_HOLE_USER,
            _check_with_stats_controls,
        ),
    ],
    ids=[
        "no_stats-potential-entrypoints",
        "with_stats-rabbit_hole-controls",
    ],
)
def test_stats_modes_expose_expected_entrypoints(
    mobile_driver,
    db,
    user_scenario: MobileTestUserScenario,
    stats_check: Callable[[StatsPage], None],
):
    """Stats behaves as expected for users without and with statistics."""
    context = MobileTestUserSelector(db).select_or_skip(user_scenario)
    driver: "Remote" = mobile_driver

    nav = ensure_test_user_session(driver, db, context)
    stats = nav.open_stats()
    assert isinstance(stats, StatsPage)

    print(f"Checking Stats scenario '{stats_check.__name__}'")
    stats_check(stats)
    print(f"Stats scenario '{stats_check.__name__}' passed")
