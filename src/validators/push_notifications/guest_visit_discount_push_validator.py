from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse

from src.repositories.notifications_repository import _build_regex_condition
from src.utils.allure_html import HTML_CSS, html_table
from src.validators.push_notifications.base import validate_push_field

try:
    import allure

    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False


GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION = "скидка в день гостевого визита"
GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION_PATTERN = r"regex:скидка в день гостевого визита(\s\[[A-Z]{2}\])?"
GUEST_VISIT_DISCOUNT_PUSH_TITLE = (
    "{{name}}, мы спрятали скидку на покупку абонемента",
    "{{name}}, we hid a discount on membership purchase",
)
GUEST_VISIT_DISCOUNT_PUSH_TEXT = (
    "скидка действует только сегодня",
    "Discount valid today only",
)
GUEST_VISIT_DISCOUNT_PUSH_DELAY_MINUTES = 30
GUEST_VISIT_DISCOUNT_PUSH_TOLERANCE_SECONDS = 60
CLUB_AWAYLINK_BY_KEY = {
    "gagarin_samal": "77007770720",
    "sadu": "77007777060",
    "highville": "77085356192",
    "green_mall": "77074646468",
    "atyrau": "77005000110",
    "akbulak_riviera": "77056467777",
    "oral": "77010841217",
    "temirtau": "77054448800",
    "nursat_alfarabi": "77077702552",
    "semey": "77470941998",
}


def _format_dt(value):
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


def _format_away_link(value):
    if not value:
        return "-"

    try:
        parsed = urlparse(value)
        query = parse_qs(parsed.query)
        text_value = query.get("text", [None])[0]
        if text_value:
            decoded_text = unquote(text_value)
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path} | text={decoded_text}"
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    except Exception:
        return str(value)


def _extract_awaylink_phone(value):
    if not value:
        return None

    parsed = urlparse(value)
    path = (parsed.path or "").strip("/")
    digits = "".join(ch for ch in path if ch.isdigit())
    return digits or None


def _resolve_club_awaylink_key(club_name):
    if not club_name:
        return None

    normalized = club_name.lower()
    if "green mall" in normalized:
        return "green_mall"
    if "akbulak" in normalized and "riviera" in normalized:
        return "akbulak_riviera"
    if "highvill" in normalized:
        return "highville"
    if "temirtau" in normalized:
        return "temirtau"
    if "atyrau" in normalized:
        return "atyrau"
    if "sadu" in normalized:
        return "sadu"
    if "semey" in normalized:
        return "semey"
    if "oral" in normalized:
        return "oral"
    if "gagarin" in normalized or "samal" in normalized:
        return "gagarin_samal"
    if "nursat" in normalized or "al-farabi" in normalized or "alfarabi" in normalized:
        return "nursat_alfarabi"
    return None


def _entry_club_matches_active_subscription_club(entry_club_id, active_subscription_club_ids):
    if not entry_club_id:
        return False
    normalized_ids = {str(club_id) for club_id in active_subscription_club_ids if club_id}
    return str(entry_club_id) in normalized_ids


def _extract_notification_language(description):
    if not description:
        return "UNKNOWN"
    if "[" in description and "]" in description:
        return description.rsplit("[", 1)[-1].split("]", 1)[0].upper()
    return "UNKNOWN"


def _build_notification_row(
    notification_id,
    language,
    created_at,
    user_id,
    away_link,
    last_entry_time,
    last_entry_club_id,
    last_entry_club_name,
    active_subscription_ids,
    active_subscription_club_names,
):
    return [
        str(notification_id),
        language,
        _format_dt(created_at),
        str(user_id),
        _format_away_link(away_link),
        _format_dt(last_entry_time),
        str(last_entry_club_id) if last_entry_club_id else "-",
        last_entry_club_name or "-",
        ", ".join(str(subscription_id) for subscription_id in active_subscription_ids) or "-",
        ", ".join(active_subscription_club_names) or "-",
    ]


def _summarize_notification_docs_by_language(docs):
    summary = {}
    total_recipients = 0

    for doc in docs:
        language = _extract_notification_language(doc.get("description"))
        recipients_count = len(doc.get("toUsers") or [])
        language_summary = summary.setdefault(language, {"docs": 0, "recipients": 0})
        language_summary["docs"] += 1
        language_summary["recipients"] += recipients_count
        total_recipients += recipients_count

    return {
        "docs": len(docs),
        "recipients": total_recipients,
        "languages": summary,
    }


def _build_notifications_tables_html(rows_by_language):
    sections = []
    headers = [
        'notificationId',
        'language',
        'created_at notification',
        'userId',
        'awaylink',
        'last successful entry time',
        'clubId',
        'clubName',
        'active userSubscriptionIds',
        'active userSubscriptionClubNames',
    ]
    for language, rows in sorted(rows_by_language.items()):
        sections.append(f"<h2>Language: {language} ({len(rows)})</h2>")
        sections.append(html_table(headers, rows))
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"{HTML_CSS}</head><body>{''.join(sections)}</body></html>"
    )


