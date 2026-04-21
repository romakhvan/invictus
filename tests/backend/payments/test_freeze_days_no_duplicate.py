"""
Проверка: один абонемент не может быть заморожен более одного раза.

Бизнес-правило: для каждого userSubscriptionID должна существовать
не более одной успешной транзакции с productType=FREEZE_DAYS.
"""

import pytest
import allure

from src.services.backend_checks.payments_checks_service import (
    run_freeze_days_no_duplicate_check,
)
from src.services.reporting.payments_text_reports import (
    build_freeze_days_duplicate_report,
)


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Freezing")
@allure.title("Один абонемент не может быть заморожен более одного раза")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "freezing", "duplicate")
def test_freeze_days_no_duplicate(db, period_days):
    """
    Для каждого userSubscriptionID проверяет, что не существует двух и более
    успешных транзакций productType=FREEZE_DAYS — повторная заморозка
    одного абонемента является нарушением бизнес-правила.
    """
    with allure.step(f"Вычислить дубликаты FREEZE_DAYS за {period_days} дней"):
        result = run_freeze_days_no_duplicate_check(db=db, period_days=period_days)

    if result.transactions_count == 0:
        pytest.skip(f"Нет FREEZE_DAYS транзакций за последние {period_days} дней")

    allure.dynamic.parameter("Транзакций FREEZE_DAYS", result.transactions_count)
    allure.dynamic.parameter("Уникальных подписок", result.unique_subscriptions_count)
    allure.dynamic.parameter("Пропущено без userSubscription", result.skipped_without_subscription)
    allure.dynamic.parameter("Нарушений (дублей)", len(result.violations))

    report = build_freeze_days_duplicate_report(result)

    if not result.violations:
        allure.attach(
            report,
            name="Результат",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    with allure.step(f"Сформировать отчёт о {len(result.violations)} нарушениях"):
        print("\n" + report)
        allure.attach(report, name="Дубли заморозки", attachment_type=allure.attachment_type.TEXT)

    first_violation = result.violations[0]
    first_transaction = first_violation.transactions[0]
    assert len(result.violations) == 0, (
        f"Найдено {len(result.violations)} абонементов с повторной заморозкой. "
        f"Первый: userSubscriptionID={first_violation.user_subscription_id}, "
        f"кол-во транзакций={len(first_violation.transactions)}, "
        f"первая транзакция id={first_transaction['_id']}"
    )
