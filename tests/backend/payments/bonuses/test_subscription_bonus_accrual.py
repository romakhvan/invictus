"""
Проверка корректности начисления бонусов за покупку абонемента.

Бизнес-правила (% от итоговой суммы транзакции):
  Годовой       (interval=365, не рекуррентный) — начисляется 10%
  Полугодовой   (interval=180, не рекуррентный) — начисляется 7%
  3-месячный    (interval=90)                   — бонус НЕ начисляется
  Месячный      (interval=30)                   — бонус НЕ начисляется
  Рекуррентный  (isRecurrent=True)              — бонус НЕ начисляется

Начисление фиксируется в userbonuseshistories с type=SUBSCRIPTION.
База расчёта: transactions.price — фактически оплаченная сумма после вычета
  bonusesSpent (потраченных бонусов) и скидки по промокоду.
  Частные случаи:
  - Без промокода и без bonusesSpent: transactions.price == paidFor.subscription[0].price
  - С промокодом: transactions.price = цена плана − скидка
  - С bonusesSpent: transactions.price = цена плана − bonusesSpent
"""

import pytest
import allure
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection

# Ожидаемый процент начисления по длительности плана (дни → доля)
ACCRUAL_RATES = {
    365: 0.10,  # годовой
    180: 0.07,  # полугодовой
}
NO_ACCRUAL_INTERVALS = {90, 30}  # 3-месячный, месячный

SAMPLE_SIZE = 300          # кол-во последних транзакций для проверки
TIME_TOLERANCE_SEC = 1800  # ±30 минут на появление бонуса
AMOUNT_TOLERANCE = 2       # ±2 тг на погрешность округления


