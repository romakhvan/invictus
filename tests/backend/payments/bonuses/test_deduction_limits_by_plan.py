"""
Проверка лимитов списания бонусов в зависимости от длительности абонемента.

Бизнес-правила (bonusesSpent <= X% от полной цены абонемента):
  Годовой       (interval=365) - не более 20%
  Полугодовой   (interval=180) - не более 10%
  3-месячный    (interval=90)  - не более 7%
  Месячный      (interval=30)  - не более 5%

Рекуррентные платежи (productType=recurrent) этим тестом не охватываются -
они проверяются в test_forbidden_types_no_bonus_spend.py.
"""

import allure
import pytest

from src.services.backend_checks.payments_checks_service import (
    run_bonus_deduction_limits_check,
)
from src.services.reporting.payments_text_reports import (
    build_bonus_deduction_limits_report,
)


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus deduction")
@allure.title("Лимиты списания бонусов соблюдаются по типу абонемента")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "deduction", "subscription", "limits")
def test_deduction_limits_by_plan(db, period_days):
    """
    Для каждой успешной транзакции со списанием бонусов (bonusesSpent > 0)
    проверяет, что лимит не превышен в зависимости от длительности абонемента.
    Тест охватывает все productType кроме recurrent.
    """
    with allure.step(f"Проверить лимиты списания бонусов за {period_days} дней"):
        result = run_bonus_deduction_limits_check(db=db, period_days=period_days)

    if result.transactions_count == 0:
        pytest.skip(
            f"Нет транзакций с bonusesSpent > 0 и абонементом за последние {period_days} дней"
        )

    allure.dynamic.parameter("Транзакций для проверки", result.transactions_count)
    allure.dynamic.parameter("Планов загружено", result.plans_count)
    allure.dynamic.parameter("Нарушений найдено", len(result.violations))

    report = build_bonus_deduction_limits_report(result)

    if not result.violations:
        allure.attach(
            report,
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step(f"Сформировать отчет о {len(result.violations)} нарушениях"):
        print("\n" + report)
        allure.attach(
            report,
            name="Нарушения лимитов",
            attachment_type=allure.attachment_type.TEXT,
        )

    first = result.violations[0]
    assert len(result.violations) == 0, (
        f"Найдено {len(result.violations)} нарушений лимита списания бонусов. "
        f"Первая: id={first.tx_id}, план='{first.plan_name}' ({first.interval} дн.), "
        f"списано {first.actual_pct}% при лимите {first.limit_pct}%"
    )