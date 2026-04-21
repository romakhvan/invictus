"""
Проверка корректности применения промокодов в транзакциях.

Бизнес-правило: каждая успешная транзакция с промокодом (paidFor.discountId)
должна ссылаться на существующую, не удалённую скидку, которая была активна
в момент покупки. Для подписочных транзакций также проверяется математика:
итоговая цена (discountedPrice) должна соответствовать вычисленной скидке.
"""

import pytest
import allure
from src.services.backend_checks.payments_checks_service import (
    run_promo_code_discount_check,
)
from src.services.reporting.payments_text_reports import (
    build_promo_code_discount_report,
)


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
    with allure.step(f"Проверить транзакции с промокодом за {period_days} дней"):
        result = run_promo_code_discount_check(db=db, period_days=period_days)

    if result.transactions_count == 0:
        pytest.skip(f"Нет транзакций с промокодом за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций с промокодом", result.transactions_count)
    allure.dynamic.parameter("Уникальных промокодов", result.unique_discount_count)
    allure.dynamic.parameter("Нарушений найдено", len(result.violations))

    report = build_promo_code_discount_report(result)

    if not result.violations:
        allure.attach(
            report,
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step(f"Сформировать отчёт о {len(result.violations)} нарушениях"):
        print("\n" + report)
        allure.attach(report, name="Нарушения промокодов", attachment_type=allure.attachment_type.TEXT)

    first_violation = result.violations[0]
    assert len(result.violations) == 0, (
        f"Найдено {len(result.violations)} нарушений промокодов из {result.transactions_count} транзакций. "
        f"Первое [{first_violation.kind}]: {first_violation.detail}, "
        f"tx_id={first_violation.tx_id}, дата={first_violation.date}"
    )
