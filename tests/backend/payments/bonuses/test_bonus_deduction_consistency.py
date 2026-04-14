"""
Проверка консистентности списания бонусов между двумя коллекциями.

Бизнес-правило: каждая успешная транзакция с bonusesSpent > 0 должна иметь
соответствующую запись type=PAY в userbonuseshistories с amount = -bonusesSpent
для того же пользователя в интервале ±5 минут.
"""

import pytest
import allure
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection

TIME_TOLERANCE_SEC = 300  # ±5 минут
AMOUNT_TOLERANCE = 1      # допуск ±1 тг на округление


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus deduction")
@allure.title("Каждое списание бонусов в транзакции отражено в userbonuseshistories")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "deduction", "consistency", "userbonuseshistories")
def test_bonus_deduction_consistency(db, period_days):
    """
    Для каждой транзакции с bonusesSpent > 0 проверяет наличие записи
    type=PAY в userbonuseshistories с amount = -bonusesSpent для того же
    пользователя в допустимом временном окне (±5 минут).
    """
    transactions_col = get_collection(db, "transactions")
    bonus_col = get_collection(db, "userbonuseshistories")
    since = datetime.now() - timedelta(days=period_days)

    # 1. Все транзакции с bonusesSpent > 0 за период
    with allure.step(f"Загрузить транзакции с bonusesSpent > 0 за {period_days} дней"):
        transactions = list(transactions_col.find(
            {
                "status": "success",
                "bonusesSpent": {"$gt": 0},
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "bonusesSpent": 1,
                "created_at": 1,
                "productType": 1,
                "clubId": 1,
                "price": 1,
            },
        ).sort("created_at", -1))

    if not transactions:
        pytest.skip(f"Нет транзакций с bonusesSpent > 0 за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций для проверки", len(transactions))

    # 2. Bulk-загрузка PAY-записей за тот же период (с буфером ±5 мин)
    with allure.step("Загрузить PAY-записи из userbonuseshistories"):
        user_ids = list({t["userId"] for t in transactions if t.get("userId")})
        times = [t["created_at"] for t in transactions]
        window_start = min(times) - timedelta(seconds=TIME_TOLERANCE_SEC)
        window_end   = max(times) + timedelta(seconds=TIME_TOLERANCE_SEC)

        pay_records = list(bonus_col.find(
            {
                "type": "PAY",
                "user": {"$in": user_ids},
                "time": {"$gte": window_start, "$lte": window_end},
            },
            {"_id": 1, "user": 1, "amount": 1, "time": 1},
        ))

    allure.dynamic.parameter("PAY-записей найдено", len(pay_records))

    # 3. Индекс PAY-записей: userId -> [(time, amount, _id)]
    pay_lookup = defaultdict(list)
    for p in pay_records:
        pay_lookup[str(p["user"])].append((p["time"], p["amount"], p["_id"]))

    # 4. Для каждой транзакции ищем соответствующую PAY-запись
    with allure.step("Сопоставить транзакции с PAY-записями"):
        violations = []
        matched_pay_ids = set()

        for t in transactions:
            user_id = str(t.get("userId", ""))
            bonuses_spent = t["bonusesSpent"]
            tx_time = t["created_at"]
            expected_amount = -bonuses_spent

            user_pays = pay_lookup.get(user_id, [])
            match = None
            for pay_time, pay_amount, pay_id in user_pays:
                time_diff = abs((pay_time - tx_time).total_seconds())
                if time_diff <= TIME_TOLERANCE_SEC and abs(pay_amount - expected_amount) <= AMOUNT_TOLERANCE:
                    match = pay_id
                    break

            if match:
                matched_pay_ids.add(match)
            else:
                violations.append({
                    "_id": t["_id"],
                    "userId": user_id,
                    "bonusesSpent": bonuses_spent,
                    "created_at": tx_time,
                    "productType": t.get("productType", "—"),
                    "price": t.get("price"),
                    "user_pay_count": len(user_pays),
                })

    allure.dynamic.parameter("Нарушений найдено", len(violations))

    if not violations:
        allure.attach(
            f"Все {len(transactions)} транзакций имеют соответствующую PAY-запись.",
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    # 5. Отчёт о нарушениях
    with allure.step(f"Сформировать отчёт о {len(violations)} нарушениях"):
        by_type = defaultdict(list)
        for v in violations:
            by_type[v["productType"]].append(v)

        lines = [
            f"Транзакций без PAY-записи: {len(violations)} из {len(transactions)}",
            "",
        ]
        for product_type, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            lines.append(f"{product_type} ({len(items)})")
            for v in items[:10]:
                date_str = v["created_at"].strftime("%Y-%m-%d %H:%M:%S") if v.get("created_at") else "—"
                lines.append(
                    f"  - {date_str} | {v['_id']} | "
                    f"bonusesSpent={v['bonusesSpent']} тг | "
                    f"PAY-записей для этого user={v['user_pay_count']}"
                )
            if len(items) > 10:
                lines.append(f"  ... и ещё {len(items) - 10}")
            lines.append("")

        report = "\n".join(lines)
        print("\n" + report)
        allure.attach(report, name="Транзакции без PAY-записи", attachment_type=allure.attachment_type.TEXT)

    first = violations[0]
    assert len(violations) == 0, (
        f"Найдено {len(violations)} транзакций с bonusesSpent > 0 без соответствующей PAY-записи "
        f"в userbonuseshistories (окно ±{TIME_TOLERANCE_SEC // 60} мин). "
        f"Первая: id={first['_id']}, bonusesSpent={first['bonusesSpent']}, "
        f"productType={first['productType']}, дата={first['created_at']}"
    )
