"""
Проверка корректности поля accessType при входе клиента по абонементу.

Бизнес-правило: вход по нерекуррентному абонементу (subscriptions.isRecurrent=false)
должен фиксироваться с accesscontrols.accessType='subscription'.
Подписки (isRecurrent=true) этим тестом не охватываются.
"""

import pytest
import allure

from src.services.backend_checks.payments_checks_service import (
    run_subscription_access_type_check,
)
from src.services.reporting.payments_text_reports import (
    build_subscription_access_type_reports,
)

SAMPLE_SIZE = 300


def _pct(part: int, total: int) -> str:
    return f"{part / total * 100:.1f}%" if total else "—"


def _club_label(result, club_id) -> str:
    name = result.club_name_map.get(club_id, "неизвестный клуб") if club_id else "неизвестный клуб"
    return f"{name} ({club_id})" if club_id else name


def _plan_label(result, plan_id) -> str:
    plan = result.plan_map.get(plan_id)
    if not plan:
        return f"неизвестный план ({plan_id})"
    return f"{plan.get('name', '—')} ({plan_id})"


@pytest.mark.backend
@allure.feature("Access Control")
@allure.story("Subscription entry validation")
@allure.title("При входе по абонементу accesscontrols.accessType=subscription")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "accesscontrols", "subscription", "access")
def test_subscription_entry_access_type(db, period_days):
    """
    Для выборки пользователей с активными нерекуррентными абонементами
    проверяет, что все их входы в клуб (type=enter, без err, без staff)
    в период действия абонемента имеют accessType='subscription'.
    """
    with allure.step("Вычислить нарушения accessType по абонементам"):
        result = run_subscription_access_type_check(
            db=db,
            period_days=period_days,
            sample_size=SAMPLE_SIZE,
        )

    if result.plans_count == 0:
        pytest.skip("Нет нерекуррентных планов абонементов в базе")
    if result.sampled_subscriptions_count == 0:
        pytest.skip(f"Нет активных абонементов за последние {period_days} дней")
    if result.entries_count == 0:
        pytest.skip("Нет входов в клуб у абонентов за период")

    allure.dynamic.parameter("Нерекуррентных планов", result.plans_count)
    allure.dynamic.parameter("Абонементов в выборке", result.sampled_subscriptions_count)
    allure.dynamic.parameter("Пользователей в выборке", result.sampled_users_count)
    allure.dynamic.parameter("Входов в выборке", result.entries_count)
    allure.dynamic.parameter("Входов в окне абонемента", result.entries_in_window_count)
    allure.dynamic.parameter("Вне окна абонемента", result.outside_window_count)
    allure.dynamic.parameter("Планов без clubId", len(result.no_clubid_entries))
    allure.dynamic.parameter("Нарушений", len(result.violations))

    reports = build_subscription_access_type_reports(result)

    with allure.step("Приложить summary и агрегаты"):
        print("\n=== SUMMARY ===\n" + reports["summary_text"])
        print("\n=== BY CLUB ===\n" + reports["by_club_text"])
        print("\n=== BY SUBSCRIPTION PLAN ===\n" + reports["by_plan_text"])
        allure.attach(reports["summary_text"], name="Summary", attachment_type=allure.attachment_type.TEXT)
        allure.attach(reports["summary_html"], name="Summary (HTML)", attachment_type=allure.attachment_type.HTML)
        allure.attach(reports["by_club_text"], name="By Club", attachment_type=allure.attachment_type.TEXT)
        allure.attach(reports["by_club_html"], name="By Club (HTML)", attachment_type=allure.attachment_type.HTML)
        allure.attach(
            reports["by_plan_text"],
            name="By Subscription Plan",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            reports["by_plan_html"],
            name="By Subscription Plan (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )

    if reports["violations_text"]:
        with allure.step("Приложить детализацию нарушений"):
            print("\n=== НАРУШЕНИЯ ПО КЛУБАМ ===\n" + reports["violations_text"])
            allure.attach(
                reports["violations_text"],
                name="Нарушения по клубам",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                reports["violations_html"],
                name="Нарушения по клубам (HTML)",
                attachment_type=allure.attachment_type.HTML,
            )

    if reports["no_clubid_text"]:
        with allure.step("Приложить диагностический блок по планам без clubId"):
            print("\n== Абонементы без clubId ===\n" + reports["no_clubid_text"])
            allure.attach(
                reports["no_clubid_text"],
                name="Абонементы без clubId",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                reports["no_clubid_html"],
                name="Планы без clubId (HTML)",
                attachment_type=allure.attachment_type.HTML,
            )

    assert len(result.violations) == 0, (
        f"Найдено {len(result.violations)} входов по абонементу с accessType != 'subscription' "
        f"({_pct(len(result.violations), result.entries_in_window_count)} из {result.entries_in_window_count} входов в окне). "
        f"Первый: entry_id={result.violations[0].entry_id}, "
        f"клуб={_club_label(result, result.violations[0].club_id)}, "
        f"план={_plan_label(result, result.violations[0].plan_id)}, "
        f"accessType='{result.violations[0].access_type or '—'}'"
    )
