from datetime import datetime

from src.services.backend_checks import payments_checks_service as service


def test_promo_code_discount_check_ignores_full_price_assertion_for_joinfee_spread(
    monkeypatch,
):
    transaction = {
        "_id": "tx-joinfee",
        "userId": "user-1",
        "created_at": datetime(2026, 4, 21, 15, 29, 22),
        "paidFor": {
            "discountId": "discount-joinfee",
            "discountedPrice": 33900,
            "subscription": [
                {
                    "price": 33900,
                }
            ],
        },
    }
    discount = {
        "_id": "discount-joinfee",
        "name": "GIRLS",
        "type": "percentage",
        "amount": 100,
        "isDeleted": False,
        "startDate": datetime(2026, 4, 1),
        "endDate": datetime(2026, 4, 30, 23, 59, 59),
        "destination": {
            "spreadOn": {
                "type": "joinfee",
            }
        },
    }

    monkeypatch.setattr(
        service,
        "get_transactions_with_promo_code",
        lambda db, since: [transaction],
    )
    monkeypatch.setattr(
        service,
        "get_discounts_map_by_ids",
        lambda db, discount_ids: {"discount-joinfee": discount},
    )

    result = service.run_promo_code_discount_check(
        db=object(),
        period_days=14,
        now=datetime(2026, 4, 23, 12, 0, 0),
    )

    assert result.transactions_count == 1
    assert [violation.kind for violation in result.violations] == []
