"""
Мониторинг транзакций со статусом internalError.
Такие транзакции указывают на внутренние ошибки сервера при обработке платежа.
"""

import pytest
import allure
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Transaction Errors")
@allure.title("Транзакции со статусом internalError отсутствуют")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "transactions", "internalError", "monitoring")
def test_no_internal_error_transactions(db, period_days):
    """
    Проверяет, что за указанный период нет транзакций со статусом internalError.
    Такой статус означает непредвиденную ошибку на стороне сервера.
    Группирует найденные проблемы по клубам и типам продуктов.
    """
    transactions_col = get_collection(db, "transactions")
    clubs_col = get_collection(db, "clubs")
    since = datetime.now() - timedelta(days=period_days)

    # 1. Получить транзакции с internalError за период
    with allure.step(f"Найти транзакции со статусом internalError за {period_days} дней"):
        error_transactions = list(transactions_col.find(
            {
                "status": "internalError",
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "clubId": 1,
                "price": 1,
                "created_at": 1,
                "productType": 1,
                "source": 1,
                "instalmentType": 1,
                "userId": 1,
                "reason": 1,
            },
        ).sort("created_at", -1))

    allure.dynamic.parameter("Найдено internalError транзакций", len(error_transactions))

    if not error_transactions:
        allure.attach(
            "Транзакций со статусом internalError не найдено. Всё в порядке.",
            name="Результат проверки",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    # 2. Загрузить названия клубов
    with allure.step("Загрузить информацию о клубах"):
        club_ids = list({t["clubId"] for t in error_transactions if t.get("clubId")})
        clubs = list(clubs_col.find({"_id": {"$in": club_ids}}, {"_id": 1, "name": 1}))
        club_id_to_name = {c["_id"]: c["name"] for c in clubs}

    # 3. Группировка по клубу
    with allure.step("Сгруппировать по клубам"):
        by_club = defaultdict(list)
        for t in error_transactions:
            club_id = t.get("clubId")
            club_name = club_id_to_name.get(club_id, f"Unknown ({club_id})") if club_id else "Без клуба"
            by_club[club_name].append(t)

        by_club_sorted = sorted(by_club.items(), key=lambda x: -len(x[1]))

    # 4. Сформировать текстовый отчёт
    with allure.step("Сформировать отчёт"):
        lines = [
            f"Всего транзакций с internalError: {len(error_transactions)}",
            f"Затронуто клубов: {len(by_club)}",
            "",
        ]
        for club_name, txs in by_club_sorted:
            lines.append(f"{club_name} ({len(txs)})")
            for t in txs[:10]:
                created_at = t.get("created_at")
                date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "—"
                price = t.get("price", 0)
                price_fmt = f"{int(price):,}".replace(",", " ") + " тг"
                product_type = t.get("productType") or "—"
                source = t.get("source") or "—"
                reason = t.get("reason") or "—"
                lines.append(
                    f"  - {date_str} | {t['_id']} | {price_fmt} | {product_type} | {source} | {reason}"
                )
            if len(txs) > 10:
                lines.append(f"  ... и ещё {len(txs) - 10}")
            lines.append("")

        report_text = "\n".join(lines)
        print("\n" + report_text)
        allure.attach(
            report_text,
            name="Транзакции с internalError",
            attachment_type=allure.attachment_type.TEXT,
        )

    # 5. Сгруппировать по productType для дополнительного контекста
    with allure.step("Статистика по productType"):
        by_product = defaultdict(int)
        for t in error_transactions:
            by_product[t.get("productType") or "—"] += 1

        product_lines = [f"{pt}: {cnt}" for pt, cnt in sorted(by_product.items(), key=lambda x: -x[1])]
        allure.attach(
            "\n".join(product_lines),
            name="Разбивка по productType",
            attachment_type=allure.attachment_type.TEXT,
        )

    # 6. Assert
    first = error_transactions[0]
    first_club = club_id_to_name.get(first.get("clubId"), "—")
    assert len(error_transactions) == 0, (
        f"Найдено {len(error_transactions)} транзакций со статусом internalError "
        f"за последние {period_days} дней. "
        f"Первая: id={first['_id']}, клуб={first_club}, "
        f"дата={first.get('created_at')}, productType={first.get('productType')}"
    )
