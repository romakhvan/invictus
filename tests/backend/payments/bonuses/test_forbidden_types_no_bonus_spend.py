"""
Проверка: запрещённые типы транзакций не должны списывать бонусы.

Бизнес-правило: следующие productType не поддерживают оплату бонусами:
  - recurrent       — рекуррентная подписка (автооплата)
  - rabbitHoleV2    — внутренний тип подписки
  - saveCard        — сохранение карты (без реальной оплаты)
  - fillBalance     — пополнение баланса
  - freezing        — заморозка (у неё отдельный тип FREEZE_DAYS с другими правилами)
"""

import pytest
import allure

from src.services.backend_checks.payments_checks_service import (
    FORBIDDEN_BONUS_PRODUCT_TYPES,
    run_forbidden_bonus_spend_check,
)
from src.services.reporting.payments_text_reports import (
    build_forbidden_bonus_spend_report,
)


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus deduction")
@allure.title("Запрещённые типы транзакций не списывают бонусы")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "deduction", "forbidden")
def test_forbidden_types_no_bonus_spend(db, period_days):
    """
    Проверяет, что транзакции с productType из списка запрещённых
    не содержат bonusesSpent > 0.
    """
    with allure.step(f"Проверить запрещённые productType за {period_days} дней"):
        result = run_forbidden_bonus_spend_check(
            db=db,
            period_days=period_days,
            forbidden_types=FORBIDDEN_BONUS_PRODUCT_TYPES,
        )

    allure.dynamic.parameter("Запрещённых productType", len(result.forbidden_types))
    allure.dynamic.parameter("Нарушений найдено", result.violations_count)

    report = build_forbidden_bonus_spend_report(result)

    if not result.violation_groups:
        allure.attach(
            report,
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step("Сгруппировать нарушения по productType"):
        print("\n" + report)
        allure.attach(
            report,
            name="Нарушения по типам",
            attachment_type=allure.attachment_type.TEXT,
        )

    first_group = result.violation_groups[0]
    first_violation = first_group.transactions[0]
    assert result.violations_count == 0, (
        f"Найдено {result.violations_count} транзакций запрещённых типов со списанием бонусов. "
        f"Типы: {[group.product_type for group in result.violation_groups]}. "
        f"Первая: id={first_violation['_id']}, productType={first_violation.get('productType')}, "
        f"bonusesSpent={first_violation.get('bonusesSpent')}, дата={first_violation.get('created_at')}"
    )
