"""
Проверка лимитов списания бонусов в зависимости от длительности абонемента.

Бизнес-правила (bonusesSpent ≤ X% от полной цены абонемента):
  Годовой       (interval=365) — не более 20%
  Полугодовой   (interval=180) — не более 10%
  3-месячный    (interval=90)  — не более 7%
  Месячный      (interval=30)  — не более 5%

Рекуррентные платежи (productType=recurrent) этим тестом не охватываются —
они проверяются в test_forbidden_types_no_bonus_spend.py.
"""

import pytest
import allure
from bson import ObjectId
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection

# Лимит бонусного списания по длительности плана (дни → макс. доля)
DEDUCTION_LIMITS = {
    365: 0.20,  # годовой
    180: 0.10,  # полугодовой
    90:  0.07,  # 3-месячный
    30:  0.05,  # месячный
}


def _interval_to_label(interval: int) -> str:
    labels = {365: "Годовой", 180: "Полугодовой", 90: "3-месячный", 30: "Месячный"}
    return labels.get(interval, f"Неизвестный ({interval} дн.)")


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus deduction")
@allure.title("Лимиты списания бонусов соблюдаются по типу абонемента")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "deduction", "subscription", "limits")
def test_deduction_limits_by_plan(db, period_days):
    """
    Для каждой успешной транзакции со списанием бонусов (bonusesSpent > 0)
    проверяет, что лимит не превышен в зависимости от длительности абонемента.
    Тест охватывает все productType кроме recurrent (они в test_forbidden_types_no_bonus_spend).
    """
    transactions_col = get_collection(db, "transactions")
    subscriptions_col = get_collection(db, "subscriptions")
    since = datetime.now() - timedelta(days=period_days)

    # 1. Транзакции с bonusesSpent > 0 и непустым paidFor.subscription
    with allure.step(f"Загрузить транзакции с bonusesSpent > 0 за {period_days} дней"):
        transactions = list(transactions_col.find(
            {
                "status": "success",
                "bonusesSpent": {"$gt": 0},
                "paidFor.subscription.0": {"$exists": True},  # непустой массив
                "productType": {"$ne": "recurrent"},          # recurrent — отдельный тест
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "productType": 1,
                "bonusesSpent": 1,
                "price": 1,
                "created_at": 1,
                "clubId": 1,
                "userId": 1,
                "paidFor.subscription": 1,
            },
        ).sort("created_at", -1))

    if not transactions:
        pytest.skip(f"Нет транзакций с bonusesSpent > 0 и абонементом за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций для проверки", len(transactions))

    # 2. Bulk-загрузка планов абонементов по subscriptionId
    with allure.step("Загрузить планы абонементов (interval, isRecurrent)"):
        sub_ids = set()
        for t in transactions:
            subs = t.get("paidFor", {}).get("subscription", [])
            if subs and subs[0].get("subscriptionId"):
                sub_ids.add(subs[0]["subscriptionId"])

        plans = list(subscriptions_col.find(
            {"_id": {"$in": list(sub_ids)}},
            {"_id": 1, "name": 1, "interval": 1, "isRecurrent": 1},
        ))
        plan_map = {p["_id"]: p for p in plans}

    # 3. Проверка лимитов
    with allure.step("Проверить лимит для каждой транзакции"):
        violations = []
        skipped_unknown_plan = []

        for t in transactions:
            subs = t.get("paidFor", {}).get("subscription", [])
            if not subs:
                continue

            full_price = subs[0].get("price")
            sub_id = subs[0].get("subscriptionId")
            if not full_price or not sub_id:
                continue

            plan = plan_map.get(sub_id)
            if not plan:
                skipped_unknown_plan.append(t["_id"])
                continue

            interval = plan.get("interval")
            if interval not in DEDUCTION_LIMITS:
                skipped_unknown_plan.append(t["_id"])
                continue

            max_fraction = DEDUCTION_LIMITS[interval]
            bonuses_spent = t.get("bonusesSpent", 0)
            actual_fraction = bonuses_spent / full_price

            if actual_fraction > max_fraction + 1e-9:  # допуск на погрешность округления
                violations.append({
                    "_id": t["_id"],
                    "productType": t.get("productType"),
                    "plan_name": plan.get("name", "—"),
                    "interval": interval,
                    "full_price": full_price,
                    "paid_price": t.get("price"),
                    "bonuses_spent": bonuses_spent,
                    "actual_pct": round(actual_fraction * 100, 2),
                    "limit_pct": int(max_fraction * 100),
                    "created_at": t.get("created_at"),
                    "club_id": t.get("clubId"),
                })

    # 4. Статистика по типам планов
    with allure.step("Статистика по типам абонементов"):
        by_interval = defaultdict(lambda: {"total": 0, "violations": 0})
        for t in transactions:
            subs = t.get("paidFor", {}).get("subscription", [])
            sub_id = subs[0].get("subscriptionId") if subs else None
            plan = plan_map.get(sub_id) if sub_id else None
            interval = plan.get("interval") if plan else None
            by_interval[interval]["total"] += 1
            if any(v["_id"] == t["_id"] for v in violations):
                by_interval[interval]["violations"] += 1

        stat_lines = []
        for interval, stat in sorted(by_interval.items(), key=lambda x: -(x[1]["total"])):
            label = _interval_to_label(interval) if interval else "план не найден"
            limit = f"≤{int(DEDUCTION_LIMITS[interval] * 100)}%" if interval in DEDUCTION_LIMITS else "—"
            stat_lines.append(
                f"  {label:<20} {limit:<8} транзакций: {stat['total']}, нарушений: {stat['violations']}"
            )
        if skipped_unknown_plan:
            stat_lines.append(f"  Пропущено (неизвестный план): {len(skipped_unknown_plan)}")

        stat_text = "\n".join(stat_lines)
        print("\n" + stat_text)
        allure.attach(stat_text, name="Статистика по типам", attachment_type=allure.attachment_type.TEXT)

    if not violations:
        return

    # 5. Отчёт о нарушениях
    with allure.step(f"Сформировать отчёт о {len(violations)} нарушениях"):
        by_label = defaultdict(list)
        for v in violations:
            by_label[_interval_to_label(v["interval"])].append(v)

        lines = [f"Нарушений лимита списания: {len(violations)}\n"]
        for label, items in sorted(by_label.items(), key=lambda x: -len(x[1])):
            lines.append(f"{label} (лимит ≤{items[0]['limit_pct']}%) — {len(items)} нарушений")
            for v in items[:15]:
                date_str = v["created_at"].strftime("%Y-%m-%d %H:%M:%S") if v.get("created_at") else "—"
                lines.append(
                    f"  - {date_str} | {v['_id']} | {v['plan_name']} | "
                    f"цена={v['full_price']} тг | списано={v['bonuses_spent']} тг ({v['actual_pct']}%)"
                )
            if len(items) > 15:
                lines.append(f"  ... и ещё {len(items) - 15}")
            lines.append("")

        report = "\n".join(lines)
        print("\n" + report)
        allure.attach(report, name="Нарушения лимитов", attachment_type=allure.attachment_type.TEXT)

    first = violations[0]
    assert len(violations) == 0, (
        f"Найдено {len(violations)} нарушений лимита списания бонусов. "
        f"Первая: id={first['_id']}, план='{first['plan_name']}' ({_interval_to_label(first['interval'])}), "
        f"списано {first['actual_pct']}% при лимите {first['limit_pct']}%"
    )