def _build_notifications_tables_html_with_stats(rows_by_language, language_stats):
    sections = []
    if language_stats:
        summary_headers = ["language", "matching docs in period", "recipients in period", "detailed rows checked"]
        summary_rows = []
        all_languages = sorted(set(language_stats) | set(rows_by_language))
        for language in all_languages:
            stats = language_stats.get(language, {})
            summary_rows.append(
                [
                    language,
                    stats.get("docs", 0),
                    stats.get("recipients", 0),
                    len(rows_by_language.get(language, [])),
                ]
            )
        sections.append("<h2>Language summary</h2>")
        sections.append(html_table(summary_headers, summary_rows, right_cols=(1, 2, 3)))

    headers = [
        'notificationId',
        'language',
        'created_at notification',
        'userId',
        'awaylink',
        'last successful entry time',
        'clubId',
        'clubName',
        'active userSubscriptionIds',
        'active userSubscriptionClubNames',
    ]
    for language, rows in sorted(rows_by_language.items()):
        stats = language_stats.get(language, {})
        docs_count = stats.get("docs")
        recipients_count = stats.get("recipients")
        if docs_count is not None:
            sections.append(
                f"<h2>Language: {language} "
                f"(checked rows: {len(rows)}, matching docs: {docs_count}, recipients in period: {recipients_count})</h2>"
            )
        else:
            sections.append(f"<h2>Language: {language} (checked rows: {len(rows)})</h2>")
        sections.append(html_table(headers, rows))
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"{HTML_CSS}</head><body>{''.join(sections)}</body></html>"
    )


def get_guest_visit_discount_push_docs(db, days=7, limit=20):
    """Возвращает последние notification-документы этого push за период."""
    since = datetime.now() - timedelta(days=days)
    query = {
        "created_at": {"$gte": since},
        "description": _build_regex_condition(GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION),
    }
    projection = {
        "_id": 1,
        "created_at": 1,
        "description": 1,
        "title": 1,
        "text": 1,
        "toUsers": 1,
        "awayLink": 1,
    }
    return list(db["notifications"].find(query, projection).sort("created_at", -1).limit(limit))


def get_guest_visit_discount_push_doc_stats(db, days=7):
    """Возвращает статистику по всем notification-документам push за период без limit."""
    since = datetime.now() - timedelta(days=days)
    query = {
        "created_at": {"$gte": since},
        "description": _build_regex_condition(GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION),
    }
    projection = {
        "_id": 1,
        "description": 1,
        "toUsers": 1,
    }
    docs = list(db["notifications"].find(query, projection))
    return _summarize_notification_docs_by_language(docs)


def _find_qualifying_guest_visit_entry(
    db,
    user_id,
    notification_time,
    delay_minutes=GUEST_VISIT_DISCOUNT_PUSH_DELAY_MINUTES,
    tolerance_seconds=GUEST_VISIT_DISCOUNT_PUSH_TOLERANCE_SECONDS,
):
    target_time = notification_time - timedelta(minutes=delay_minutes)
    window_start = target_time - timedelta(seconds=tolerance_seconds)
    window_end = target_time + timedelta(seconds=tolerance_seconds)

    return db["accesscontrols"].find_one(
        {
            "user": user_id,
            "type": "enter",
            "accessType": "visits",
            "err": {"$exists": False},
            "time": {"$gte": window_start, "$lte": window_end},
        },
        {"_id": 1, "time": 1, "club": 1},
        sort=[("time", -1)],
    )


