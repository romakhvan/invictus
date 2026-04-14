"""
Проверка: запрещённые типы транзакций не должны списывать бонусы.

Бизнес-правило: следующие productType не поддерживают оплату бонусами:
  - recurrent       — рекуррентная подписка (автооплата)
  - rabbitHoleV2    — внутренний тип подписки
  - saveCard        — сохранение карты (без реальной оплаты)
  - fillBalance     — пополнение баланса
  - freezing        — заморозка (у неё отдельный тип FREEZE_DAYS с другими правилами)
"""

import pytest
import allure
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection

# Типы транзакций, для которых бонусы НИКОГДА не должны списываться
FORBIDDEN_TYPES = ["recurrent", "rabbitHoleV2", "saveCard", "fillBalance", "freezing"]


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus deduction")
@allure.title("Запрещённые типы транзакций не списывают бонусы")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "deduction", "forbidden")
def test_forbidden_types_no_bonus_spend(db, period_days):
    """
    Проверяет, что транзакции с productType из списка запрещённых
    не содержат bonusesSpent > 0.
    """
    col = get_collection(db, "transactions")
    since = datetime.now() - timedelta(days=period_days)

    with allure.step(f"Найти транзакции запрещённых типов с bonusesSpent > 0 за {period_days} дней"):
        violations = list(col.find(
            {
                "status": "success",
                "productType": {"$in": FORBIDDEN_TYPES},
                "bonusesSpent": {"$gt": 0},
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
            },
        ).sort("created_at", -1))

    allure.dynamic.parameter("Нарушений найдено", len(violations))

    if not violations:
        allure.attach(
            "Нарушений не найдено. Все запрещённые типы работают корректно.",
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    # Группируем по productType для наглядности
    with allure.step("Сгруппировать нарушения по productType"):
        from collections import defaultdict
        by_type = defaultdict(list)
        for v in violations:
            by_type[v.get("productType", "—")].append(v)

        lines = [
            f"Нарушений: {len(violations)} | Типов: {len(by_type)}",
            "",
        ]
        for product_type, txs in sorted(by_type.items(), key=lambda x: -len(x[1])):
            lines.append(f"{product_type} ({len(txs)})")
            for t in txs[:10]:
                created_at = t.get("created_at")
                date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "—"
                price = t.get("price", 0)
                spent = t.get("bonusesSpent", 0)
                pct = round(spent / price * 100, 1) if price else "?"
                lines.append(
                    f"  - {date_str} | {t['_id']} | цена={price} тг | списано={spent} тг ({pct}%)"
                )
            if len(txs) > 10:
                lines.append(f"  ... и ещё {len(txs) - 10}")
            lines.append("")

        report = "\n".join(lines)
        print("\n" + report)
        allure.attach(
            report,
            name="Нарушения по типам",
            attachment_type=allure.attachment_type.TEXT,
        )

    first = violations[0]
    assert len(violations) == 0, (
        f"Найдено {len(violations)} транзакций запрещённых типов со списанием бонусов. "
        f"Типы: {list(by_type.keys())}. "
        f"Первая: id={first['_id']}, productType={first.get('productType')}, "
        f"bonusesSpent={first.get('bonusesSpent')}, дата={first.get('created_at')}"
    )
