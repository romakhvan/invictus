"""
Мониторинг распределения транзакций по доле бонусов от полной стоимости.
Аналитический тест — не проверяет нарушения, только репортирует распределение.
"""

import allure
import pytest
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.allure_html import html_table, HTML_CSS

# Корзины: [lo, hi) — верхняя граница последней = 101, чтобы включить pct == 100.0
BINS = [
    (0, 10), (10, 20), (20, 30), (30, 40), (40, 50),
    (50, 60), (60, 70), (70, 80), (80, 90), (90, 101),
]
BIN_LABELS = [
    "Использовано бонусов 0–10%", "Использовано бонусов 10–20%", "Использовано бонусов 20–30%",
    "Использовано бонусов 30–40%", "Использовано бонусов 40–50%", "Использовано бонусов 50–60%",
    "Использовано бонусов 60–70%", "Использовано бонусов 70–80%", "Использовано бонусов 80–90%",
    "Использовано бонусов 90–100%",
]

# Максимум строк на корзину в детальной таблице
MAX_ROWS_PER_BIN = 200


def _pct_str(value: float) -> str:
    return f"{value:.1f}%"


def _fmt_num(n: float) -> str:
    """1234567 → '1 234 567'"""
    return f"{int(n):,}".replace(",", "\u00a0")



def _build_overall_html(overall_by_type: dict, total_count: int) -> str:
    """Итого по productType."""
    headers = ["productType", "Кол-во", "% от всех"]
    rows = []
    for pt, e in sorted(overall_by_type.items(), key=lambda x: -x[1]["count"]):
        rows.append([
            pt,
            e["count"],
            _pct_str(e["count"] / total_count * 100) if total_count else "—",
        ])
    table = html_table(headers, rows, right_cols=(1, 2))
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{HTML_CSS}</head><body>{table}</body></html>"


def _build_by_product_html(bin_details: dict) -> str:
    """
    Объединённая таблица: для каждого productType — список транзакций с указанием корзины.
    Строки отсортированы по дате убывания.
    """
    by_product = defaultdict(list)
    for txs in bin_details.values():
        for tx in txs:
            by_product[tx["pt"]].append(tx)

    headers = [
        "Название", "Дата и время", "Transaction ID", "User ID",
        "Полная стоимость", "Бонусов использовано", "% бонусов",
    ]
    parts = []
    for pt in sorted(by_product.keys()):
        txs = by_product[pt]
        sorted_txs = sorted(txs, key=lambda x: x["pct"], reverse=True)
        shown = sorted_txs[:10]
        rest = len(txs) - len(shown)
        parts.append(f"<h2>{pt} ({len(txs)} транзакций)</h2>")
        rows = []
        for tx in shown:
            rows.append([
                tx["name"],
                tx["dt"],
                tx["tx_id"],
                tx["user_id"],
                _fmt_num(tx["full_cost"]),
                _fmt_num(tx["bonuses_spent"]),
                _pct_str(tx["pct"]),
            ])
        if rest > 0:
            rows.append([f"<span class='gray'>... и ещё {rest}</span>", "", "", "", "", "", ""])
        parts.append(html_table(headers, rows, right_cols=(4, 5, 6)))
    body = "".join(parts) or "<p>Нет данных</p>"
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{HTML_CSS}</head><body>{body}</body></html>"


