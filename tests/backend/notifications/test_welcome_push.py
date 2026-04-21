import allure
import re
from datetime import datetime, timedelta

import pytest_check as check
from bson import ObjectId

from src.repositories.notifications_repository import _build_regex_condition, get_user_ids_with_welcome_message
from src.utils.allure_html import HTML_CSS, html_kv, html_table
from src.validators.push_notifications.base import validate_push_field
from src.validators.push_notifications.welcome_push_validator import get_welcome_push_recipients


WELCOME_PUSH_DESCRIPTION = "Купил первый абонемент, но не приходит в клуб 1 неделю [RU]"
WELCOME_PUSH_TITLE = "{{name}}, добро пожаловать в Invictus 🏃"
WELCOME_PUSH_TEXT = "Здесь мы добьемся результата вместе. Ждем на тренировках."


def _format_dt(value):
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _extract_notification_language(description):
    if not description:
        return "UNKNOWN"
    if "[" in description and "]" in description:
        return description.rsplit("[", 1)[-1].split("]", 1)[0].upper()
    return "UNKNOWN"


def _build_multilanguage_description_pattern(description):
    base_description = re.sub(r"\s*\[[A-Z]{2}\]\s*$", "", description).strip()
    return f"regex:{base_description}(\\s\\[[A-Z]{{2}}\\])?"


def _get_welcome_push_docs(db, days=7):
    since = datetime.now() - timedelta(days=days)
    query = {
        "created_at": {"$gte": since},
        "description": _build_regex_condition(_build_multilanguage_description_pattern(WELCOME_PUSH_DESCRIPTION)),
    }
    projection = {
        "_id": 1,
        "created_at": 1,
        "description": 1,
        "title": 1,
        "text": 1,
        "toUsers": 1,
    }
    return list(db["notifications"].find(query, projection).sort("created_at", -1))


def _build_language_summary_model(docs, examples_per_language=10):
    summary = {}
    for doc in docs:
        language = _extract_notification_language(doc.get("description"))
        language_summary = summary.setdefault(
            language,
            {
                "docs": 0,
                "recipients": 0,
                "examples": [],
            },
        )
        language_summary["docs"] += 1
        language_summary["recipients"] += len(doc.get("toUsers") or [])
        if len(language_summary["examples"]) < examples_per_language:
            language_summary["examples"].append(
                {
                    "notification_id": str(doc.get("_id") or "-"),
                    "created_at": _format_dt(doc.get("created_at")),
                    "description": doc.get("description") or "-",
                    "title": doc.get("title") or "-",
                    "text": doc.get("text") or "-",
                    "recipients": len(doc.get("toUsers") or []),
                }
            )
    return summary


def _build_language_summary_html(language_summary):
    sections = ["<!DOCTYPE html><html><head><meta charset='utf-8'>", HTML_CSS, "</head><body>"]
    sections.append("<h2>Language summary</h2>")

    summary_rows = []
    for language, stats in sorted(language_summary.items()):
        summary_rows.append(
            [
                language,
                stats["docs"],
                stats["recipients"],
                len(stats["examples"]),
            ]
        )
    sections.append(
        html_table(
            ["language", "matching docs in period", "recipients in period", "examples shown"],
            summary_rows,
            right_cols=(1, 2, 3),
        )
    )

    example_headers = ["notificationId", "created_at", "description", "title", "text", "recipients"]
    for language, stats in sorted(language_summary.items()):
        sections.append(
            f"<h2>Language: {language} (examples: {len(stats['examples'])} of {stats['docs']})</h2>"
        )
        rows = [
            [
                example["notification_id"],
                example["created_at"],
                example["description"],
                example["title"],
                example["text"],
                example["recipients"],
            ]
            for example in stats["examples"]
        ]
        sections.append(html_table(example_headers, rows, right_cols=(5,)))

    sections.append("</body></html>")
    return "".join(sections)


