"""Checks visits pricing rules for configured club types."""

from collections import Counter, defaultdict

import allure
import pytest

from src.services.backend_checks.payments_checks_service import run_visit_price_check
from src.utils.allure_html import HTML_CSS, html_kv, html_table


def _fmt_dt(value) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S") if value else "-"


def _fmt_value(value) -> str:
    return "-" if value is None else str(value)


def _build_summary_text(result) -> str:
    return "\n".join(
        [
            f"Period: last {result.period_days} days",
            f"Checked records: {result.checked_transactions_count}",
            f"Visits transactions after join: {result.transactions_count}",
            "Configured pricing: club-specific rules + fallback GO=5000, Girls=10000",
            f"Violations: {len(result.violations)}",
        ]
    )


def _build_summary_html(result) -> str:
    return HTML_CSS + "<h2>Summary</h2>" + html_kv(
        [
            ("Period", f"last {result.period_days} days"),
            ("Checked records", result.checked_transactions_count),
            ("Visits transactions after join", result.transactions_count),
            ("Configured pricing", "club-specific rules + fallback GO=5000, Girls=10000"),
            ("Violations", len(result.violations)),
        ]
    )


def _build_violations_text(result) -> str:
    if not result.violations:
        return "No violations found"

    lines = []
    grouped = defaultdict(list)
    for violation in sorted(result.violations, key=lambda item: (item.club_name, item.created_at or result.since)):
        grouped[violation.club_name].append(violation)

    for club_name, violations in grouped.items():
        lines.append(f"{club_name} ({len(violations)})")
        for violation in violations[:20]:
            lines.append(
                " | ".join(
                    [
                        _fmt_dt(violation.created_at),
                        f"tx_id={violation.tx_id}",
                        f"clubId={violation.club_id}",
                        f"clubType={violation.club_type}",
                        f"expected={violation.expected_total_price}",
                        f"actual={violation.actual_total_price}",
                        f"unitPrice={violation.expected_unit_price}",
                        f"visitsCount={violation.visits_count}",
                        f"clubServicePrice={violation.clubservice_price}",
                        f"clubServiceId={violation.club_service_id}",
                        f"userId={violation.user_id}",
                    ]
                )
            )
        if len(violations) > 20:
            lines.append(f"... and {len(violations) - 20} more violations for this club")
        lines.append("")
    return "\n".join(lines).strip()


def _build_by_club_html(result) -> str:
    stats = defaultdict(lambda: {"records": 0, "violations": 0, "club_type": "-"})
    for violation in result.violations:
        key = (violation.club_name, _fmt_value(violation.club_id))
        stats[key]["records"] += 1
        stats[key]["violations"] += 1
        stats[key]["club_type"] = violation.club_type or "-"

    rows = [
        (club_name, club_id, stat["club_type"], stat["records"], stat["violations"])
        for (club_name, club_id), stat in sorted(
            stats.items(),
            key=lambda item: (-item[1]["violations"], item[0][0], item[0][1]),
        )
    ]
    if not rows:
        rows = [("No violations", "-", "GO/Girls", result.checked_transactions_count, 0)]
    return HTML_CSS + "<h2>By Club</h2>" + html_table(
        ["Club", "clubId", "clubType", "Records", "Violations"],
        rows,
        right_cols=(3, 4),
    )


def _build_mismatch_patterns_html(result) -> str:
    counter = Counter(
        (
            _fmt_value(item.club_type),
            _fmt_value(item.expected_total_price),
            _fmt_value(item.actual_total_price),
        )
        for item in result.violations
    )
    rows = [
        (club_type, expected, actual, count)
        for (club_type, expected, actual), count in counter.most_common()
    ]
    if not rows:
        rows = [("GO/Girls", "configured", "-", 0)]
    return HTML_CSS + "<h2>Mismatch Patterns</h2>" + html_table(
        ["clubType", "Expected", "Actual", "Violations"],
        rows,
        right_cols=(3,),
    )


