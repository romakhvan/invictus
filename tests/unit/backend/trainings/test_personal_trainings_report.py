from datetime import datetime

from src.services.backend_checks.trainings_checks_service import PersonalTrainingConsistencyRecord
from src.services.reporting.trainings_text_reports import (
    build_personal_trainings_grouped_html_report,
    build_personal_trainings_text_table,
)


def _record(
    idx: int,
    training_type: str,
    title: str,
    updated_at="N/A",
) -> PersonalTrainingConsistencyRecord:
    return PersonalTrainingConsistencyRecord(
        idx=idx,
        usp_id=f"usp-{idx}",
        user_id=f"user-{idx}",
        initial_count=10,
        count=9,
        tickets_count=8,
        hist_count=9,
        sessions_count=1,
        cancel_not_restored=0,
        status="FAIL",
        updated_at=updated_at,
        created_at="N/A",
        service_product_title=title,
        service_product_type="SPECIALIST",
        service_product_training_type=training_type,
        tickets_mismatch=True,
        tickets_mismatch_expected="count=9",
        tickets_mismatch_actual="activeTickets=8",
    )


def test_grouped_html_report_omits_title_and_redundant_columns():
    record = _record(
        idx=1,
        training_type="trial",
        title="Long <Personal Training> Title With Many Words",
    )

    html = build_personal_trainings_grouped_html_report([record], title="Расхождения")
    text = build_personal_trainings_text_table([record])

    assert "SP Type" in html
    assert "<th>Title</th>" not in html
    assert "Status" not in html
    assert html.count("<th>Train Type</th>") == 1
    assert "pt-title" not in html
    assert "Long &lt;Personal Training&gt; Title With Many Words" not in html
    assert "Title" not in text
    assert "Long <Personal Training> Title With Many Words" not in text


def test_grouped_html_report_groups_records_by_training_type_and_puts_sp_type_second():
    html = build_personal_trainings_grouped_html_report(
        [
            _record(idx=1, training_type="trial", title="Trial product"),
            _record(idx=2, training_type="personal", title="Personal product"),
        ],
        title="Расхождения",
    )

    assert 'id="rule-tickets-mismatch-train-type-personal"' in html
    assert 'id="rule-tickets-mismatch-train-type-trial"' in html
    assert "Personal product" not in html
    assert "Trial product" not in html
    assert html.index("<th>№</th>") < html.index("<th>SP Type</th>") < html.index("<th>USP ID</th>")


def test_grouped_html_report_uses_collapsible_sections():
    html = build_personal_trainings_grouped_html_report(
        [_record(idx=1, training_type="trial", title="Trial product")],
        title="Расхождения",
    )

    assert '<details class="pt-group" id="rule-tickets-mismatch-train-type-trial">' in html
    assert "<summary>" in html
    assert "Train Type: trial" in html
    assert "</summary>" in html
    assert "</details>" in html


def test_grouped_html_report_has_summary_for_expected_training_types():
    html = build_personal_trainings_grouped_html_report(
        [
            _record(
                idx=1,
                training_type="duo",
                title="Older duo",
                updated_at=datetime(2026, 4, 20, 10, 0, 0),
            ),
            _record(
                idx=2,
                training_type="duo",
                title="Latest duo",
                updated_at=datetime(2026, 4, 23, 12, 30, 0),
            ),
            _record(
                idx=3,
                training_type="pt",
                title="Personal",
                updated_at=datetime(2026, 4, 21, 9, 15, 0),
            ),
        ],
        title="Расхождения",
    )

    assert '<section class="pt-summary">' in html
    assert "<h3>Summary</h3>" in html
    assert "<td>duo</td><td class=\"r\">2</td><td>2026-04-23 12:30:00</td>" in html
    assert "<td>mg</td><td class=\"r\">0</td><td>N/A</td>" in html
    assert "<td>pt</td><td class=\"r\">1</td><td>2026-04-21 09:15:00</td>" in html
    assert "<td>trio</td><td class=\"r\">0</td><td>N/A</td>" in html
    assert html.index("<h3>Summary</h3>") < html.index('<nav class="pt-groups-nav">')