def _build_summary_text(push_id, created_at, actual_title, actual_text, recipients_count) -> str:
    return "\n".join(
        [
            "Period: last 7 days",
            f"Push ID: {push_id or '-'}",
            f"Push sent at: {created_at or '-'}",
            f"Push description: {WELCOME_PUSH_DESCRIPTION}",
            f"Push title: {actual_title or '-'}",
            f"Push text: {actual_text or '-'}",
            f"Recipients in push: {recipients_count}",
            "Rule note: Extra IDs may include users who did not visit after the latest purchase,",
            "but still do not match this test because they had subscriptions before the current 7-day window.",
        ]
    )


def _build_pass_criteria_text() -> str:
    return "\n".join(
        [
            "Pass criteria",
            f"Description: {WELCOME_PUSH_DESCRIPTION}",
            f"Title: {WELCOME_PUSH_TITLE}",
            f"Text: {WELCOME_PUSH_TEXT}",
            "Expected recipients: first-time subscribers with subscriptions longer than 1 day",
            "Excluded recipients: users with one-day subscriptions",
            "Purchase age: 7 to 14 days before push send time",
            "Club entries: no entries after purchase",
            "Recipient comparison: actual push recipients must match expected recipients",
            "Missing IDs: 0",
            "Extra IDs: 0",
        ]
    )


def _to_mongo_user_id(value):
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except Exception:
        return value


def _filter_users_by_purchase_age(db, users, push_created_at, min_days_after_purchase=7, max_days_after_purchase=14):
    user_ids = [user["_id"] for user in users]
    if not user_ids:
        return []

    latest_allowed_purchase = push_created_at - timedelta(days=min_days_after_purchase)
    earliest_allowed_purchase = push_created_at - timedelta(days=max_days_after_purchase)
    mongo_user_ids = [_to_mongo_user_id(user_id) for user_id in user_ids]
    subscriptions = list(
        db["usersubscriptions"].find(
            {
                "user": {"$in": mongo_user_ids},
                "isDeleted": False,
            },
            {"user": 1, "created_at": 1},
        )
    )

    latest_subscription_by_user = {}
    for subscription in subscriptions:
        user_id = str(subscription.get("user"))
        created_at = subscription.get("created_at")
        if not created_at:
            continue
        if user_id not in latest_subscription_by_user or created_at > latest_subscription_by_user[user_id]:
            latest_subscription_by_user[user_id] = created_at

    return [
        user
        for user in users
        if latest_subscription_by_user.get(str(user["_id"])) is not None
        and earliest_allowed_purchase <= latest_subscription_by_user[str(user["_id"])] <= latest_allowed_purchase
    ]


def _build_user_diagnostic_rows(db, user_ids):
    rows = []
    sorted_user_ids = sorted(str(user_id) for user_id in user_ids)
    if not sorted_user_ids:
        return rows

    mongo_user_ids = [_to_mongo_user_id(user_id) for user_id in sorted_user_ids]
    subscriptions = list(
        db["usersubscriptions"].find(
            {
                "user": {"$in": mongo_user_ids},
                "isDeleted": False,
            },
            {"user": 1, "created_at": 1, "startDate": 1, "endDate": 1},
        )
    )
    entries = list(
        db["accesscontrols"].find(
            {"user": {"$in": mongo_user_ids}},
            {"user": 1, "time": 1},
        )
    )

    subscriptions_by_user = {
        user_id: {"count": 0, "one_day_count": 0, "latest_created_at": None}
        for user_id in sorted_user_ids
    }
    for subscription in subscriptions:
        user_id = str(subscription.get("user"))
        if user_id not in subscriptions_by_user:
            continue
        subscriptions_by_user[user_id]["count"] += 1
        start_date = subscription.get("startDate")
        end_date = subscription.get("endDate")
        if start_date and end_date and (end_date - start_date) <= timedelta(days=1):
            subscriptions_by_user[user_id]["one_day_count"] += 1
        created_at = subscription.get("created_at")
        latest_created_at = subscriptions_by_user[user_id]["latest_created_at"]
        if created_at and (latest_created_at is None or created_at > latest_created_at):
            subscriptions_by_user[user_id]["latest_created_at"] = created_at

    last_entries_by_user = {user_id: None for user_id in sorted_user_ids}
    for entry in entries:
        user_id = str(entry.get("user"))
        if user_id not in last_entries_by_user:
            continue
        entry_time = entry.get("time")
        if entry_time and (last_entries_by_user[user_id] is None or entry_time > last_entries_by_user[user_id]):
            last_entries_by_user[user_id] = entry_time

    for user_id in sorted_user_ids:
        subscription_stats = subscriptions_by_user[user_id]
        subscriptions_count = str(subscription_stats["count"])
        if subscription_stats["one_day_count"]:
            subscriptions_count = f"{subscriptions_count} (one-day: {subscription_stats['one_day_count']})"
        rows.append(
            {
                "user_id": user_id,
                "subscriptions_count": subscriptions_count,
                "last_subscription_created_at": _format_dt(subscription_stats["latest_created_at"]),
                "last_entry_time": _format_dt(last_entries_by_user[user_id]),
            }
        )

    return rows


