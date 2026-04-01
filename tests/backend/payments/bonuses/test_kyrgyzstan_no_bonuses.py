"""
Проверка бизнес-правила: в Кыргызстане бонусы не используются при оплате.
Ни одна успешная транзакция с country=KG не должна иметь bonusesSpent != null.
"""
import pytest
import allure
from bson import ObjectId
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection

KYRGYZSTAN_COUNTRY_ID = ObjectId("67c1a10edd7823df5c8bcace")


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Kyrgyzstan bonuses restriction")
@allure.title("В Кыргызстане бонусы не используются при оплате")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "kyrgyzstan", "bonuses")
def test_kyrgyzstan_no_bonuses_spent(db, period_days):
    """
    Проверяет, что ни одна успешная транзакция в Кыргызстане
    не содержит bonusesSpent != null.
    """
    col = get_collection(db, "transactions")
    days_ago = datetime.now() - timedelta(days=period_days)

    # Sanity-check: известное нарушение должно быть видно в этой БД
    known = col.find_one({"_id": ObjectId("69a98aa3245025ac664f144e")})
    assert known is not None, (
        "Sanity-check провален: транзакция 69a98aa3245025ac664f144e не найдена. "
        "Тест подключён не к той БД (ожидается PROD)."
    )

    violations = list(col.find(
        {
            "country": {"$in": [KYRGYZSTAN_COUNTRY_ID, str(KYRGYZSTAN_COUNTRY_ID)]},
            "bonusesSpent": {"$ne": None},
            "status": "success",
            "created_at": {"$gte": days_ago},
        },
        {"_id": 1, "bonusesSpent": 1, "price": 1, "created_at": 1, "clubId": 1},
    ).sort("created_at", -1).limit(20))

    if violations:
        lines = [f"Найдено нарушений: {len(violations)}\n"]
        for t in violations:
            created = t.get("created_at")
            lines.append(
                f"  _id={t['_id']}  bonusesSpent={t.get('bonusesSpent')}  "
                f"price={t.get('price')}  date={created}"
            )
        detail = "\n".join(lines)
        allure.attach(detail, name="Нарушения", attachment_type=allure.attachment_type.TEXT)

    assert len(violations) == 0, (
        f"Найдено {len(violations)} транзакций в Кыргызстане с bonusesSpent != null. "
        f"Первая: _id={violations[0]['_id']}"
    )
