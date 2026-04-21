"""
Проверка корректности начисления бонусов за покупку абонемента.

Бизнес-правила (% от итоговой суммы транзакции):
  Годовой       (interval=365, не рекуррентный) - начисляется 10%
  Полугодовой   (interval=180, не рекуррентный) - начисляется 7%
  3-месячный    (interval=90)                   - бонус не начисляется
  Месячный      (interval=30)                   - бонус не начисляется
  Рекуррентный  (isRecurrent=True)              - бонус не начисляется

Начисление фиксируется в userbonuseshistories с type=SUBSCRIPTION.
База расчета: transactions.price - фактически оплаченная сумма после вычета
bonusesSpent и скидки по промокоду.
"""

import allure
import pytest

from src.services.backend_checks.payments_checks_service import (
    SUBSCRIPTION_BONUS_AMOUNT_TOLERANCE,
    SUBSCRIPTION_BONUS_SAMPLE_SIZE,
    SUBSCRIPTION_BONUS_TIME_TOLERANCE_SEC,
    run_subscription_bonus_accrual_check,
)
from src.services.reporting.payments_text_reports import (
    build_subscription_bonus_accrual_report,
)


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus accrual")
@allure.title("Бонусы за покупку абонемента начислены корректно (тип и сумма)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "accrual", "subscription", "userbonuseshistories")
def test_subscription_bonus_accrual(db, period_days):
    """
    Для выборки последних покупок абонементов проверяет:
    1. Годовой / Полугодовой -> запись SUBSCRIPTION в userbonuseshistories существует
       и amount ~= price * ожидаемый_%.
    2. 3-месячный / Месячный -> запись SUBSCRIPTION в userbonuseshistories отсутствует.
    """
    with allure.step(f"Проверить начисление SUBSCRIPTION-бонусов за {period_days} дней"):
        result = run_subscription_bonus_accrual_check(
            db=db,
            period_days=period_days,
            sample_size=SUBSCRIPTION_BONUS_SAMPLE_SIZE,
            time_tolerance_sec=SUBSCRIPTION_BONUS_TIME_TOLERANCE_SEC,
            amount_tolerance=SUBSCRIPTION_BONUS_AMOUNT_TOLERANCE,
        )

    if result.transactions_count == 0:
        pytest.skip(f"Нет покупок абонементов за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций в выборке", result.transactions_count)
    allure.dynamic.parameter("Планов загружено", result.plans_count)
    allure.dynamic.parameter("SUBSCRIPTION-бонусов найдено", result.bonus_records_count)

    total_violations = (
        len(result.missing_bonus)
        + len(result.wrong_amount)
        + len(result.unexpected_bonus)
    )
    allure.dynamic.parameter("Нарушений найдено", total_violations)

    report = build_subscription_bonus_accrual_report(result)

    if total_violations == 0:
        allure.attach(
            report,
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step(f"Сформировать отчет о {total_violations} нарушениях"):
        print("\n" + report)
        allure.attach(
            report,
            name="Нарушения начисления SUBSCRIPTION-бонусов",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert total_violations == 0, (
        f"Найдено {total_violations} нарушений начисления SUBSCRIPTION-бонусов: "
        f"отсутствует={len(result.missing_bonus)}, неверная сумма={len(result.wrong_amount)}, "
        f"лишний бонус={len(result.unexpected_bonus)}."
    )