def _recipient_table_rows(rows):
    if not rows:
        return [["Нет пользователей для отображения", "-", "-", "-"]]
    return [
        [
            row["user_id"],
            row["subscriptions_count"],
            row["last_subscription_created_at"],
            row["last_entry_time"],
        ]
        for row in rows
    ]


def _build_recipient_mismatch_html(missing_rows, extra_rows):
    headers = [
        "userid",
        "всего абонементов",
        "дата приобретения последнего абонемента",
        "time последнего входа на момент отправки пуш",
    ]
    sections = ["<!DOCTYPE html><html><head><meta charset='utf-8'>", HTML_CSS, "</head><body>"]
    sections.append("<h2>Recipient mismatch details</h2>")
    sections.append(f"<details><summary>Missing IDs ({len(missing_rows)})</summary>")
    sections.append(html_table(headers, _recipient_table_rows(missing_rows), right_cols=(1,)))
    sections.append("</details>")
    sections.append(f"<details><summary>Extra IDs ({len(extra_rows)})</summary>")
    sections.append(html_table(headers, _recipient_table_rows(extra_rows), right_cols=(1,)))
    sections.append("</details>")
    sections.append("</body></html>")
    return "".join(sections)


def _build_summary_html(push_id, created_at, actual_title, actual_text, recipients_count) -> str:
    return HTML_CSS + "<h2>Summary</h2>" + html_kv(
        [
            ("Period", "last 7 days"),
            ("Push ID", push_id or "-"),
            ("Push sent at", created_at or "-"),
            ("Push description", WELCOME_PUSH_DESCRIPTION),
            ("Push title", actual_title or "-"),
            ("Push text", actual_text or "-"),
            ("Recipients in push", recipients_count),
            ("Rule note", "Extra IDs may include users with no visits after the latest purchase if this is not their first subscription"),
        ]
    )