def _interval_label(interval: int) -> str:
    return {365: "Годовой", 180: "Полугодовой", 90: "3-месячный", 30: "Месячный"}.get(
        interval, f"Неизвестный ({interval} дн.)"
    )


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus accrual")
@allure.title("Бонусы за покупку абонемента начислены корректно (тип и сумма)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "accrual", "subscription", "userbonuseshistories")
def test_subscription_bonus_accrual(db, period_days):
    """
    Для выборки последних SAMPLE_SIZE покупок абонементов (не рекуррентных) проверяет:
    1. Годовой / Полугодовой → запись SUBSCRIPTION в userbonuseshistories существует
       и amount ≈ price * ожидаемый_%.
    2. 3-месячный / Месячный → запись SUBSCRIPTION в userbonuseshistories ОТСУТСТВУЕТ.
    """
    transactions_col = get_collection(db, "transactions")
    subscriptions_col = get_collection(db, "subscriptions")
    bonus_col = get_collection(db, "userbonuseshistories")
    since = datetime.now() - timedelta(days=period_days)

    # 1. Выборка покупок абонементов (не рекуррентные платежи)
    with allure.step(f"Загрузить последние {SAMPLE_SIZE} покупок абонементов за {period_days} дней"):
        transactions = list(transactions_col.find(
            {
                "status": "success",
                "productType": {"$in": ["services", "subscription"]},
                "paidFor.subscription.0": {"$exists": True},
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "price": 1,
                "bonusesSpent": 1,
                "created_at": 1,
                "clubId": 1,
                "productType": 1,
                "paidFor.subscription": 1,
                "paidFor.discountId": 1,
            },
        ).sort("created_at", -1).limit(SAMPLE_SIZE))

    if not transactions:
        pytest.skip(f"Нет покупок абонементов за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций в выборке", len(transactions))

    # 2. Bulk-загрузка планов абонементов
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

    # 3. Bulk-загрузка SUBSCRIPTION-бонусов за период
    with allure.step("Загрузить SUBSCRIPTION-записи из userbonuseshistories"):
        user_ids = list({t["userId"] for t in transactions if t.get("userId")})
        times = [t["created_at"] for t in transactions]
        window_start = min(times) - timedelta(seconds=TIME_TOLERANCE_SEC)
        window_end   = max(times) + timedelta(seconds=TIME_TOLERANCE_SEC)

        sub_bonuses = list(bonus_col.find(
            {
                "type": "SUBSCRIPTION",
                "user": {"$in": user_ids},
                "time": {"$gte": window_start, "$lte": window_end},
            },
            {"_id": 1, "user": 1, "amount": 1, "time": 1},
        ))

    # Индекс: userId -> [(time, amount, bonus_id)]
    bonus_lookup = defaultdict(list)
    for b in sub_bonuses:
        bonus_lookup[str(b["user"])].append((b["time"], b["amount"], b["_id"]))

    allure.dynamic.parameter("SUBSCRIPTION-бонусов найдено", len(sub_bonuses))

    # 4. Сопоставление транзакций с бонусами
    with allure.step("Сопоставить транзакции с SUBSCRIPTION-бонусами"):
        missing_bonus   = []   # годовой/полугодовой — бонус не найден
        wrong_amount    = []   # годовой/полугодовой — бонус есть, но сумма не та
        unexpected_bonus = []  # 3-месячный/месячный — бонус не должен быть
        skipped         = []   # план не найден или interval неизвестен

        for t in transactions:
            subs = t.get("paidFor", {}).get("subscription", [])
            sub_id = subs[0].get("subscriptionId") if subs else None
            plan = plan_map.get(sub_id) if sub_id else None

            if not plan:
                skipped.append({"reason": "план не найден", "tx_id": t["_id"]})
                continue

            interval = plan.get("interval")
            is_recurrent = plan.get("isRecurrent", False)

            # Рекуррентные планы пропускаем — для них бонусов быть не должно,
            # и recurrent-транзакции уже отфильтрованы по productType выше.
            if is_recurrent:
                skipped.append({"reason": "рекуррентный план", "tx_id": t["_id"]})
                continue

            if interval not in ACCRUAL_RATES and interval not in NO_ACCRUAL_INTERVALS:
                skipped.append({"reason": f"неизвестный interval={interval}", "tx_id": t["_id"]})
                continue

            user_id = str(t.get("userId", ""))
            tx_time = t["created_at"]
            price = t.get("price", 0)

            # База для расчёта бонуса — всегда transactions.price:
            # фактически оплаченная сумма после вычета bonusesSpent и скидки по промокоду.
            subs_paid = t.get("paidFor", {}).get("subscription", [])
            sub_price = subs_paid[0].get("price", 0) if subs_paid else 0
            has_promo = bool(t.get("paidFor", {}).get("discountId"))
            bonuses_spent = t.get("bonusesSpent", 0) or 0
            base_price = price  # transactions.price уже учитывает все вычеты

            # Транзакции с нулевой ценой пропускаем — бонус не начисляется
            if price == 0 or sub_price == 0:
                skipped.append({"reason": "price=0" if price == 0 else "sub_price=0", "tx_id": t["_id"]})
                continue

            # Ищем SUBSCRIPTION-бонус в окне ±10 мин
            candidates = [
                (bt, ba, bid) for bt, ba, bid in bonus_lookup.get(user_id, [])
                if abs((bt - tx_time).total_seconds()) <= TIME_TOLERANCE_SEC
            ]

            if interval in ACCRUAL_RATES:
                # --- Годовой / Полугодовой: бонус ОБЯЗАТЕЛЕН ---
                rate = ACCRUAL_RATES[interval]
                expected_amount = round(base_price * rate)

                if not candidates:
                    missing_bonus.append({
                        "tx_id": t["_id"],
                        "plan_name": plan.get("name", "—"),
                        "interval": interval,
                        "price": price,
                        "sub_price": sub_price,
                        "expected_amount": expected_amount,
                        "created_at": tx_time,
                    })
                else:
                    # Берём кандидата с наиболее близкой суммой
                    best = min(candidates, key=lambda c: abs(c[1] - expected_amount))
                    actual_amount = best[1]
                    if abs(actual_amount - expected_amount) > AMOUNT_TOLERANCE:
                        wrong_amount.append({
                            "tx_id": t["_id"],
                            "plan_name": plan.get("name", "—"),
                            "interval": interval,
                            "price": price,
                            "sub_price": sub_price,
                            "bonuses_spent": bonuses_spent,
                            "base_price": base_price,
                            "has_promo": has_promo,
                            "expected_amount": expected_amount,
                            "actual_amount": actual_amount,
                            "diff": actual_amount - expected_amount,
                            "created_at": tx_time,
                        })

            else:
                # --- 3-месячный / Месячный: бонус НЕ должен начисляться ---
                if candidates:
                    unexpected_bonus.append({
                        "tx_id": t["_id"],
                        "plan_name": plan.get("name", "—"),
                        "interval": interval,
                        "price": price,
                        "bonus_amount": candidates[0][1],
                        "created_at": tx_time,
                    })

    # 5. Статистика
    with allure.step("Статистика по типам абонементов"):
        type_counts = defaultdict(int)
        for t in transactions:
            subs = t.get("paidFor", {}).get("subscription", [])
            sub_id = subs[0].get("subscriptionId") if subs else None
            plan = plan_map.get(sub_id) if sub_id else None
            interval = plan.get("interval") if plan else None
            type_counts[_interval_label(interval) if interval else "план не найден"] += 1

        stat_lines = [f"Всего транзакций: {len(transactions)}", ""]
        for label, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
            stat_lines.append(f"  {label}: {cnt}")
        stat_lines += [
            "",
            f"Пропущено (нет плана / неизвестный interval): {len(skipped)}",
            f"Нарушений — нет бонуса: {len(missing_bonus)}",
            f"Нарушений — неверная сумма: {len(wrong_amount)}",
            f"Нарушений — бонус не должен быть: {len(unexpected_bonus)}",
        ]
        stat_text = "\n".join(stat_lines)
        print("\n" + stat_text)
        allure.attach(stat_text, name="Статистика", attachment_type=allure.attachment_type.TEXT)

    # 6. Отчёты нарушений
    total_violations = len(missing_bonus) + len(wrong_amount) + len(unexpected_bonus)

    if missing_bonus:
        lines = [
            f"Годовой/Полугодовой без SUBSCRIPTION-бонуса: {len(missing_bonus)}\n",
            "  дата               | tx_id                    | план        | оплачено   | цена плана | ожид. бонус",
            "  " + "-" * 95,
        ]
        for v in missing_bonus[:20]:
            date_str = v["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            lines.append(
                f"  {date_str} | {v['tx_id']} | {v['plan_name']:<11} | "
                f"{v['price']:>9} тг | {v['sub_price']:>9} тг | {v['expected_amount']:>10} тг"
            )
        allure.attach("\n".join(lines), name="Нет SUBSCRIPTION-бонуса", attachment_type=allure.attachment_type.TEXT)

    if wrong_amount:
        lines = [
            f"Неверная сумма SUBSCRIPTION-бонуса: {len(wrong_amount)}\n",
            "  дата               | tx_id                    | план        | цена плана | бонусы сп. | цена (база)| ожид. бонус     | факт. бонус | разница",
            "  " + "-" * 145,
        ]
        for v in wrong_amount[:20]:
            date_str = v["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            rate_pct = int(ACCRUAL_RATES[v["interval"]] * 100)
            promo_mark = " +promo" if v["has_promo"] else ""
            lines.append(
                f"  {date_str} | {v['tx_id']} | {v['plan_name']:<11} | "
                f"{v['sub_price']:>9} тг | {v['bonuses_spent']:>9} тг | "
                f"{v['base_price']:>9} тг{promo_mark:<7} | "
                f"{v['expected_amount']:>8} тг ({rate_pct}%) | {v['actual_amount']:>10} тг | {v['diff']:>+7d}"
            )
        allure.attach("\n".join(lines), name="Неверная сумма бонуса", attachment_type=allure.attachment_type.TEXT)

    if unexpected_bonus:
        lines = [
            f"Бонус начислен, хотя не должен: {len(unexpected_bonus)}\n",
            "  дата               | tx_id                    | план        | интервал | оплачено   | факт. бонус",
            "  " + "-" * 100,
        ]
        for v in unexpected_bonus[:20]:
            date_str = v["created_at"].strftime("%Y-%m-%d %H:%M:%S")
            lines.append(
                f"  {date_str} | {v['tx_id']} | {v['plan_name']:<11} | "
                f"{v['interval']:>5} дн. | {v['price']:>9} тг | {v['bonus_amount']:>10} тг"
            )
        allure.attach("\n".join(lines), name="Лишний SUBSCRIPTION-бонус", attachment_type=allure.attachment_type.TEXT)

    assert total_violations == 0, (
        f"Найдено {total_violations} нарушений начисления SUBSCRIPTION-бонусов: "
        f"отсутствует={len(missing_bonus)}, неверная сумма={len(wrong_amount)}, "
        f"лишний бонус={len(unexpected_bonus)}."
    )
