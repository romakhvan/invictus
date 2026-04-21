"""
Мониторинг транзакций со статусом internalError.
Такие транзакции указывают на внутренние ошибки сервера при обработке платежа.
"""

import pytest
import allure
from src.services.backend_checks.payments_checks_service import (
    run_internal_error_transactions_check,
)
from src.services.reporting.payments_text_reports import (
    build_internal_error_product_breakdown,
    build_internal_error_report,
)


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
    with allure.step(f"Проверить internalError транзакции за {period_days} дней"):
        result = run_internal_error_transactions_check(db=db, period_days=period_days)

    allure.dynamic.parameter("Найдено internalError транзакций", result.error_transactions_count)
    allure.dynamic.parameter("Затронуто клубов", result.affected_clubs_count)

    report_text = build_internal_error_report(result)

    if result.error_transactions_count == 0:
        allure.attach(
            report_text,
            name="Результат проверки",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step("Сформировать отчёт"):
        print("\n" + report_text)
        allure.attach(
            report_text,
            name="Транзакции с internalError",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Статистика по productType"):
        allure.attach(
            build_internal_error_product_breakdown(result),
            name="Разбивка по productType",
            attachment_type=allure.attachment_type.TEXT,
        )

    first_group = result.club_groups[0]
    first_transaction = first_group.transactions[0]
    assert result.error_transactions_count == 0, (
        f"Найдено {result.error_transactions_count} транзакций со статусом internalError "
        f"за последние {period_days} дней. "
        f"Первая: id={first_transaction['_id']}, клуб={first_group.club_name}, "
        f"дата={first_transaction.get('created_at')}, productType={first_transaction.get('productType')}"
    )