def _build_combined_html(bin_details: dict) -> str:
    """
    Объединённая таблица: для каждой корзины — список транзакций с разбивкой по productType.
    Строки отсортированы по productType, внутри — по дате убывания.
    """
    headers = [
        "productType", "Дата и время", "Transaction ID", "User ID",
        "Полная стоимость", "Бонусов использовано", "% бонусов",
    ]
    parts = []
    for i, label in enumerate(BIN_LABELS):
        txs = bin_details[i]
        if not txs:
            continue
        sorted_txs = sorted(txs, key=lambda x: (x["pt"], x["dt"]))
        shown = sorted_txs[:MAX_ROWS_PER_BIN]
        rest = len(txs) - len(shown)
        parts.append(f"<h2>{label} ({len(txs)} транзакций)</h2>")
        rows = []
        for tx in shown:
            rows.append([
                tx["pt"],
                tx["dt"],
                tx["tx_id"],
                tx["user_id"],
                _fmt_num(tx["full_cost"]),
                _fmt_num(tx["bonuses_spent"]),
                _pct_str(tx["pct"]),
            ])
        if rest > 0:
            rows.append([f"<span class='gray'>... и ещё {rest}</span>", "", "", "", "", "", ""])
        parts.append(html_table(headers, rows, right_cols=(4, 5, 6)))
    body = "".join(parts) or "<p>Нет данных</p>"
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{HTML_CSS}</head><body>{body}</body></html>"


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus usage")
@allure.title("Распределение транзакций по доле бонусов от полной стоимости")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("backend", "payments", "bonuses", "monitoring", "distribution")
def test_bonus_usage_distribution(db, period_days):
    """
    Аналитический мониторинг: показывает распределение успешных транзакций с бонусами
    по корзинам (0–10%, 10–20%, ..., 90–100%) с разбивкой по productType.
    Формула: full_cost = price + bonusesSpent, bonus_pct = bonusesSpent / full_cost * 100.
    Тест не проверяет нарушения и не падает при наличии данных.
    """
    transactions_col = db["transactions"]
    now = datetime.utcnow()
    since = now - timedelta(days=period_days)

    # --- Шаг 1: Загрузка ---
    with allure.step(f"Загрузить транзакции с bonusesSpent > 0 за {period_days} дней"):
        transactions = list(transactions_col.find(
            {
                "status": "success",
                "bonusesSpent": {"$gt": 0},
                "isDeleted": {"$ne": True},
                "created_at": {"$gte": since},
            },
            {"_id": 1, "bonusesSpent": 1, "price": 1, "productType": 1, "userId": 1, "created_at": 1, "paidFor": 1},
        ).sort("created_at", -1))

    if not transactions:
        pytest.skip(f"Нет транзакций с bonusesSpent > 0 за последние {period_days} дней")

    # --- Bulk-загрузка названий продуктов ---
    with allure.step("Загрузить названия продуктов из subscriptions"):
        sub_ids = set()
        for t in transactions:
            subs = t.get("paidFor", {}).get("subscription", [])
            if subs and subs[0].get("subscriptionId"):
                sub_ids.add(subs[0]["subscriptionId"])
        plans = list(db["subscriptions"].find(
            {"_id": {"$in": list(sub_ids)}},
            {"_id": 1, "name": 1},
        ))
        plan_map = {p["_id"]: p.get("name") or "—" for p in plans}

    # --- Шаг 2: Группировка ---
    with allure.step("Рассчитать долю бонусов и сгруппировать по корзинам"):
        bins_data = defaultdict(lambda: defaultdict(lambda: {"count": 0}))
        bin_details = defaultdict(list)
        overall_by_type = defaultdict(lambda: {"count": 0})
        skipped = 0
        total_bonuses = 0.0

        for t in transactions:
            bonuses_spent = t.get("bonusesSpent") or 0
            price = t.get("price") or 0
            full_cost = price + bonuses_spent
            if full_cost <= 0:
                skipped += 1
                continue

            pct = bonuses_spent / full_cost * 100
            bin_idx = min(int(pct // 10), 9)
            pt = t.get("productType") or "unknown"
            subs = t.get("paidFor", {}).get("subscription", [])
            sub_id = subs[0].get("subscriptionId") if subs else None
            name = plan_map.get(sub_id, "—") if sub_id else "—"

            bins_data[bin_idx][pt]["count"] += 1
            overall_by_type[pt]["count"] += 1
            total_bonuses += bonuses_spent

            bin_details[bin_idx].append({
                "pt": pt,
                "name": name,
                "dt": t["created_at"].strftime("%Y-%m-%d %H:%M:%S"),
                "tx_id": str(t["_id"]),
                "user_id": str(t.get("userId", "—")),
                "full_cost": full_cost,
                "bonuses_spent": bonuses_spent,
                "pct": pct,
            })

        total_count = len(transactions) - skipped

        allure.dynamic.parameter("Транзакций с бонусами", total_count)
        allure.attach(
            (
                f"Период: последние {period_days} дней "
                f"(с {since.strftime('%Y-%m-%d')} по {now.strftime('%Y-%m-%d')} UTC)\n"
                f"Всего транзакций с bonusesSpent > 0: {len(transactions)}\n"
                f"Пропущено (full_cost = 0): {skipped}\n"
                f"Итого бонусов потрачено: {_fmt_num(total_bonuses)} тг"
            ),
            name="Конфигурация",
            attachment_type=allure.attachment_type.TEXT,
        )

    # --- Шаг 3: Детализация по productType + список транзакций ---
    with allure.step("Детализация транзакций по корзинам и productType"):
        allure.attach(
            _build_combined_html(bin_details),
            name="Транзакции по корзинам и productType",
            attachment_type=allure.attachment_type.HTML,
        )

    # --- Шаг 4: Детализация по productType ---
    with allure.step("Детализация транзакций по productType"):
        allure.attach(
            _build_by_product_html(bin_details),
            name="Транзакции по productType",
            attachment_type=allure.attachment_type.HTML,
        )

    # --- Шаг 5: Общая статистика по productType ---
    with allure.step("Общая статистика по productType"):
        allure.attach(
            _build_overall_html(overall_by_type, total_count),
            name="Итого по productType",
            attachment_type=allure.attachment_type.HTML,
        )
