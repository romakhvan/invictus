"""
Проверка: один абонемент не может быть заморожен более одного раза.

Бизнес-правило: для каждого userSubscriptionID должна существовать
не более одной успешной транзакции с productType=FREEZE_DAYS.
"""

import pytest
import allure
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Freezing")
@allure.title("Один абонемент не может быть заморожен более одного раза")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "freezing", "duplicate")
def test_freeze_days_no_duplicate(db, period_days):
    """
    Для каждого userSubscriptionID проверяет, что не существует двух и более
    успешных транзакций productType=FREEZE_DAYS — повторная заморозка
    одного абонемента является нарушением бизнес-правила.
    """
    col = get_collection(db, "transactions")
    since = datetime.now() - timedelta(days=period_days)

    with allure.step(f"Загрузить FREEZE_DAYS транзакции за {period_days} дней"):
        transactions = list(col.find(
            {
                "productType": "FREEZE_DAYS",
                "status": "success",
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "created_at": 1,
                "price": 1,
                "paidFor.freezing.userSubscription": 1,
            },
        ).sort("created_at", -1))

    if not transactions:
        pytest.skip(f"Нет FREEZE_DAYS транзакций за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций FREEZE_DAYS", len(transactions))

    with allure.step("Сгруппировать по userSubscriptionID и найти дубликаты"):
        by_sub = defaultdict(list)
        skipped = 0
        for t in transactions:
            user_sub_id = t.get("paidFor", {}).get("freezing", {}).get("userSubscription")
            if not user_sub_id:
                skipped += 1
                continue
            by_sub[str(user_sub_id)].append(t)

        violations = {sub_id: txs for sub_id, txs in by_sub.items() if len(txs) > 1}

    allure.dynamic.parameter("Уникальных подписок", len(by_sub))
    allure.dynamic.parameter("Нарушений (дублей)", len(violations))

    if not violations:
        allure.attach(
            f"Дублей не найдено. Проверено {len(by_sub)} уникальных подписок.",
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step(f"Сформировать отчёт о {len(violations)} нарушениях"):
        lines = [
            f"Абонементов с дублирующей заморозкой: {len(violations)} из {len(by_sub)}",
            "",
        ]
        for sub_id, txs in sorted(violations.items(), key=lambda x: -len(x[1])):
            lines.append(f"userSubscription={sub_id} ({len(txs)} транзакции)")
            for t in txs:
                date_str = t["created_at"].strftime("%Y-%m-%d %H:%M:%S") if t.get("created_at") else "—"
                lines.append(
                    f"  - {date_str} | {t['_id']} | userId={t.get('userId')} | price={t.get('price')} тг"
                )
            lines.append("")

        report = "\n".join(lines)
        print("\n" + report)
        allure.attach(report, name="Дубли заморозки", attachment_type=allure.attachment_type.TEXT)

    first_sub_id = next(iter(violations))
    first_tx = violations[first_sub_id][0]
    assert len(violations) == 0, (
        f"Найдено {len(violations)} абонементов с повторной заморозкой. "
        f"Первый: userSubscriptionID={first_sub_id}, "
        f"кол-во транзакций={len(violations[first_sub_id])}, "
        f"первая транзакция id={first_tx['_id']}"
    )
