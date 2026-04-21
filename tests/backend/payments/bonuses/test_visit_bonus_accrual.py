"""
Проверка бизнес-правил начисления VISIT-бонусов:
1. Каждый VISIT-бонус соответствует реальному посещению клуба
   (accesscontrols.type=enter, без поля err, accessType != staff).
2. Пользователь получает не более одного VISIT-бонуса в день.
"""

import allure
import pytest

from src.services.backend_checks.payments_checks_service import (
    VISIT_BONUS_FORWARD_SAMPLE_USERS,
    VISIT_BONUS_SAMPLE_SIZE,
    VISIT_BONUS_TIME_TOLERANCE_SEC,
    run_visit_bonus_accrual_check,
    run_visit_bonus_coverage_check,
)
from src.services.reporting.payments_text_reports import (
    build_visit_bonus_accrual_report,
    build_visit_bonus_coverage_report,
)


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus accrual")
@allure.title("За посещение клуба начисляются бонусы (VISIT)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "visit", "accesscontrols")
def test_visit_bonus_accrual(db, period_days):
    """
    Для выборки последних VISIT-бонусов проверяет:
    1. Каждый бонус имеет соответствующий enter в accesscontrols.
    2. Ни один пользователь не получил более одного VISIT-бонуса за день.
    """
    with allure.step(f"Проверить VISIT-бонусы за {period_days} дней"):
        result = run_visit_bonus_accrual_check(
            db=db,
            period_days=period_days,
            sample_size=VISIT_BONUS_SAMPLE_SIZE,
            time_tolerance_sec=VISIT_BONUS_TIME_TOLERANCE_SEC,
        )

    if result.bonus_records_count == 0:
        pytest.skip(f"Нет VISIT-бонусов за последние {period_days} дней")

    allure.dynamic.parameter("Проверено бонусов", result.bonus_records_count)
    allure.dynamic.parameter("Валидных входов найдено", result.access_entries_count)
    allure.dynamic.parameter("Дублей за день", len(result.duplicate_days))
    allure.dynamic.parameter("Бонусов без посещения", len(result.missing_visit_bonuses))

    report = build_visit_bonus_accrual_report(result)
    total_violations = len(result.duplicate_days) + len(result.missing_visit_bonuses)

    if total_violations == 0:
        allure.attach(report, name="Результат", attachment_type=allure.attachment_type.TEXT)
        return

    with allure.step(f"Сформировать отчет о {total_violations} нарушениях"):
        print("\n" + report)
        allure.attach(
            report,
            name="Нарушения VISIT-бонусов",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert len(result.duplicate_days) == 0, (
        f"Найдено {len(result.duplicate_days)} случаев, когда пользователь получил "
        f"более одного VISIT-бонуса за день."
    )
    assert len(result.missing_visit_bonuses) == 0, (
        f"Найдено {len(result.missing_visit_bonuses)} VISIT-бонусов без соответствующего посещения клуба. "
        f"Первый: bonus_id={result.missing_visit_bonuses[0].bonus_id}, "
        f"user={result.missing_visit_bonuses[0].user_id}, "
        f"time={result.missing_visit_bonuses[0].time}"
    )


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus accrual")
@allure.title("За каждый день посещения клуба абоненту начислен VISIT-бонус")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "visit", "accesscontrols")
def test_visit_generates_bonus(db, period_days):
    """
    Для пользователей-абонентов из выборки проверяет, что каждый день с валидным
    посещением клуба содержит хотя бы один VISIT-бонус.
    """
    with allure.step(f"Проверить покрытие посещений VISIT-бонусами за {period_days} дней"):
        result = run_visit_bonus_coverage_check(
            db=db,
            period_days=period_days,
            sample_users_limit=VISIT_BONUS_FORWARD_SAMPLE_USERS,
        )

    if result.sample_users_count == 0:
        pytest.skip("Нет пользователей с VISIT-бонусами за период")

    allure.dynamic.parameter("Пользователей в выборке", result.sample_users_count)
    allure.dynamic.parameter("Дней с VISIT-бонусами", result.bonus_days_count)
    allure.dynamic.parameter("Дней с посещениями", result.visit_days_count)
    allure.dynamic.parameter("Нарушений найдено", len(result.violations))

    report = build_visit_bonus_coverage_report(result)

    if not result.violations:
        allure.attach(report, name="Результат", attachment_type=allure.attachment_type.TEXT)
        return

    with allure.step(f"Сформировать отчет о {len(result.violations)} нарушениях"):
        print("\n" + report)
        allure.attach(
            report,
            name="Посещения без VISIT-бонуса",
            attachment_type=allure.attachment_type.TEXT,
        )

    first = result.violations[0]
    assert len(result.violations) == 0, (
        f"Найдено {len(result.violations)} дней с посещением клуба без VISIT-бонуса. "
        f"Первый: user={first.user_id}, date={first.date}"
    )