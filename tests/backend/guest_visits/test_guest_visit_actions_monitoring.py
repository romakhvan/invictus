"""
Monitoring for guest visit actions transfer/use consistency.
"""

from collections import Counter
from datetime import datetime, timedelta

import allure
import pytest

from src.utils.allure_html import HTML_CSS, html_kv, html_table


def _fmt_dt(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _build_summary_html(summary_pairs: list[tuple[str, object]]) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"{HTML_CSS}</head><body><h2>Summary</h2>{html_kv(summary_pairs)}</body></html>"
    )


def _build_table_html(headers: list[str], rows: list[list[object]], right_cols: tuple[int, ...] = ()) -> str:
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"{HTML_CSS}</head><body>{html_table(headers, rows, right_cols=right_cols)}</body></html>"
    )


def _build_full_name(user_doc: dict) -> str:
    full_name = " ".join(
        part
        for part in [
            user_doc.get("lastName"),
            user_doc.get("firstName"),
            user_doc.get("middleName"),
        ]
        if part
    ).strip()
    return full_name or user_doc.get("fullName") or user_doc.get("name") or "-"


def _build_user_totals_rows(counter: Counter, actions_counter: Counter, users_by_id: dict) -> list[list[object]]:
    rows: list[list[object]] = []
    for user_id, visits_count in sorted(counter.items(), key=lambda item: (-item[1], str(item[0]))):
        user_doc = users_by_id.get(user_id, {})
        rows.append(
            [
                str(user_id),
                _build_full_name(user_doc),
                user_doc.get("role") or "-",
                visits_count,
                actions_counter[user_id],
            ]
        )
    return rows


def _build_user_totals_html(sent_rows: list[list[object]], received_rows: list[list[object]]) -> str:
    sent_table = html_table(
        ["User ID", "Р¤РРћ", "Role", "Visits sent", "Transfer actions"],
        sent_rows,
        right_cols=(3, 4),
    )
    received_table = html_table(
        ["User ID", "Р¤РРћ", "Role", "Visits received", "Transfer actions"],
        received_rows,
        right_cols=(3, 4),
    )
    body = (
        "<h2>Users guest visits totals</h2>"
        "<details class='collapsible' open>"
        "<summary>Users by sent visits</summary>"
        f"<div class='collapsible-body'>{sent_table}</div>"
        "</details>"
        "<details class='collapsible' open>"
        "<summary>Users by received visits</summary>"
        f"<div class='collapsible-body'>{received_table}</div>"
        "</details>"
    )
    return (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        f"{HTML_CSS}</head><body>{body}</body></html>"
    )


