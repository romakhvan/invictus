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
    build_promo_code_discount_reports,
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
    with allure.step(f"Проверить транзакции с промокодом за последние {period_days} дней"):
        result = run_promo_code_discount_check(db=db, period_days=period_days)

    if result.transactions_count == 0:
        pytest.skip(f"Нет транзакций с промокодом за последние {period_days} дней")

    allure.dynamic.parameter("Обработано транзакций с промокодом", result.transactions_count)
    allure.dynamic.parameter("Уникальных промокодов", result.unique_discount_count)
    allure.dynamic.parameter("Нарушений", len(result.violations))

    reports = build_promo_code_discount_reports(result)

    print("\n=== ИТОГ ПРОВЕРКИ ПРОМОКОДОВ ===\n" + reports["summary_text"])
    allure.attach(
        reports["summary_text"],
        name="Итог проверки промокодов",
        attachment_type=allure.attachment_type.TEXT,
    )

    if result.violations:
        print("\n=== НАРУШЕНИЯ ПРОМОКОДОВ ===\n" + reports["violations_text"])
        allure.attach(
            reports["violations_text"],
            name="Нарушения промокодов",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            reports["violations_html"],
            name="Нарушения промокодов (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )
        if reports["expected_vs_actual_text"]:
            allure.attach(
                reports["expected_vs_actual_text"],
                name="Expected vs Actual",
                attachment_type=allure.attachment_type.TEXT,
            )

    latest_violation = (
        max(result.violations, key=lambda item: item.date or result.since)
        if result.violations
        else None
    )
    assert len(result.violations) == 0, (
        f"Найдено {len(result.violations)} нарушений промокодов "
        f"из {result.transactions_count} транзакций за последние {period_days} дней. "
        f"Последняя ошибочная запись: tx_id={latest_violation.tx_id}, "
        f"date={latest_violation.date}, kind={latest_violation.kind}, "
        f"discountId={latest_violation.discount_id}, "
        f"discountName={latest_violation.discount_name or '—'}, "
        f"userId={latest_violation.user_id or '—'}, detail={latest_violation.detail}"
    )
