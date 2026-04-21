from datetime import datetime

from src.validators.push_notifications.guest_visit_discount_push_validator import (
    _build_notification_row,
    _build_notifications_tables_html,
    _build_notifications_tables_html_with_stats,
    _entry_club_matches_active_subscription_club,
    _extract_awaylink_phone,
    _resolve_club_awaylink_key,
    _summarize_notification_docs_by_language,
)


def test_build_notification_row_includes_awaylink_and_club_name():
    row = _build_notification_row(
        notification_id="notification-1",
        language="RU",
        created_at=datetime(2026, 4, 20, 6, 14, 6, 388000),
        user_id="user-1",
        away_link="https://example.com/offer",
        last_entry_time=datetime(2026, 4, 20, 5, 44, 6, 273000),
        last_entry_club_id="club-1",
        last_entry_club_name="Invictus Test Club",
        active_subscription_ids=["subscription-1", "subscription-2"],
        active_subscription_club_names=["Invictus Green Mall", "Invictus Semey"],
    )

    assert row == [
        "notification-1",
        "RU",
        "2026-04-20 06:14:06",
        "user-1",
        "https://example.com/offer",
        "2026-04-20 05:44:06",
        "club-1",
        "Invictus Test Club",
        "subscription-1, subscription-2",
        "Invictus Green Mall, Invictus Semey",
    ]


def test_build_notification_row_shortens_awaylink_query_text():
    row = _build_notification_row(
        notification_id="notification-2",
        language="RU",
        created_at=datetime(2026, 4, 20, 6, 14, 6, 388000),
        user_id="user-2",
        away_link=(
            "https://wa.me/77470941998?"
            "text=%D0%A5%D0%BE%D1%87%D1%83%20%D0%BA%D1%83%D0%BF%D0%B8%D1%82%D1%8C%20"
            "%D0%B0%D0%B1%D0%BE%D0%BD%D0%B5%D0%BC%D0%B5%D0%BD%D1%82%20%D0%BF%D0%BE%20"
            "%D1%81%D0%BA%D0%B8%D0%B4%D0%BA%D0%B5"
        ),
        last_entry_time=datetime(2026, 4, 20, 5, 44, 6, 273000),
        last_entry_club_id="club-2",
        last_entry_club_name="Invictus WhatsApp Club",
        active_subscription_ids=[],
        active_subscription_club_names=[],
    )

    assert row[4] == "https://wa.me/77470941998 | text=Хочу купить абонемент по скидке"


def test_extract_awaylink_phone_returns_whatsapp_number():
    phone = _extract_awaylink_phone(
        "https://wa.me/77074646468?text=%D0%A5%D0%BE%D1%87%D1%83"
    )

    assert phone == "77074646468"


def test_resolve_club_awaylink_key_supports_alias_groups():
    assert _resolve_club_awaylink_key("Invictus Fitness Gagarin") == "gagarin_samal"
    assert _resolve_club_awaylink_key("Invictus Fitness Samal") == "gagarin_samal"
    assert _resolve_club_awaylink_key("Invictus GO Tau-Samal") == "gagarin_samal"
    assert _resolve_club_awaylink_key("Invictus Fitness Nursat") == "nursat_alfarabi"
    assert _resolve_club_awaylink_key("Invictus Fitness Al-Farabi") == "nursat_alfarabi"
    assert _resolve_club_awaylink_key("Invictus Fitness Highvill") == "highville"


def test_entry_club_matches_active_subscription_club_returns_true_on_any_match():
    assert _entry_club_matches_active_subscription_club(
        entry_club_id="club-1",
        active_subscription_club_ids=["club-2", "club-1", None],
    ) is True


def test_entry_club_matches_active_subscription_club_ignores_empty_values():
    assert _entry_club_matches_active_subscription_club(
        entry_club_id="club-1",
        active_subscription_club_ids=[None, "", "club-2"],
    ) is False


def test_build_notifications_tables_html_groups_rows_by_language_with_counts():
    html = _build_notifications_tables_html(
        {
            "RU": [[
                "notification-1",
                "RU",
                "2026-04-20 06:14:06",
                "user-1",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
            ]],
            "EN": [
                [
                    "notification-2",
                    "EN",
                    "2026-04-20 06:15:06",
                    "user-2",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                ],
                [
                    "notification-3",
                    "EN",
                    "2026-04-20 06:16:06",
                    "user-3",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                    "-",
                ],
            ],
        }
    )

    assert "Language: RU (1)" in html
    assert "Language: EN (2)" in html
    assert html.count("<table>") == 2


def test_summarize_notification_docs_by_language_counts_all_matching_docs():
    summary = _summarize_notification_docs_by_language(
        [
            {"description": "скидка в день гостевого визита [EN]", "toUsers": ["u1"]},
            {"description": "скидка в день гостевого визита [EN]", "toUsers": ["u2", "u3"]},
            {"description": "скидка в день гостевого визита [RU]", "toUsers": ["u4"]},
        ]
    )

    assert summary["docs"] == 3
    assert summary["recipients"] == 4
    assert summary["languages"] == {
        "EN": {"docs": 2, "recipients": 3},
        "RU": {"docs": 1, "recipients": 1},
    }


def test_build_notifications_tables_html_with_stats_shows_period_doc_counts_separately():
    html = _build_notifications_tables_html_with_stats(
        rows_by_language={
            "EN": [[
                "notification-39",
                "EN",
                "2026-04-20 06:16:06",
                "user-39",
                "-",
                "-",
                "-",
                "-",
                "-",
                "-",
            ]],
        },
        language_stats={
            "EN": {"docs": 39, "recipients": 39},
            "RU": {"docs": 5, "recipients": 7},
        },
    )

    assert "Language summary" in html
    assert "matching docs in period" in html
    assert "Language: EN (checked rows: 1, matching docs: 39, recipients in period: 39)" in html
    assert "RU" in html
