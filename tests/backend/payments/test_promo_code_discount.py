"""
Проверка корректности применения промокодов в транзакциях.

Бизнес-правило: каждая успешная транзакция с промокодом (paidFor.discountId)
должна ссылаться на существующую, не удалённую скидку, которая была активна
в момент покупки. Для подписочных транзакций также проверяется математика:
итоговая цена (discountedPrice) должна соответствовать вычисленной скидке.
"""

import pytest
import allure
from collections import defaultdict
from datetime import datetime, timedelta

from bson import ObjectId

from src.utils.repository_helpers import get_collection

PRICE_TOLERANCE = 1  # допуск ±1 тг на округление


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Промокоды")
@allure.title("Применённый промокод корректно отражён в транзакции: скидка, цена, период действия")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "discounts", "promo", "price")
def test_promo_code_discount_correctness(db, period_days):
    """
    Для каждой успешной транзакции с paidFor.discountId проверяет:
    A — скидка существует в коллекции discounts
    B — скидка не удалена (isDeleted: false)
    C — скидка была активна в момент транзакции (startDate <= created_at <= endDate)
    D — для подписочных транзакций: discountedPrice совпадает с расчётным значением
    """
    transactions_col = get_collection(db, "transactions")
    discounts_col = get_collection(db, "discounts")
    since = datetime.now() - timedelta(days=period_days)

    # 1. Загрузить транзакции с промокодом за период
    with allure.step(f"Загрузить успешные транзакции с промокодом за {period_days} дней"):
        transactions = list(transactions_col.find(
            {
                "paidFor.discountId": {"$exists": True},
                "status": "success",
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "created_at": 1,
                "price": 1,
                "productType": 1,
                "paidFor.discountId": 1,
                "paidFor.discountedPrice": 1,
                "paidFor.totalPrice": 1,
                "paidFor.subscription": 1,
            },
        ).sort("created_at", -1))

    if not transactions:
        pytest.skip(f"Нет транзакций с промокодом за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций с промокодом", len(transactions))

    # 2. Bulk-загрузить все затронутые скидки
    with allure.step("Загрузить документы скидок из коллекции discounts"):
        raw_ids = [t["paidFor"]["discountId"] for t in transactions if t.get("paidFor", {}).get("discountId")]
        discount_ids = list({ObjectId(str(did)) for did in raw_ids})
        discounts_map = {
            str(d["_id"]): d
            for d in discounts_col.find({"_id": {"$in": discount_ids}})
        }

    allure.dynamic.parameter("Уникальных промокодов", len(discounts_map))

    # 3. Проверить каждую транзакцию
    with allure.step("Проверить соответствие промокода условиям"):
        violations = []

        for tx in transactions:
            paid_for = tx.get("paidFor", {})
            discount_id_raw = paid_for.get("discountId")
            if not discount_id_raw:
                continue

            discount_id = str(discount_id_raw)
            tx_id = str(tx["_id"])
            tx_date = tx.get("created_at")
            user_id = str(tx.get("userId", "—"))
            discount = discounts_map.get(discount_id)

            # A — скидка существует
            if not discount:
                violations.append({
                    "kind": "A",
                    "label": "Скидка не найдена",
                    "tx_id": tx_id,
                    "discount_id": discount_id,
                    "user_id": user_id,
                    "date": tx_date,
                    "detail": f"discountId={discount_id} не найден в коллекции discounts",
                })
                continue

            discount_name = discount.get("name", discount_id)

            # B — скидка не удалена
            if discount.get("isDeleted"):
                violations.append({
                    "kind": "B",
                    "label": "Скидка удалена",
                    "tx_id": tx_id,
                    "discount_id": discount_id,
                    "discount_name": discount_name,
                    "user_id": user_id,
                    "date": tx_date,
                    "detail": f"промокод {discount_name} помечен isDeleted=true",
                })

            # C — скидка была активна в момент транзакции
            if tx_date:
                start = discount.get("startDate")
                end = discount.get("endDate")
                if start and end:
                    # Привести к naive datetime если необходимо
                    if tx_date.tzinfo is not None:
                        tx_date_cmp = tx_date.replace(tzinfo=None)
                    else:
                        tx_date_cmp = tx_date
                    start_cmp = start.replace(tzinfo=None) if start.tzinfo else start
                    end_cmp = end.replace(tzinfo=None) if end.tzinfo else end

                    if not (start_cmp <= tx_date_cmp <= end_cmp):
                        violations.append({
                            "kind": "C",
                            "label": "Скидка неактивна на дату транзакции",
                            "tx_id": tx_id,
                            "discount_id": discount_id,
                            "discount_name": discount_name,
                            "user_id": user_id,
                            "date": tx_date,
                            "detail": (
                                f"промокод {discount_name}: "
                                f"период {start.date()} — {end.date()}, "
                                f"транзакция {tx_date.date()}"
                            ),
                        })

            # D — математика скидки (только для транзакций с подпиской)
            subscriptions = paid_for.get("subscription") or []
            discounted_price = paid_for.get("discountedPrice")

            if subscriptions and discounted_price is not None:
                original = subscriptions[0].get("price")
                disc_type = discount.get("type", "")
                amount = discount.get("amount", 0)

                expected = None
                if original is not None:
                    if disc_type in ("percentage", "%"):
                        expected = round(original * (1 - amount / 100))
                    elif disc_type == "cash":
                        expected = original - amount

                if expected is not None and abs(discounted_price - expected) > PRICE_TOLERANCE:
                    violations.append({
                        "kind": "D",
                        "label": "Неверная сумма скидки",
                        "tx_id": tx_id,
                        "discount_id": discount_id,
                        "discount_name": discount_name,
                        "user_id": user_id,
                        "date": tx_date,
                        "detail": (
                            f"промокод {discount_name} ({disc_type} {amount}): "
                            f"ожидалось={expected} тг, факт discountedPrice={discounted_price} тг, "
                            f"catalog price={original} тг"
                        ),
                    })

    allure.dynamic.parameter("Нарушений найдено", len(violations))

    if not violations:
        allure.attach(
            f"Все {len(transactions)} транзакций прошли проверку промокода.",
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    # 4. Отчёт о нарушениях
    with allure.step(f"Сформировать отчёт о {len(violations)} нарушениях"):
        by_kind = defaultdict(list)
        for v in violations:
            by_kind[v["kind"]].append(v)

        lines = [
            f"Нарушений промокодов: {len(violations)} из {len(transactions)} транзакций",
            "",
        ]
        for kind in ("A", "B", "C", "D"):
            items = by_kind.get(kind, [])
            if not items:
                continue
            label = items[0]["label"]
            lines.append(f"[{kind}] {label} ({len(items)})")
            for v in items[:10]:
                date_str = v["date"].strftime("%Y-%m-%d %H:%M:%S") if v.get("date") else "—"
                lines.append(f"  - {date_str} | {v['tx_id']} | {v['detail']}")
            if len(items) > 10:
                lines.append(f"  ... и ещё {len(items) - 10}")
            lines.append("")

        report = "\n".join(lines)
        print("\n" + report)
        allure.attach(report, name="Нарушения промокодов", attachment_type=allure.attachment_type.TEXT)

    first = violations[0]
    assert len(violations) == 0, (
        f"Найдено {len(violations)} нарушений промокодов из {len(transactions)} транзакций. "
        f"Первое [{first['kind']}]: {first['detail']}, "
        f"tx_id={first['tx_id']}, дата={first.get('date')}"
    )
