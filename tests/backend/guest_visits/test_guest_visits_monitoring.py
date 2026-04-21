"""Monitoring for clients with source=user guest visits."""

from datetime import datetime

import allure
import pytest

from src.utils.allure_html import HTML_CSS, html_table


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _build_clients_with_guest_visits_html(
    used_rows: list[list[object]],
    unused_rows: list[list[object]],
) -> str:
    headers = [
        "User ID",
        "Role",
        "Used isActive=false",
        "Unused isActive=true",
        "Total source=user",
        "Latest visit at",
        "Last successful entry",
        "Latest userSubscription ID",
        "Subscription endDate",
    ]
    used_table = html_table(headers, used_rows, right_cols=(2, 3, 4))
    unused_table = html_table(headers, unused_rows, right_cols=(2, 3, 4))
    body = (
        "<h2>Guest visits by clients</h2>"
        "<details class='collapsible' open>"
        "<summary>Top clients by used guest visits</summary>"
        f"<div class='collapsible-body'>{used_table}</div>"
        "</details>"
        "<details class='collapsible'>"
        "<summary>Top clients by unused guest visits</summary>"
        f"<div class='collapsible-body'>{unused_table}</div>"
        "</details>"
    )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"{HTML_CSS}</head><body>{body}</body></html>"
    )


def _limit_top_client_rows(rows: list[list[object]], limit: int = 25) -> list[list[object]]:
    return rows[:limit]


def _build_client_row(
    user_id: str,
    role: str,
    used_count: int,
    unused_count: int,
    latest_visit_at: str,
    last_successful_entry: str,
    subscription_id: str,
    subscription_end_date: str,
) -> list[object]:
    return [
        user_id,
        role,
        used_count,
        unused_count,
        used_count + unused_count,
        latest_visit_at,
        last_successful_entry,
        subscription_id,
        subscription_end_date,
    ]


@pytest.mark.backend
@allure.feature("Guest Visits")
@allure.story("Guest Visits Monitoring")
@allure.title("РњРѕРЅРёС‚РѕСЂРёРЅРі РєР»РёРµРЅС‚РѕРІ СЃ РіРѕСЃС‚РµРІС‹РјРё РІРёР·РёС‚Р°РјРё source=user")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("backend", "guest-visits", "monitoring", "visits")
def test_guest_visits_monitoring(db):
    top_limit = 25

    with allure.step("РЎРѕР±СЂР°С‚СЊ С‚РѕРї РєР»РёРµРЅС‚РѕРІ РїРѕ visits source=user Р·Р° РІСЃС‘ РІСЂРµРјСЏ"):
        grouped_stats = list(
            db["visits"].aggregate(
                [
                    {"$match": {"source": "user", "user": {"$exists": True, "$ne": None}}},
                    {
                        "$group": {
                            "_id": "$user",
                            "used_count": {
                                "$sum": {"$cond": [{"$eq": ["$isActive", False]}, 1, 0]}
                            },
                            "unused_count": {
                                "$sum": {"$cond": [{"$eq": ["$isActive", True]}, 1, 0]}
                            },
                            "latest_visit_at": {"$max": "$created_at"},
                        }
                    },
                    {
                        "$match": {
                            "$or": [
                                {"used_count": {"$gt": 0}},
                                {"unused_count": {"$gt": 0}},
                            ]
                        }
                    },
                ],
                allowDiskUse=True,
            )
        )

    if not grouped_stats:
        pytest.skip("РќРµС‚ visits СЃ source=user")

    used_stats = sorted(
        [item for item in grouped_stats if item.get("used_count", 0) > 0],
        key=lambda item: (-item.get("used_count", 0), -item.get("unused_count", 0), str(item["_id"])),
    )[:top_limit]
    unused_stats = sorted(
        [item for item in grouped_stats if item.get("unused_count", 0) > 0],
        key=lambda item: (-item.get("unused_count", 0), -item.get("used_count", 0), str(item["_id"])),
    )[:top_limit]

    if not used_stats and not unused_stats:
        pytest.skip("РќРµС‚ РєР»РёРµРЅС‚РѕРІ СЃ visits source=user Рё isActive=false/isActive=true")

    top_user_ids = {
        item["_id"]
        for item in used_stats + unused_stats
        if item.get("_id") is not None
    }

    subscriptions_by_user: dict[object, dict[str, object]] = {}
    for subscription in db["usersubscriptions"].find(
        {"user": {"$in": list(top_user_ids)}},
        {"_id": 1, "user": 1, "created_at": 1, "endDate": 1},
    ).sort("created_at", -1):
        user_id = subscription.get("user")
        if user_id and user_id not in subscriptions_by_user:
            subscriptions_by_user[user_id] = subscription

    last_entries_by_user: dict[object, dict[str, object]] = {}
    for entry in db["accesscontrols"].find(
        {
            "user": {"$in": list(top_user_ids)},
            "type": "enter",
            "err": {"$exists": False},
        },
        {"_id": 1, "user": 1, "time": 1},
    ).sort("time", -1):
        user_id = entry.get("user")
        if user_id and user_id not in last_entries_by_user:
            last_entries_by_user[user_id] = entry

    users_by_id = {
        doc["_id"]: doc
        for doc in db["users"].find(
            {"_id": {"$in": list(top_user_ids)}},
            {"_id": 1, "role": 1},
        )
    }

    def _rows_from_stats(stats: list[dict[str, object]]) -> list[list[object]]:
        rows: list[list[object]] = []
        for item in stats:
            user_id = item.get("_id")
            if user_id is None:
                continue

            subscription = subscriptions_by_user.get(user_id) or {}
            last_entry = last_entries_by_user.get(user_id) or {}
            rows.append(
                _build_client_row(
                    user_id=str(user_id),
                    role=users_by_id.get(user_id, {}).get("role") or "-",
                    used_count=int(item.get("used_count") or 0),
                    unused_count=int(item.get("unused_count") or 0),
                    latest_visit_at=_fmt_dt(item.get("latest_visit_at")),
                    last_successful_entry=_fmt_dt(last_entry.get("time")),
                    subscription_id=str(subscription.get("_id")) if subscription.get("_id") else "-",
                    subscription_end_date=_fmt_dt(subscription.get("endDate")),
                )
            )
        return rows

    used_rows = _limit_top_client_rows(_rows_from_stats(used_stats))
    unused_rows = _limit_top_client_rows(_rows_from_stats(unused_stats))

    if not used_rows and not unused_rows:
        pytest.skip("РќРµС‚ РєР»РёРµРЅС‚РѕРІ РґР»СЏ РѕС‚С‡С‘С‚Р° guest visits")

    with allure.step("РџСЂРёР»РѕР¶РёС‚СЊ РєР»РёРµРЅС‚РѕРІ СЃ guest visits"):
        allure.attach(
            _build_clients_with_guest_visits_html(
                used_rows=used_rows,
                unused_rows=unused_rows,
            ),
            name="Clients with guest visits",
            attachment_type=allure.attachment_type.HTML,
        )