def test_rule_grouped_html_report_shows_rule_sections_and_expected_actual():
    record = _record(idx=1, training_type="trio", title="TRIO <Product>")
    record = record.__class__(
        **{
            **record.__dict__,
            "tickets_mismatch": True,
            "tickets_mismatch_expected": "count=3",
            "tickets_mismatch_actual": "activeTickets=4",
            "history_count_mismatch": True,
            "history_count_mismatch_expected": "count=3",
            "history_count_mismatch_actual": "hist=2",
        }
    )

    html = build_personal_trainings_grouped_html_report([record], title="Расхождения")

    assert 'id="rule-tickets-mismatch"' in html
    assert 'id="rule-history-count-mismatch"' in html
    assert "count != active trainingtickets" in html
    assert "count != latest history currentCount" in html
    assert "count=3" in html
    assert "activeTickets=4" in html
    assert "hist=2" in html
    assert "TRIO &lt;Product&gt;" not in html
    assert "<th>Expected</th>" in html
    assert "<th>Actual</th>" in html
    assert "Status" not in html
    assert html.count("<th>Train Type</th>") == 1


def test_rule_grouped_html_report_has_rule_summary_counts():
    tickets_record = _record(idx=1, training_type="trio", title="Ticket mismatch")
    tickets_record = tickets_record.__class__(
        **{
            **tickets_record.__dict__,
            "tickets_mismatch": True,
            "tickets_mismatch_expected": "count=3",
            "tickets_mismatch_actual": "activeTickets=4",
        }
    )
    sessions_record = _record(idx=2, training_type="pt", title="Session mismatch")
    sessions_record = sessions_record.__class__(
        **{
            **sessions_record.__dict__,
            "tickets_mismatch": False,
            "tickets_mismatch_expected": "N/A",
            "tickets_mismatch_actual": "N/A",
            "sessions_usage_mismatch": True,
            "sessions_usage_mismatch_expected": "initial-count=10-3",
            "sessions_usage_mismatch_actual": "sessions+cancel=6+0",
        }
    )

    html = build_personal_trainings_grouped_html_report(
        [tickets_record, sessions_record],
        title="Расхождения",
    )

    assert '<section class="pt-rule-summary">' in html
    assert "<td>count != active trainingtickets</td><td class=\"r\">1</td>" in html
    assert "<td>count != latest history currentCount</td><td class=\"r\">0</td>" in html
    assert "<td>active trainingtickets != latest history currentCount</td><td class=\"r\">0</td>" in html
    assert (
        "<td>trainingsessions + cancel_not_restored != initialCount - count</td>"
        "<td class=\"r\">1</td>"
    ) in html


def test_grouped_html_report_shows_date_selection_criteria_before_rule_summary():
    html = build_personal_trainings_grouped_html_report(
        [_record(idx=1, training_type="pt", title="Personal")],
        title="Расхождения",
        date_filter_summary={
            "specific_usp_id": None,
            "updated_from": None,
            "created_from": datetime(2026, 1, 24, 15, 30, 45),
            "updated_offset": "0y 0m 0d",
            "created_offset": "0y 3m 0d",
        },
    )

    assert '<section class="pt-date-filters">' in html
    assert "<h3>Selection Criteria / Date Filters</h3>" in html
    assert "<td>specific_usp_id</td><td>not set</td>" in html
    assert "<td>updated_at</td><td>no filter</td>" in html
    assert "<td>created_at</td><td>&gt;= 2026-01-24 15:30:45 (offset: 0y 3m 0d)</td>" in html
    assert html.index('<section class="pt-date-filters">') < html.index('<section class="pt-rule-summary">')


def test_reports_sort_rows_by_updated_at_descending():
    older = _record(
        idx=1,
        training_type="pt",
        title="Older product",
        updated_at=datetime(2026, 4, 20, 10, 0, 0),
    )
    latest = _record(
        idx=2,
        training_type="pt",
        title="Latest product",
        updated_at=datetime(2026, 4, 24, 9, 0, 0),
    )
    no_date = _record(idx=3, training_type="pt", title="No date product", updated_at="N/A")

    html = build_personal_trainings_grouped_html_report(
        [older, no_date, latest],
        title="Расхождения",
    )
    text = build_personal_trainings_text_table([older, no_date, latest])

    assert html.index("usp-2") < html.index("usp-1") < html.index("usp-3")
    assert text.index("usp-2") < text.index("usp-1") < text.index("usp-3")
