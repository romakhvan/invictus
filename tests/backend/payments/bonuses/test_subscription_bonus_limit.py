"""
Проверка бизнес-правила: при покупке абонемента нельзя оплатить бонусами более 20% от суммы.
Ни одна успешная транзакция с productType=subscription за последние 90 дней
не должна иметь bonusesSpent > 20% от полной стоимости абонемента.
"""
import allure
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection

MAX_BONUS_FRACTION = 0.20  # не более 20% от суммы абонемента


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus limit")
@allure.title("При покупке абонемента бонусами оплачено не более 20%")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "subscription")
def test_subscription_bonus_limit(db):
    """
    Проверяет, что ни одна успешная транзакция покупки абонемента
    не содержит bonusesSpent > 20% от price.
    """
    col = get_collection(db, "transactions")
    since = datetime.now() - timedelta(days=90)

    # Успешные транзакции абонементов за последние 90 дней, где бонусы были потрачены
    transactions = list(col.find(
        {
            "productType": "subscription",
            "status": "success",
            "bonusesSpent": {"$ne": None, "$gt": 0},
            "created_at": {"$gte": since},
        },
        {"_id": 1, "price": 1, "paidFor.subscription.price": 1, "bonusesSpent": 1, "created_at": 1, "clubId": 1},
    ).sort("created_at", -1))

    violations = []
    for t in transactions:
        bonuses_spent = t.get("bonusesSpent")

        # Полная стоимость абонемента — в paidFor.subscription[0].price
        subscriptions = t.get("paidFor", {}).get("subscription", [])
        full_price = subscriptions[0].get("price") if subscriptions else None

        # Пропускаем транзакции без полной стоимости во избежание деления на ноль
        if not full_price:
            continue

        fraction = bonuses_spent / full_price
        if fraction > MAX_BONUS_FRACTION:
            violations.append({
                "_id": t["_id"],
                "full_price": full_price,
                "paid_price": t.get("price"),
                "bonusesSpent": bonuses_spent,
                "fraction_pct": round(fraction * 100, 2),
                "created_at": t.get("created_at"),
                "clubId": t.get("clubId"),
            })

    if violations:
        lines = [f"Найдено нарушений: {len(violations)} (лимит: {int(MAX_BONUS_FRACTION * 100)}%)\n"]
        for v in violations:
            created = v.get("created_at")
            lines.append(
                f"  _id={v['_id']}  bonusesSpent={v['bonusesSpent']}  "
                f"full_price={v['full_price']}  paid={v['paid_price']}  доля={v['fraction_pct']}%  date={created}"
            )
        detail = "\n".join(lines)
        allure.attach(detail, name="Нарушения лимита бонусов", attachment_type=allure.attachment_type.TEXT)
        print("\n" + detail)

    assert len(violations) == 0, (
        f"Найдено {len(violations)} транзакций абонементов, где бонусы превысили "
        f"{int(MAX_BONUS_FRACTION * 100)}% от суммы. "
        f"Первая: _id={violations[0]['_id']}, full_price={violations[0]['full_price']}, "
        f"bonusesSpent={violations[0]['bonusesSpent']}, доля={violations[0]['fraction_pct']}%"
    )
