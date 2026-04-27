from datetime import datetime

from src.services.backend_checks.payments_checks_service import (
    PromoCodeDiscountCheckResult,
    PromoCodeDiscountViolation,
)
from src.services.reporting.payments_text_reports import build_promo_code_discount_reports


def test_promo_code_discount_reports_include_summary_and_success_context():
    result = PromoCodeDiscountCheckResult(
        period_days=7,
        since=datetime(2026, 4, 15, 10, 0, 0),
        transactions_count=12,
        unique_discount_count=3,
        violations=[],
    )

    reports = build_promo_code_discount_reports(result)

    assert "Итог проверки промокодов" in reports["summary_text"]
    assert "Период: последние 7 дней" in reports["summary_text"]
    assert "Проверено транзакций с paidFor.discountId: 12" in reports["summary_text"]
    assert "Промокодов найдено в discounts: 3" in reports["summary_text"]
    assert "Нарушений: 0" in reports["summary_text"]
    assert "Последняя ошибочная запись" not in reports["summary_text"]
    assert reports["violations_text"] == ""


def test_promo_code_discount_reports_split_violations_by_diagnostic_purpose():
    result = PromoCodeDiscountCheckResult(
        period_days=14,
        since=datetime(2026, 4, 8, 10, 0, 0),
        transactions_count=20,
        unique_discount_count=4,
        violations=[
            PromoCodeDiscountViolation(
                kind="A",
                label="Скидка не найдена",
                tx_id="tx-old",
                discount_id="discount-missing",
                user_id="user-1",
                date=datetime(2026, 4, 12, 9, 0, 0),
                detail="discountId=discount-missing не найден в коллекции discounts",
            ),
            PromoCodeDiscountViolation(
                kind="D",
                label="Неверная сумма скидки",
                tx_id="tx-new",
                discount_id="discount-price",
                discount_name="SPRING",
                user_id="user-2",
                date=datetime(2026, 4, 18, 15, 30, 0),
                detail="промокод SPRING (% 20): ожидалось=8000 тг, факт discountedPrice=9000 тг, catalog price=10000 тг",
            ),
        ],
    )

    reports = build_promo_code_discount_reports(result)

    assert "Нарушений: 2" in reports["summary_text"]
    assert "by_kind_text" not in reports
    assert "by_kind_html" not in reports
    assert "[A] Скидка не найдена (1)" in reports["violations_text"]
    assert "[D] Неверная сумма скидки (1)" in reports["violations_text"]
    assert "tx_id=tx-new" in reports["violations_text"]
    assert "discountId=discount-price" in reports["violations_text"]
    assert "ожидалось=8000 тг" in reports["expected_vs_actual_text"]
    assert "факт discountedPrice=9000 тг" in reports["expected_vs_actual_text"]
    assert "latest_violation_text" not in reports
    assert "latest_violations_html" not in reports
    assert "Последняя ошибочная запись: 2026-04-18 15:30:00" in reports["summary_text"]
    assert "tx_id=tx-new" in reports["summary_text"]
