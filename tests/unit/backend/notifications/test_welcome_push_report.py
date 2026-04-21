from datetime import datetime, timedelta

from tests.backend.notifications.test_welcome_push import (
    WELCOME_PUSH_DESCRIPTION,
    WELCOME_PUSH_TEXT,
    WELCOME_PUSH_TITLE,
    _build_language_summary_html,
    _build_language_summary_model,
    _build_pass_criteria_text,
    _build_recipient_mismatch_html,
    _build_user_diagnostic_rows,
    _filter_users_by_purchase_age,
)


def _notification_doc(index, language):
    return {
        "_id": f"notification-{language}-{index}",
        "created_at": datetime(2026, 4, 21, 9, index, 0),
        "description": f"Welcome push [{language}]",
        "title": f"Title {language} {index}",
        "text": f"Text {language} {index}",
        "toUsers": [f"user-{language}-{index}"],
    }


class _FakeCollection:
    def __init__(self, docs):
        self._docs = docs

    def find(self, query, projection):
        users = {str(user_id) for user_id in query["user"]["$in"]}
        return [doc for doc in self._docs if str(doc.get("user")) in users]


class _FakeDb:
    def __init__(self, subscriptions, entries):
        self._collections = {
            "usersubscriptions": _FakeCollection(subscriptions),
            "accesscontrols": _FakeCollection(entries),
        }

    def __getitem__(self, name):
        return self._collections[name]


def test_build_language_summary_model_limits_examples_to_10_per_language():
    docs = [_notification_doc(index, "RU") for index in range(12)]
    docs += [_notification_doc(index, "EN") for index in range(3)]

    summary = _build_language_summary_model(docs, examples_per_language=10)

    assert summary["RU"]["docs"] == 12
    assert summary["RU"]["recipients"] == 12
    assert len(summary["RU"]["examples"]) == 10
    assert summary["RU"]["examples"][0]["notification_id"] == "notification-RU-0"
    assert summary["RU"]["examples"][-1]["notification_id"] == "notification-RU-9"
    assert summary["EN"]["docs"] == 3
    assert len(summary["EN"]["examples"]) == 3


def test_build_language_summary_html_shows_summary_and_limited_examples():
    summary = _build_language_summary_model(
        [_notification_doc(index, "RU") for index in range(11)],
        examples_per_language=10,
    )

    html = _build_language_summary_html(summary)

    assert "Language summary" in html
    assert "examples shown" in html
    assert "Language: RU (examples: 10 of 11)" in html
    assert "notification-RU-9" in html
    assert "notification-RU-10" not in html


def test_build_pass_criteria_text_describes_success_parameters():
    text = _build_pass_criteria_text()

    assert "Pass criteria" in text
    assert f"Description: {WELCOME_PUSH_DESCRIPTION}" in text
    assert f"Title: {WELCOME_PUSH_TITLE}" in text
    assert f"Text: {WELCOME_PUSH_TEXT}" in text
    assert "Expected recipients: first-time subscribers with subscriptions longer than 1 day" in text
    assert "Excluded recipients: users with one-day subscriptions" in text
    assert "Purchase age: 7 to 14 days before push send time" in text
    assert "Club entries: no entries after purchase" in text
    assert "Missing IDs: 0" in text
    assert "Extra IDs: 0" in text


def test_build_recipient_mismatch_html_shows_two_user_diagnostics_tables():
    missing_rows = [
        {
            "user_id": "user-1",
            "subscriptions_count": "2 (one-day: 1)",
            "last_subscription_created_at": "2026-04-20 10:15:00",
            "last_entry_time": "2026-04-21 08:30:00",
        }
    ]
    extra_rows = [
        {
            "user_id": "user-2",
            "subscriptions_count": 3,
            "last_subscription_created_at": "2026-04-19 12:00:00",
            "last_entry_time": "-",
        }
    ]

    html = _build_recipient_mismatch_html(missing_rows, extra_rows)

    assert "Recipient mismatch details" in html
    assert "Missing IDs" in html
    assert "Extra IDs" in html
    assert html.count("<details") == 2
    assert html.count("<summary>") == 2
    assert "<summary>Missing IDs (1)</summary>" in html
    assert "<summary>Extra IDs (1)</summary>" in html
    assert html.count("<table>") == 2
    assert "userid" in html
    assert "всего абонементов" in html
    assert "дата приобретения последнего абонемента" in html
    assert "time последнего входа на момент отправки пуш" in html
    assert "user-1" in html
    assert "user-2" in html
    assert "2 (one-day: 1)" in html
    assert "2026-04-20 10:15:00" in html
    assert "2026-04-21 08:30:00" in html


def test_build_recipient_mismatch_html_shows_empty_state_in_both_tables():
    html = _build_recipient_mismatch_html([], [])

    assert "Missing IDs" in html
    assert "Extra IDs" in html
    assert html.count("<details") == 2
    assert html.count("<summary>") == 2
    assert html.count("<table>") == 2
    assert html.count("Нет пользователей для отображения") == 2


def test_build_user_diagnostic_rows_marks_one_day_subscriptions():
    user_id = "69e2400bc97246767e9993e2"
    start = datetime(2026, 4, 20, 10, 0, 0)
    db = _FakeDb(
        subscriptions=[
            {
                "user": user_id,
                "created_at": start,
                "startDate": start,
                "endDate": start + timedelta(days=1),
                "isDeleted": False,
            }
        ],
        entries=[],
    )

    rows = _build_user_diagnostic_rows(db, [user_id])

    assert rows == [
        {
            "user_id": user_id,
            "subscriptions_count": "1 (one-day: 1)",
            "last_subscription_created_at": "2026-04-20 10:00:00",
            "last_entry_time": "-",
        }
    ]


def test_filter_users_by_purchase_age_keeps_only_subscriptions_from_7_to_14_days():
    young_user_id = "65c0a2f75e80160110161ac0"
    eligible_user_id = "621390d9a26797525a3b8754"
    old_user_id = "62710e410037b12c8bdd6a1c"
    push_created_at = datetime(2026, 4, 19, 3, 0, 0)
    db = _FakeDb(
        subscriptions=[
            {
                "user": young_user_id,
                "created_at": datetime(2026, 4, 17, 13, 10, 13),
                "isDeleted": False,
            },
            {
                "user": eligible_user_id,
                "created_at": datetime(2026, 4, 12, 2, 59, 59),
                "isDeleted": False,
            },
            {
                "user": old_user_id,
                "created_at": datetime(2026, 4, 4, 2, 59, 59),
                "isDeleted": False,
            },
        ],
        entries=[],
    )
    users = [{"_id": young_user_id}, {"_id": eligible_user_id}, {"_id": old_user_id}]

    filtered_users = _filter_users_by_purchase_age(
        db,
        users,
        push_created_at,
        min_days_after_purchase=7,
        max_days_after_purchase=14,
    )

    assert filtered_users == [{"_id": eligible_user_id}]