@allure.feature("Guest Visits")
@allure.story("Guest Visit Actions")
@allure.title("Monitoring РїРµСЂРµРґР°С‡Рё Рё РїРѕР»СѓС‡РµРЅРёСЏ РіРѕСЃС‚РµРІС‹С… userguestvisitactions")
@allure.description(
    "РџРѕРєР°Р·С‹РІР°РµС‚ РѕР±СЉС‘Рј guest visit actions Р·Р° РїРµСЂРёРѕРґ Рё РїСЂРѕРІРµСЂСЏРµС‚ С†РµР»РѕСЃС‚РЅРѕСЃС‚СЊ СЃРІСЏР·РµР№ "
    "РґР»СЏ РїРµСЂРµРґР°С‡Рё РіРѕСЃС‚РµРІРѕРіРѕ РІРёР·РёС‚Р° Рё РµРіРѕ РїРѕР»СѓС‡РµРЅРёСЏ."
)
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("backend", "guest-visits", "monitoring", "userguestvisitactions")
def test_guest_visit_actions_monitoring(db, period_days):
    since = datetime.now() - timedelta(days=period_days)
    projection = {
        "_id": 1,
        "created_at": 1,
        "type": 1,
        "source": 1,
        "sender": 1,
        "receiver": 1,
        "visit": 1,
        "senderUserSubscription": 1,
        "amount": 1,
    }

    with allure.step(f"РЎРѕР±СЂР°С‚СЊ userguestvisitactions Р·Р° РїРѕСЃР»РµРґРЅРёРµ {period_days} РґРЅРµР№"):
        actions = list(
            db["userguestvisitactions"].find(
                {"created_at": {"$gte": since}},
                projection,
            ).sort("created_at", -1)
        )

    if not actions:
        pytest.skip(f"Р—Р° РїРѕСЃР»РµРґРЅРёРµ {period_days} РґРЅРµР№ РЅРµС‚ userguestvisitactions")

    transfer_actions = [action for action in actions if action.get("type") == "TRANSFER"]
    use_actions = [action for action in actions if action.get("type") == "USE"]
    mobile_transfer_actions = [action for action in transfer_actions if action.get("source") == "MOBILE"]
    admin_transfer_actions = [action for action in transfer_actions if action.get("source") == "ADMIN"]

    visit_ids = [action["visit"] for action in transfer_actions if action.get("visit")]
    subscription_ids = [
        action["senderUserSubscription"]
        for action in transfer_actions
        if action.get("senderUserSubscription")
    ]

    visits_by_id = {
        doc["_id"]: doc
        for doc in db["visits"].find({"_id": {"$in": visit_ids}}, {"_id": 1, "user": 1, "type": 1, "source": 1})
    }
    subscriptions_by_id = {
        doc["_id"]: doc
        for doc in db["usersubscriptions"].find({"_id": {"$in": subscription_ids}}, {"_id": 1, "user": 1})
    }
    user_ids = {
        action.get("sender")
        for action in transfer_actions
        if action.get("sender")
    } | {
        action.get("receiver")
        for action in transfer_actions
        if action.get("receiver")
    }
    users_by_id = {
        doc["_id"]: doc
        for doc in db["users"].find(
            {"_id": {"$in": list(user_ids)}},
            {"_id": 1, "role": 1, "firstName": 1, "lastName": 1, "middleName": 1, "fullName": 1, "name": 1},
        )
    }

    transfer_source_stats = Counter(action.get("source") or "-" for action in transfer_actions)
    use_source_stats = Counter(action.get("source") or "-" for action in use_actions)
    action_type_stats = Counter(action.get("type") or "-" for action in actions)
    sent_visits_by_user: Counter = Counter()
    received_visits_by_user: Counter = Counter()
    sent_actions_by_user: Counter = Counter()
    received_actions_by_user: Counter = Counter()

    for action in transfer_actions:
        amount = action.get("amount") or 0
        sender = action.get("sender")
        receiver = action.get("receiver")
        if sender:
            sent_visits_by_user[sender] += amount
            sent_actions_by_user[sender] += 1
        if receiver:
            received_visits_by_user[receiver] += amount
            received_actions_by_user[receiver] += 1

    anomalies: list[dict[str, object]] = []
    monitoring_notes: list[dict[str, object]] = []

    for action in mobile_transfer_actions:
        action_id = str(action["_id"])
        visit_doc = visits_by_id.get(action.get("visit"))
        subscription_doc = subscriptions_by_id.get(action.get("senderUserSubscription"))

        if not action.get("sender"):
            anomalies.append(
                {
                    "kind": "transfer_missing_sender",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": "sender is empty",
                }
            )
        if not action.get("receiver"):
            anomalies.append(
                {
                    "kind": "transfer_missing_receiver",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": "receiver is empty",
                }
            )
        if not action.get("visit"):
            anomalies.append(
                {
                    "kind": "transfer_missing_visit",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": "visit is empty",
                }
            )
        elif visit_doc is None:
            anomalies.append(
                {
                    "kind": "transfer_visit_not_found",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"visit {action.get('visit')} not found",
                }
            )
        elif visit_doc.get("user") != action.get("receiver"):
            anomalies.append(
                {
                    "kind": "transfer_visit_receiver_mismatch",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"visit.user={visit_doc.get('user')} receiver={action.get('receiver')}",
                }
            )

        if not action.get("senderUserSubscription"):
            monitoring_notes.append(
                {
                    "kind": "transfer_missing_sender_subscription",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": "senderUserSubscription is empty",
                }
            )
        elif subscription_doc is None:
            monitoring_notes.append(
                {
                    "kind": "transfer_subscription_not_found",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"senderUserSubscription {action.get('senderUserSubscription')} not found",
                }
            )
        elif subscription_doc.get("user") != action.get("sender"):
            relation = "receiver" if subscription_doc.get("user") == action.get("receiver") else "other"
            monitoring_notes.append(
                {
                    "kind": "transfer_subscription_sender_mismatch",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": (
                        f"subscription.user={subscription_doc.get('user')} "
                        f"sender={action.get('sender')} relation={relation}"
                    ),
                }
            )

        if (action.get("amount") or 0) <= 0:
            anomalies.append(
                {
                    "kind": "transfer_non_positive_amount",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"amount={action.get('amount')}",
                }
            )

    for action in admin_transfer_actions:
        action_id = str(action["_id"])
        if action.get("receiver") is None and action.get("visit") is None:
            monitoring_notes.append(
                {
                    "kind": "admin_transfer_without_receiver_and_visit",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"sender={action.get('sender')}",
                }
            )
        if action.get("senderUserSubscription") is None:
            monitoring_notes.append(
                {
                    "kind": "admin_transfer_without_sender_subscription",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"sender={action.get('sender')}",
                }
            )

    for action in use_actions:
        action_id = str(action["_id"])

        if not action.get("receiver"):
            anomalies.append(
                {
                    "kind": "use_missing_receiver",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": "receiver is empty",
                }
            )
        if action.get("sender") is not None:
            anomalies.append(
                {
                    "kind": "use_unexpected_sender",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"sender={action.get('sender')}",
                }
            )
        if action.get("visit") is not None:
            anomalies.append(
                {
                    "kind": "use_unexpected_visit",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"visit={action.get('visit')}",
                }
            )
        if action.get("senderUserSubscription") is not None:
            anomalies.append(
                {
                    "kind": "use_unexpected_sender_subscription",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"senderUserSubscription={action.get('senderUserSubscription')}",
                }
            )
        if (action.get("amount") or 0) <= 0:
            anomalies.append(
                {
                    "kind": "use_non_positive_amount",
                    "action_id": action_id,
                    "created_at": _fmt_dt(action.get("created_at")),
                    "source": action.get("source") or "-",
                    "details": f"amount={action.get('amount')}",
                }
            )

    anomaly_stats = Counter(item["kind"] for item in anomalies)
    note_stats = Counter(item["kind"] for item in monitoring_notes)
    sent_rows = _build_user_totals_rows(sent_visits_by_user, sent_actions_by_user, users_by_id)
    received_rows = _build_user_totals_rows(received_visits_by_user, received_actions_by_user, users_by_id)
    summary_pairs = [
        ("Period", f"last {period_days} days"),
        ("Since", _fmt_dt(since)),
        ("Actions total", len(actions)),
        ("TRANSFER", len(transfer_actions)),
        ("TRANSFER MOBILE", len(mobile_transfer_actions)),
        ("TRANSFER ADMIN", len(admin_transfer_actions)),
        ("USE", len(use_actions)),
        ("Unique senders in TRANSFER", len({str(action.get('sender')) for action in transfer_actions if action.get('sender')})),
        ("Unique receivers", len({str(action.get('receiver')) for action in actions if action.get('receiver')})),
        ("Anomalies total", len(anomalies)),
        ("Monitoring notes", len(monitoring_notes)),
        ("Latest action at", _fmt_dt(actions[0].get("created_at"))),
        ("Oldest action at", _fmt_dt(actions[-1].get("created_at"))),
    ]

    with allure.step("РџСЂРёР»РѕР¶РёС‚СЊ summary Рё breakdown"):
        allure.dynamic.parameter("Р’СЃРµРіРѕ actions", len(actions))
        allure.dynamic.parameter("TRANSFER", len(transfer_actions))
        allure.dynamic.parameter("USE", len(use_actions))
        allure.dynamic.parameter("РђРЅРѕРјР°Р»РёР№", len(anomalies))
        allure.dynamic.parameter("Monitoring notes", len(monitoring_notes))
        allure.attach(
            "\n".join(f"{key}: {value}" for key, value in summary_pairs),
            name="Summary",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            _build_summary_html(summary_pairs),
            name="Summary (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )
        allure.attach(
            _build_table_html(
                ["Type", "Count"],
                [[action_type, count] for action_type, count in action_type_stats.most_common()],
                right_cols=(1,),
            ),
            name="Actions by type",
            attachment_type=allure.attachment_type.HTML,
        )
        allure.attach(
            _build_table_html(
                ["TRANSFER source", "Count"],
                [[source, count] for source, count in transfer_source_stats.most_common()],
                right_cols=(1,),
            ),
            name="TRANSFER by source",
            attachment_type=allure.attachment_type.HTML,
        )
        allure.attach(
            _build_table_html(
                ["USE source", "Count"],
                [[source, count] for source, count in use_source_stats.most_common()],
                right_cols=(1,),
            ),
            name="USE by source",
            attachment_type=allure.attachment_type.HTML,
        )
        allure.attach(
            _build_user_totals_html(sent_rows, received_rows),
            name="Users by sent and received visits",
            attachment_type=allure.attachment_type.HTML,
        )

    if monitoring_notes:
        with allure.step("РџСЂРёР»РѕР¶РёС‚СЊ РјРѕРЅРёС‚РѕСЂРёРЅРіРѕРІС‹Рµ РЅР°Р±Р»СЋРґРµРЅРёСЏ"):
            allure.attach(
                _build_table_html(
                    ["Note", "Count"],
                    [[kind, count] for kind, count in note_stats.most_common()],
                    right_cols=(1,),
                ),
                name="Monitoring notes by type",
                attachment_type=allure.attachment_type.HTML,
            )
            allure.attach(
                _build_table_html(
                    ["Kind", "Action ID", "Created at", "Source", "Details"],
                    [
                        [
                            item["kind"],
                            item["action_id"],
                            item["created_at"],
                            item["source"],
                            item["details"],
                        ]
                        for item in monitoring_notes[:200]
                    ],
                ),
                name="Monitoring note samples",
                attachment_type=allure.attachment_type.HTML,
            )

    if anomalies:
        with allure.step("РџСЂРёР»РѕР¶РёС‚СЊ СЃС‚Р°С‚РёСЃС‚РёРєСѓ Рё РїСЂРёРјРµСЂС‹ Р°РЅРѕРјР°Р»РёР№"):
            allure.attach(
                _build_table_html(
                    ["Anomaly", "Count"],
                    [[kind, count] for kind, count in anomaly_stats.most_common()],
                    right_cols=(1,),
                ),
                name="Anomalies by type",
                attachment_type=allure.attachment_type.HTML,
            )
            allure.attach(
                _build_table_html(
                    ["Kind", "Action ID", "Created at", "Source", "Details"],
                    [
                        [
                            item["kind"],
                            item["action_id"],
                            item["created_at"],
                            item["source"],
                            item["details"],
                        ]
                        for item in anomalies[:200]
                    ],
                ),
                name="Anomaly samples",
                attachment_type=allure.attachment_type.HTML,
            )

    assert not anomalies, (
        "РќР°Р№РґРµРЅС‹ РїСЂРѕР±Р»РµРјС‹ С†РµР»РѕСЃС‚РЅРѕСЃС‚Рё РІ userguestvisitactions: "
        + ", ".join(f"{kind}={count}" for kind, count in anomaly_stats.most_common())
    )
