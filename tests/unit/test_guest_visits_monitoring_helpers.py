from tests.backend.guest_visits.test_guest_visits_monitoring import (
    _build_clients_with_guest_visits_html,
    _build_client_row,
    _limit_top_client_rows,
)


def test_guest_visits_monitoring_helpers_limit_rows_and_render_two_collapsible_tables():
    rows = [
        [
            f"user-{index}",
            "client",
            100 - index,
            index % 3,
            100,
            "2026-04-20 10:00:00",
            "2026-04-19 09:30:00",
            f"sub-{index}",
            "2026-10-20 10:00:00",
        ]
        for index in range(30)
    ]

    limited_rows = _limit_top_client_rows(rows)

    assert len(limited_rows) == 25
    assert limited_rows[0][0] == "user-0"
    assert limited_rows[-1][0] == "user-24"

    html = _build_clients_with_guest_visits_html(
        used_rows=limited_rows,
        unused_rows=limited_rows[:10],
    )

    assert "Top clients by used guest visits" in html
    assert "Top clients by unused guest visits" in html
    assert html.count("<details") == 2
    assert "Last successful entry" in html
    assert "Latest userSubscription ID" in html
    assert "Subscription endDate" in html


def test_build_client_row_includes_enriched_fields():
    row = _build_client_row(
        user_id="user-1",
        role="client",
        used_count=5,
        unused_count=2,
        latest_visit_at="2026-04-20 10:00:00",
        last_successful_entry="2026-04-19 09:30:00",
        subscription_id="sub-1",
        subscription_end_date="2026-10-20 10:00:00",
    )

    assert row == [
        "user-1",
        "client",
        5,
        2,
        7,
        "2026-04-20 10:00:00",
        "2026-04-19 09:30:00",
        "sub-1",
        "2026-10-20 10:00:00",
    ]
