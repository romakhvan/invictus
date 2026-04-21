"""
Мониторинг использования бонусов в транзакциях по клиентам и купленным продуктам.
Аналитический тест — не проверяет пороги, а публикует сводку и детализацию в Allure.
"""

import allure
import pytest

from src.services.backend_checks.payments_checks_service import run_bonus_usage_monitoring
from src.utils.allure_html import HTML_CSS, html_table


def _fmt_num(value: int | float) -> str:
    """1234567 -> '1 234 567'."""
    return f"{int(value):,}".replace(",", "\u00a0")


def _fmt_datetime(value) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _build_clients_html(result) -> str:
    headers = [
        "User ID",
        "Транзакций",
        "Бонусов использовано",
        "Первая транзакция",
        "Последняя транзакция",
        "На что потрачены бонусы",
    ]
    rows = [
        [
            client.user_id,
            client.transactions_count,
            _fmt_num(client.bonuses_spent_total),
            _fmt_datetime(client.first_transaction_at),
            _fmt_datetime(client.last_transaction_at),
            client.spent_on_summary,
        ]
        for client in result.clients
    ]
    table = html_table(headers, rows, right_cols=(1, 2))
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{HTML_CSS}</head><body>{table}</body></html>"


def _build_products_html(result) -> str:
    headers = ["productType", "Название", "Транзакций", "Бонусов использовано"]
    rows = [
        [
            product.product_type,
            product.product_name,
            product.transactions_count,
            _fmt_num(product.bonuses_spent_total),
        ]
        for product in result.products
    ]
    table = html_table(headers, rows, right_cols=(2, 3))
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{HTML_CSS}</head><body>{table}</body></html>"


def _build_product_types_html(result) -> str:
    headers = ["productType", "Транзакций"]
    rows = [
        [product_type, count]
        for product_type, count in result.product_type_counts.items()
    ]
    table = html_table(headers, rows, right_cols=(1,))
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{HTML_CSS}</head><body>{table}</body></html>"


def _build_transactions_html(result) -> str:
    headers = [
        "Дата и время",
        "Transaction ID",
        "User ID",
        "productType",
        "Название",
        "Доп. информация",
        "Price",
        "bonusesSpent",
    ]
    rows = [
        [
            _fmt_datetime(transaction.created_at),
            transaction.tx_id,
            transaction.user_id,
            transaction.product_type,
            transaction.product_name,
            transaction.product_meta,
            _fmt_num(transaction.price or 0),
            _fmt_num(transaction.bonuses_spent),
        ]
        for transaction in result.transactions
    ]
    table = html_table(headers, rows, right_cols=(6, 7))
    return f"<!DOCTYPE html><html><head><meta charset='utf-8'>{HTML_CSS}</head><body>{table}</body></html>"


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus usage")
@allure.title("Мониторинг использования бонусов по клиентам и купленным продуктам")
@allure.severity(allure.severity_level.NORMAL)
@allure.tag("backend", "payments", "bonuses", "monitoring", "clients", "products")
def test_bonus_usage_monitoring(db, period_days):
    """
    Аналитический мониторинг успешных транзакций с bonusesSpent > 0.
    Показывает общую статистику, сводку по клиентам и детализацию по продуктам.
    """
    with allure.step(f"Собрать мониторинг использования бонусов за {period_days} дней"):
        result = run_bonus_usage_monitoring(db=db, period_days=period_days)

    if result.transactions_count == 0:
        pytest.skip(f"Нет транзакций с bonusesSpent > 0 за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций с бонусами", result.transactions_count)
    allure.dynamic.parameter("Уникальных клиентов", result.unique_clients_count)
    allure.dynamic.parameter("Бонусов использовано", _fmt_num(result.total_bonuses_spent))

    with allure.step("Сформировать текстовую сводку"):
        summary = (
            f"Период: последние {period_days} дней\n"
            f"Начиная с: {result.since.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Успешных транзакций с bonusesSpent > 0: {result.transactions_count}\n"
            f"Уникальных клиентов: {result.unique_clients_count}\n"
            f"Всего бонусов использовано: {_fmt_num(result.total_bonuses_spent)} тг\n"
            f"Уникальных сочетаний productType/название: {len(result.products)}"
        )
        allure.attach(summary, name="Сводка", attachment_type=allure.attachment_type.TEXT)

    with allure.step("Показать статистику по клиентам"):
        allure.attach(
            _build_clients_html(result),
            name="Клиенты",
            attachment_type=allure.attachment_type.HTML,
        )

    with allure.step("Показать статистику по продуктам"):
        allure.attach(
            _build_products_html(result),
            name="Продукты",
            attachment_type=allure.attachment_type.HTML,
        )
        allure.attach(
            _build_product_types_html(result),
            name="Итого по productType",
            attachment_type=allure.attachment_type.HTML,
        )

    with allure.step("Показать детализацию транзакций"):
        allure.attach(
            _build_transactions_html(result),
            name="Транзакции с продуктами",
            attachment_type=allure.attachment_type.HTML,
        )