def check_guest_visit_discount_push(db, days=7, limit=20):
    """
    Проверяет, что notification с description "скидка в день гостевого визита"
    создаётся для пользователя примерно через 30 минут после входа по гостевому визиту.
    """
    print("\n=== CHECK: Guest Visit Discount Push ===")
    docs = get_guest_visit_discount_push_docs(db=db, days=days, limit=limit)
    doc_stats = get_guest_visit_discount_push_doc_stats(db=db, days=days)

    if not docs:
        print("[WARNING] Push не найден.")
        return False

    print(f"[INFO] Найдено notification docs: {len(docs)}")

    print(f"[INFO] Matching docs in period: {doc_stats['docs']}")

    violations = []
    checked_recipients = 0
    rows_by_language = {}
    club_ids = set()
    user_ids = set()
    entries_by_notification_user = {}

    for doc in docs:
        validate_push_field(
            "description",
            doc.get("description") or "",
            (
                GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION_PATTERN,
                GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION_PATTERN,
            ),
        )
        validate_push_field("title", doc.get("title") or "", GUEST_VISIT_DISCOUNT_PUSH_TITLE)
        validate_push_field("text", doc.get("text") or "", GUEST_VISIT_DISCOUNT_PUSH_TEXT)

        for user_id in doc.get("toUsers") or []:
            checked_recipients += 1
            user_ids.add(user_id)
            entry = _find_qualifying_guest_visit_entry(
                db=db,
                user_id=user_id,
                notification_time=doc["created_at"],
            )
            entries_by_notification_user[(str(doc["_id"]), str(user_id))] = entry
            if entry and entry.get("club"):
                club_ids.add(entry["club"])
            if entry is None:
                violations.append(
                    {
                        "notification_id": str(doc["_id"]),
                        "notification_time": str(doc["created_at"]),
                        "user_id": str(user_id),
                        "expected_guest_visit_time": str(
                            doc["created_at"] - timedelta(minutes=GUEST_VISIT_DISCOUNT_PUSH_DELAY_MINUTES)
                        ),
                    }
                )

    print(f"[INFO] Проверено получателей: {checked_recipients}")
    print(f"[INFO] Нарушений: {len(violations)}")

    clubs_by_id = {
        club["_id"]: club
        for club in db["clubs"].find({"_id": {"$in": list(club_ids)}}, {"_id": 1, "name": 1, "title": 1})
    } if club_ids else {}
    active_subscriptions_by_user = {}
    if user_ids:
        active_subscriptions = list(
            db["usersubscriptions"].find(
                {
                    "user": {"$in": list(user_ids)},
                    "isActive": True,
                    "isDeleted": False,
                },
                {"_id": 1, "user": 1, "clubId": 1},
            )
        )
        for subscription in active_subscriptions:
            user_id = subscription.get("user")
            club_id = subscription.get("clubId")
            if club_id:
                club_ids.add(club_id)
            if user_id not in active_subscriptions_by_user:
                active_subscriptions_by_user[user_id] = []
            active_subscriptions_by_user[user_id].append(subscription)

    if club_ids:
        clubs_by_id.update(
            {
                club["_id"]: club
                for club in db["clubs"].find({"_id": {"$in": list(club_ids)}}, {"_id": 1, "name": 1, "title": 1})
            }
        )

    for doc in docs:
        away_link = doc.get("awayLink")
        language = _extract_notification_language(doc.get("description"))
        for user_id in doc.get("toUsers") or []:
            entry = entries_by_notification_user.get((str(doc["_id"]), str(user_id)))
            club_id = entry.get("club") if entry else None
            club_doc = clubs_by_id.get(club_id, {}) if club_id else {}
            club_name = club_doc.get("name") or club_doc.get("title")
            club_key = _resolve_club_awaylink_key(club_name)
            expected_phone = CLUB_AWAYLINK_BY_KEY.get(club_key)
            actual_phone = _extract_awaylink_phone(away_link)
            if entry is not None and expected_phone and actual_phone != expected_phone:
                violations.append(
                    {
                        "notification_id": str(doc["_id"]),
                        "notification_time": str(doc["created_at"]),
                        "user_id": str(user_id),
                        "club_name": club_name,
                        "expected_awaylink_phone": expected_phone,
                        "actual_awaylink_phone": actual_phone,
                    }
                )
            active_subscriptions = active_subscriptions_by_user.get(user_id, [])
            active_subscription_club_ids = [subscription.get("clubId") for subscription in active_subscriptions]
            if entry is not None and _entry_club_matches_active_subscription_club(club_id, active_subscription_club_ids):
                violations.append(
                    {
                        "notification_id": str(doc["_id"]),
                        "notification_time": str(doc["created_at"]),
                        "user_id": str(user_id),
                        "entry_club_id": str(club_id),
                        "active_subscription_club_ids": [
                            str(subscription_club_id)
                            for subscription_club_id in active_subscription_club_ids
                            if subscription_club_id
                        ],
                    }
                )
            active_subscription_ids = [str(subscription.get("_id")) for subscription in active_subscriptions if subscription.get("_id")]
            active_subscription_club_names = []
            for subscription in active_subscriptions:
                subscription_club_id = subscription.get("clubId")
                if not subscription_club_id:
                    continue
                subscription_club_doc = clubs_by_id.get(subscription_club_id, {})
                active_subscription_club_names.append(
                    subscription_club_doc.get("name") or subscription_club_doc.get("title") or str(subscription_club_id)
                )
            rows_by_language.setdefault(language, []).append(
                _build_notification_row(
                    notification_id=doc["_id"],
                    language=language,
                    created_at=doc.get("created_at"),
                    user_id=user_id,
                    away_link=away_link,
                    last_entry_time=entry.get("time") if entry else None,
                    last_entry_club_id=club_id,
                    last_entry_club_name=club_name,
                    active_subscription_ids=active_subscription_ids,
                    active_subscription_club_names=active_subscription_club_names,
                )
            )

    if ALLURE_AVAILABLE:
        allure.attach(
            _build_notifications_tables_html_with_stats(
                rows_by_language=rows_by_language,
                language_stats=doc_stats["languages"],
            ),
            name="Guest visit discount notifications",
            attachment_type=allure.attachment_type.HTML,
        )

    return len(violations) == 0
