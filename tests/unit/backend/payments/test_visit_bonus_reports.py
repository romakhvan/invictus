from datetime import date, datetime

from src.services.backend_checks.payments_checks_service import (
    VisitBonusAccrualCheckResult,
    VisitBonusCoverageCheckResult,
    VisitBonusCoverageViolation,
    VisitBonusDuplicateDayViolation,
    VisitBonusMissingVisitViolation,
)
from src.services.reporting.payments_text_reports import (
    build_visit_bonus_accrual_reports,
    build_visit_bonus_coverage_report,
)


def test_visit_bonus_accrual_reports_include_success_summary_context():
    result = VisitBonusAccrualCheckResult(
        period_days=7,
        since=datetime(2026, 4, 16, 0, 0, 0),
        sample_size=500,
        bonus_records_count=12,
        access_entries_count=12,
        duplicate_days=[],
        missing_visit_bonuses=[],
    )

    reports = build_visit_bonus_accrual_reports(result)

    assert "Итог проверки VISIT-бонусов" in reports["summary_text"]
    assert "Период: последние 7 дней" in reports["summary_text"]
    assert "Проверено VISIT-бонусов: 12" in reports["summary_text"]
    assert "Валидных входов найдено: 12" in reports["summary_text"]
    assert "Нарушений: 0" in reports["summary_text"]
    assert "Последняя ошибочная запись" not in reports["summary_text"]
    assert reports["violations_text"] == ""
    assert reports["expected_vs_actual_text"] == ""


def test_visit_bonus_accrual_reports_show_latest_missing_visit_and_expected_actual():
    result = VisitBonusAccrualCheckResult(
        period_days=14,
        since=datetime(2026, 4, 9, 0, 0, 0),
        sample_size=500,
        bonus_records_count=2,
        access_entries_count=1,
        duplicate_days=[
            VisitBonusDuplicateDayViolation(
                user_id="user-1",
                date=date(2026, 4, 20),
                bonus_ids=["bonus-old-1", "bonus-old-2"],
            )
        ],
        missing_visit_bonuses=[
            VisitBonusMissingVisitViolation(
                bonus_id="bonus-old",
                user_id="user-2",
                amount=500,
                time=datetime(2026, 4, 18, 9, 0, 0),
            ),
            VisitBonusMissingVisitViolation(
                bonus_id="bonus-new",
                user_id="user-3",
                amount=500,
                time=datetime(2026, 4, 22, 10, 30, 0),
            ),
        ],
    )

    reports = build_visit_bonus_accrual_reports(result)

    assert "Нарушений: 3" in reports["summary_text"]
    assert "Последняя ошибочная запись: 2026-04-22 10:30:00" in reports["summary_text"]
    assert "bonus_id=bonus-new" in reports["summary_text"]
    assert "expected=валидный вход accesscontrols" in reports["summary_text"]
    assert "actual=вход не найден" in reports["summary_text"]
    assert "Дубли VISIT-бонусов за день (1)" in reports["violations_text"]
    assert "VISIT-бонусы без посещения (2)" in reports["violations_text"]
    assert "bonus_id=bonus-new" in reports["expected_vs_actual_text"]
    assert "expected=валидный вход accesscontrols" in reports["expected_vs_actual_text"]
    assert "actual=вход не найден" in reports["expected_vs_actual_text"]


def test_visit_bonus_coverage_report_includes_accesscontrol_id_and_expected_actual():
    result = VisitBonusCoverageCheckResult(
        period_days=7,
        since=datetime(2026, 4, 16, 0, 0, 0),
        sample_users_limit=200,
        sample_users_count=1,
        bonus_days_count=0,
        visit_days_count=1,
        violations=[
            VisitBonusCoverageViolation(
                user_id="user-1",
                date=date(2026, 4, 23),
                accesscontrol_id="access-1",
            )
        ],
    )

    report = build_visit_bonus_coverage_report(result)

    assert "accesscontrolId=access-1" in report
    assert "user=user-1" in report
    assert "expected=VISIT-бонус" in report
    assert "actual=нет бонуса" in report