def _build_latest_violations_html(result) -> str:
    rows = [
        (
            _fmt_dt(violation.created_at),
            violation.tx_id,
            violation.club_name,
            _fmt_value(violation.club_id),
            _fmt_value(violation.club_type),
            _fmt_value(violation.club_service_id),
            _fmt_value(violation.user_id),
            violation.expected_total_price,
            violation.actual_total_price,
            violation.visits_count,
        )
        for violation in sorted(
            result.violations,
            key=lambda item: item.created_at or result.since,
            reverse=True,
        )[:10]
    ]
    if not rows:
        rows = [('-', '-', 'No violations', '-', 'GO/Girls', '-', '-', '-', '-', '-')]
    return HTML_CSS + "<h2>Latest Violations</h2>" + html_table(
        ["Date", "tx_id", "Club", "clubId", "clubType", "clubServiceId", "userId", "Expected", "Actual", "Visits"],
        rows,
        right_cols=(7, 8, 9),
    )


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Visits pricing")
@allure.title("Visits are purchased at club-specific prices")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "visits", "price", "go", "girls", "fitness")
def test_visits_are_purchased_at_configured_prices(db, period_days):
    """
    For successful visits transactions, follows paidFor.visits.clubServiceId ->
    clubservices.club -> clubs.type and checks configured per-visit prices.
    Specific clubs have priority; otherwise fallback rules are GO=5000 and Girls=10000.
    """
    with allure.step(f"Check visits prices by club rules for the last {period_days} days"):
        result = run_visit_price_check(db=db, period_days=period_days)

    if result.transactions_count == 0:
        pytest.skip(f"No successful visits transactions found for the last {period_days} days")
    if result.checked_transactions_count == 0:
        pytest.skip(
            f"No successful visits transactions matched configured club or club-type rules for the last {period_days} days"
        )

    allure.dynamic.parameter("Sample period", f"last {period_days} days")
    allure.dynamic.parameter("Checked records", result.checked_transactions_count)
    allure.dynamic.parameter("Visits transactions after join", result.transactions_count)
    allure.dynamic.parameter("Checked configured transactions", result.checked_transactions_count)
    allure.dynamic.parameter("Violations", len(result.violations))

    summary_text = _build_summary_text(result)
    summary_html = _build_summary_html(result)
    violations_text = _build_violations_text(result)
    by_club_html = _build_by_club_html(result)
    mismatch_patterns_html = _build_mismatch_patterns_html(result)
    latest_violations_html = _build_latest_violations_html(result)

    with allure.step("Attach summary and analytics"):
        allure.attach(summary_text, name="Summary", attachment_type=allure.attachment_type.TEXT)
        allure.attach(summary_html, name="Summary (HTML)", attachment_type=allure.attachment_type.HTML)
        allure.attach(by_club_html, name="By Club (HTML)", attachment_type=allure.attachment_type.HTML)
        allure.attach(
            mismatch_patterns_html,
            name="Mismatch Patterns (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )

    if result.violations:
        with allure.step("Attach violation details"):
            allure.attach(
                violations_text,
                name="Violations by club",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                latest_violations_html,
                name="Latest Violations (HTML)",
                attachment_type=allure.attachment_type.HTML,
            )
        print("\n=== SUMMARY ===\n" + summary_text)
        print("\n=== VIOLATIONS ===\n" + violations_text)

    latest_violation = (
        max(result.violations, key=lambda item: item.created_at or result.since)
        if result.violations
        else None
    )
    assert len(result.violations) == 0, (
        f"Found {len(result.violations)} visits transactions with incorrect totalPrice "
        f"out of {result.checked_transactions_count} checked records for the last {period_days} days. "
        f"Latest mismatch: tx_id={latest_violation.tx_id}, "
        f"date={_fmt_dt(latest_violation.created_at)}, "
        f"club={latest_violation.club_name}, "
        f"clubId={latest_violation.club_id}, "
        f"clubType={latest_violation.club_type}, "
        f"expected={latest_violation.expected_total_price} "
        f"({latest_violation.expected_unit_price} x visitsCount={latest_violation.visits_count}), "
        f"actual={latest_violation.actual_total_price}, "
        f"clubServiceId={latest_violation.club_service_id}, "
        f"userId={latest_violation.user_id}"
    )