@allure.feature("Push Notifications")
@allure.story("Welcome Push")
@allure.title('Проверка пуша "Добро пожаловать"')
@allure.description("Проверяет пуш для новых пользователей без входов в клуб неделю после покупки")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "notifications", "mongodb")
@allure.link(name="MongoDB Query", url="mongodb://localhost:27017")
def test_welcome_push_with_new_subscriptions(db):
    """
    Проверяет пуш "Добро пожаловать":
    - Заголовок и текст соответствуют шаблону;
    - Пользователи действительно купили абонемент впервые;
    - Количество получателей совпадает с количеством ожидаемых получателей.
    """
    with allure.step("Определить welcome push за период и приложить summary"):
        print("\n=== TEST: Welcome Push ===")
        allure.attach(
            "ENVIRONMENT: PROD\nTEST: Welcome Push Validation",
            name="Test Configuration",
            attachment_type=allure.attachment_type.TEXT,
        )
        push_user_ids, created_at, actual_title, actual_text = get_user_ids_with_welcome_message(
            db=db,
            description=WELCOME_PUSH_DESCRIPTION,
            title=WELCOME_PUSH_TITLE,
            text=WELCOME_PUSH_TEXT,
            days=7,
            limit=1,
        )
        push_doc = db["notifications"].find_one(
            {
                "created_at": created_at,
                "description": _build_regex_condition(WELCOME_PUSH_DESCRIPTION),
                "title": _build_regex_condition(WELCOME_PUSH_TITLE),
                "text": _build_regex_condition(WELCOME_PUSH_TEXT),
            },
            {"_id": 1},
            sort=[("created_at", -1)],
        ) if created_at else None
        push_id = str(push_doc["_id"]) if push_doc else "-"
        welcome_docs = _get_welcome_push_docs(db=db, days=7)
        language_summary = _build_language_summary_model(welcome_docs, examples_per_language=10)
        allure.dynamic.parameter("Push ID", push_id)
        allure.dynamic.parameter("Push sent at", str(created_at) if created_at else "-")
        allure.dynamic.parameter("Push title", actual_title or "-")
        allure.dynamic.parameter("Push recipients", len(push_user_ids))
        allure.attach(
            _build_pass_criteria_text(),
            name="Pass criteria",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            _build_summary_text(push_id, created_at, actual_title, actual_text, len(push_user_ids)),
            name="Summary",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            _build_summary_html(push_id, created_at, actual_title, actual_text, len(push_user_ids)),
            name="Summary (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )
        allure.attach(
            _build_language_summary_html(language_summary),
            name="Language summary",
            attachment_type=allure.attachment_type.HTML,
        )

    with allure.step("Проверить содержимое welcome push и соответствие получателей бизнес-правилу"):
        if not created_at:
            check.is_true(False, "Welcome push не найден за последние 7 дней")
            assert False, "Welcome push не найден за последние 7 дней"

        title_ok = validate_push_field("title", actual_title or "", WELCOME_PUSH_TITLE)
        text_ok = validate_push_field("text", actual_text or "", WELCOME_PUSH_TEXT)
        expected_users_before_age_filter = get_welcome_push_recipients(db, created_at)
        expected_users = _filter_users_by_purchase_age(
            db,
            expected_users_before_age_filter,
            created_at,
            min_days_after_purchase=7,
            max_days_after_purchase=14,
        )
        expected_user_ids = {str(user["_id"]) for user in expected_users}
        actual_user_ids = {str(user_id) for user_id in push_user_ids}
        missing_ids = sorted(expected_user_ids - actual_user_ids)
        extra_ids = sorted(actual_user_ids - expected_user_ids)
        missing_rows = _build_user_diagnostic_rows(db, missing_ids)
        extra_rows = _build_user_diagnostic_rows(db, extra_ids)

        allure.dynamic.parameter("Expected recipients before purchase age filter", len(expected_users_before_age_filter))
        allure.dynamic.parameter("Expected recipients", len(expected_user_ids))
        allure.dynamic.parameter("Missing IDs", len(missing_ids))
        allure.dynamic.parameter("Extra IDs", len(extra_ids))
        allure.attach(
            _build_recipient_mismatch_html(missing_rows, extra_rows),
            name="Recipient mismatch details",
            attachment_type=allure.attachment_type.HTML,
        )

        has_expected_users = bool(expected_users)
        recipients_ok = not missing_ids and not extra_ids
        result = title_ok and text_ok and has_expected_users and recipients_ok
        check.is_true(has_expected_users, "Не найдены ожидаемые получатели welcome push")
        check.is_true(
            recipients_ok,
            f"Несовпадения в получателях welcome push: missing={len(missing_ids)}, extra={len(extra_ids)}",
        )

        if not result:
            allure.attach(
                "1. Проверьте Summary: там указаны дата, description, title, text и количество получателей найденного пуша\n"
                "2. Сверьте Recipient mismatch details: там есть HTML-таблицы Missing IDs и Extra IDs\n"
                "3. Для Extra IDs сначала проверьте историю подписок: тест ждёт только первую подписку в жизни, а не просто отсутствие входов после последней покупки\n"
                "4. Найдите пользователей в MongoDB: db.users.find({_id: ObjectId('...')})\n"
                "5. Проверьте подписки: db.usersubscriptions.find({user: ObjectId('...')})\n"
                "6. Проверьте входы: db.accesscontrols.find({user: ObjectId('...')})",
                name="How to Debug",
                attachment_type=allure.attachment_type.TEXT,
            )

        assert result, "Push 'Добро пожаловать' не прошёл проверку"
