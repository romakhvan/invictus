"""
Проверка консистентности списания бонусов между двумя коллекциями.

Бизнес-правило: каждая успешная транзакция с bonusesSpent > 0 должна иметь
соответствующую запись type=PAY в userbonuseshistories с amount = -bonusesSpent
для того же пользователя в интервале ±5 минут.
"""

import pytest
import allure

from src.services.backend_checks.payments_checks_service import (
    BONUS_PAY_AMOUNT_TOLERANCE,
    BONUS_PAY_TIME_TOLERANCE_SEC,
    run_bonus_deduction_consistency_check,
)
from src.services.reporting.payments_text_reports import (
    build_bonus_deduction_consistency_report,
)


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus deduction")
@allure.title("Каждое списание бонусов в транзакции отражено в userbonuseshistories")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "deduction", "consistency", "userbonuseshistories")
def test_bonus_deduction_consistency(db, period_days):
    """
    Для каждой транзакции с bonusesSpent > 0 проверяет наличие записи
    type=PAY в userbonuseshistories с amount = -bonusesSpent для того же
    пользователя в допустимом временном окне (±5 минут).
    """
    with allure.step(f"Проверить консистентность списаний бонусов за {period_days} дней"):
        result = run_bonus_deduction_consistency_check(
            db=db,
            period_days=period_days,
            time_tolerance_sec=BONUS_PAY_TIME_TOLERANCE_SEC,
            amount_tolerance=BONUS_PAY_AMOUNT_TOLERANCE,
        )

    if result.transactions_count == 0:
        pytest.skip(f"Нет транзакций с bonusesSpent > 0 за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций для проверки", result.transactions_count)
    allure.dynamic.parameter("PAY-записей найдено", result.pay_records_count)
    allure.dynamic.parameter("Нарушений найдено", len(result.violations))

    report = build_bonus_deduction_consistency_report(result)

    if not result.violations:
        allure.attach(
            report,
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step(f"Сформировать отчёт о {len(result.violations)} нарушениях"):
        print("\n" + report)
        allure.attach(report, name="Транзакции без PAY-записи", attachment_type=allure.attachment_type.TEXT)

    first = result.violations[0]
    assert len(result.violations) == 0, (
        f"Найдено {len(result.violations)} транзакций с bonusesSpent > 0 без соответствующей PAY-записи "
        f"в userbonuseshistories (окно ±{result.time_tolerance_sec // 60} мин). "
        f"Первая: id={first.tx_id}, bonusesSpent={first.bonuses_spent}, "
        f"productType={first.product_type}, дата={first.created_at}"
    )
