"""Текстовые и HTML report builders для backend-check сценариев trainings."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from html import escape
import json
import re

from src.services.backend_checks.trainings_checks_service import (
    PersonalTrainingConsistencyCheckResult,
    PersonalTrainingConsistencyRecord,
    RULE_TITLES,
)
from src.utils.allure_html import HTML_CSS, html_table

_COL_HEADER = (
    f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} "
    f"{'SP Type':<11} {'Train Type':<12} "
    f"{'Tickets':<8} {'Hist':<5} {'Sessions':<9} {'CnlNR':<7} "
    f"{'Status':<7} {'Manual Hist ID':<26} {'Manual Change':<15} "
    f"{'Manual At':<22} {'Updated At':<22} {'Created At':<22}"
)
_COL_SEP = "=" * 330
_REPORT_HTML_CSS = HTML_CSS + """
<style>
.pt-compact{white-space:nowrap}
.pt-groups-nav{margin:0 0 14px;font-size:12px}
.pt-groups-nav a{display:inline-block;margin:0 8px 6px 0;color:#24527a;text-decoration:none}
.pt-group{margin:18px 0 28px;page-break-after:always;border:1px solid #d9e2ec;border-radius:6px;overflow:hidden}
.pt-group:last-child{page-break-after:auto}
.pt-group summary{cursor:pointer;padding:10px 14px;background:#f4f7fb;color:#2c3e50;font-weight:bold}
.pt-group summary:hover{background:#eaf1f8}
.pt-group summary::-webkit-details-marker{display:none}
.pt-group-body{padding:10px 14px 0;overflow-x:auto}
.pt-group-count{color:#687887;font-weight:normal}
.pt-summary{margin:0 0 14px}
.pt-summary h3{margin:0 0 6px;font-size:13px;color:#2c3e50}
.pt-summary table{margin-bottom:10px}
.pt-summary td,.pt-summary th{padding:3px 10px;font-size:12px}
.pt-rule-summary{margin:0 0 14px}
.pt-rule-summary h3{margin:0 0 6px;font-size:13px;color:#2c3e50}
.pt-rule-summary table{margin-bottom:10px}
.pt-rule-summary td,.pt-rule-summary th{padding:3px 10px;font-size:12px}
.pt-date-filters{margin:0 0 14px}
.pt-date-filters h3{margin:0 0 6px;font-size:13px;color:#2c3e50}
.pt-date-filters table{margin-bottom:10px}
.pt-date-filters td,.pt-date-filters th{padding:3px 10px;font-size:12px}
.pt-rule{margin:18px 0 28px}
.pt-rule h3{margin:0 0 8px;font-size:14px;color:#2c3e50}
</style>
"""

_SUMMARY_TRAINING_TYPES = ("duo", "mg", "pt", "trio")


def _fmt_date(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt != "N/A" else "N/A"


def _fmt_text(value) -> str:
    return str(value) if value not in (None, "") else "N/A"


def _truncate(value, max_len: int = 30) -> str:
    text = _fmt_text(value)
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _html_compact(value) -> str:
    return f'<span class="pt-compact">{escape(_fmt_text(value))}</span>'


def _html_cell(value) -> str:
    return escape(_fmt_text(value))


def _train_type_slug(value) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", _fmt_text(value).lower()).strip("-")
    return slug or "n-a"


def _latest_updated_at(records: list[PersonalTrainingConsistencyRecord]) -> str:
    dated_records = [record.updated_at for record in records if record.updated_at != "N/A"]
    if not dated_records:
        return "N/A"
    return _fmt_date(max(dated_records))


def _updated_at_sort_value(record: PersonalTrainingConsistencyRecord):
    return record.updated_at if record.updated_at != "N/A" else datetime.min


def _sort_records_by_updated_at_desc(
    records: list[PersonalTrainingConsistencyRecord],
) -> list[PersonalTrainingConsistencyRecord]:
    return sorted(records, key=_updated_at_sort_value, reverse=True)


def _build_training_type_summary(records: list[PersonalTrainingConsistencyRecord]) -> str:
    by_type: dict[str, list[PersonalTrainingConsistencyRecord]] = defaultdict(list)
    for record in records:
        by_type[_fmt_text(record.service_product_training_type).lower()].append(record)

    rows = [
        [train_type, str(len(by_type[train_type])), _latest_updated_at(by_type[train_type])]
        for train_type in _SUMMARY_TRAINING_TYPES
    ]
    return (
        '<section class="pt-summary">'
        "<h3>Summary</h3>"
        + html_table(["Train Type", "Errors", "Last updated_at"], rows, right_cols=(1,))
        + "</section>"
    )


def _build_rule_summary(records: list[PersonalTrainingConsistencyRecord]) -> str:
    counts = {
        rule_id: sum(1 for record in records if getattr(record, rule_id))
        for rule_id in RULE_TITLES
    }
    rows = [[title, str(counts[rule_id])] for rule_id, title in RULE_TITLES.items()]
    return (
        '<section class="pt-rule-summary">'
        "<h3>Rule Summary</h3>"
        + html_table(["Rule", "Errors"], rows, right_cols=(1,))
        + "</section>"
    )


def _offset_to_label(offset) -> str:
    return f"{offset.years}y {offset.months}m {offset.days}d"


def _build_date_filter_summary(
    *,
    result: PersonalTrainingConsistencyCheckResult | None = None,
    date_filter_summary: dict[str, object] | None = None,
) -> str:
    if date_filter_summary is None and result is not None:
        date_filter_summary = {
            "specific_usp_id": result.specific_usp_id,
            "updated_from": result.updated_from,
            "created_from": result.created_from,
            "updated_offset": _offset_to_label(result.updated_offset),
            "created_offset": _offset_to_label(result.created_offset),
        }
    if date_filter_summary is None:
        return ""

    specific_usp_id = date_filter_summary.get("specific_usp_id")
    updated_from = date_filter_summary.get("updated_from")
    created_from = date_filter_summary.get("created_from")
    updated_offset = date_filter_summary.get("updated_offset", "N/A")
    created_offset = date_filter_summary.get("created_offset", "N/A")

    rows = [
        [
            _html_cell("specific_usp_id"),
            _html_cell(f"specific USP record: {specific_usp_id}" if specific_usp_id else "not set"),
        ],
        [
            _html_cell("updated_at"),
            _html_cell(
                "no filter" if updated_from is None else f">= {_fmt_date(updated_from)} (offset: {updated_offset})"
            ),
        ],
        [
            _html_cell("created_at"),
            _html_cell(
                "no filter" if created_from is None else f">= {_fmt_date(created_from)} (offset: {created_offset})"
            ),
        ],
    ]
    return (
        '<section class="pt-date-filters">'
        "<h3>Selection Criteria / Date Filters</h3>"
        + html_table(["Field", "Criteria"], rows)
        + "</section>"
    )


def _result_to_line(record: PersonalTrainingConsistencyRecord) -> str:
    return (
        f"{record.idx:<4} {record.usp_id:<26} {record.user_id:<26} "
        f"{str(record.initial_count):<5} {str(record.count):<6} "
        f"{_truncate(record.service_product_type, 11):<11} "
        f"{_truncate(record.service_product_training_type, 12):<12} "
        f"{str(record.tickets_count):<8} {str(record.hist_count):<5} "
        f"{str(record.sessions_count):<9} {str(record.cancel_not_restored):<7} "
        f"{record.status:<7} {str(record.manual_count_update_id or 'N/A'):<26} "
        f"{record.manual_count_change:<15} {_fmt_date(record.manual_count_update_at):<22} "
        f"{_fmt_date(record.updated_at):<22} {_fmt_date(record.created_at):<22}"
    )


def build_personal_trainings_text_table(records: list[PersonalTrainingConsistencyRecord]) -> str:
    """Строит текстовую таблицу результатов."""
    lines = [_COL_HEADER, _COL_SEP] + [
        _result_to_line(record) for record in _sort_records_by_updated_at_desc(records)
    ]
    return "\n".join(lines)


def build_personal_trainings_html_table(
    records: list[PersonalTrainingConsistencyRecord],
    *,
    title: str,
) -> str:
    """Строит HTML-таблицу результатов."""
    headers = [
        "№",
        "USP ID",
        "User ID",
        "Init",
        "Count",
        "SP Type",
        "Train Type",
        "Tickets",
        "Hist",
        "Sessions",
        "CnlNR",
        "Status",
        "Manual Hist ID",
        "Manual Change",
        "Manual At",
        "Updated At",
        "Created At",
    ]
    rows = [
        [
            str(record.idx),
            record.usp_id,
            record.user_id,
            str(record.initial_count),
            str(record.count),
            _html_compact(record.service_product_type),
            _html_compact(record.service_product_training_type),
            str(record.tickets_count),
            str(record.hist_count),
            str(record.sessions_count),
            str(record.cancel_not_restored),
            record.status,
            str(record.manual_count_update_id or "N/A"),
            record.manual_count_change,
            _fmt_date(record.manual_count_update_at),
            _fmt_date(record.updated_at),
            _fmt_date(record.created_at),
        ]
        for record in _sort_records_by_updated_at_desc(records)
    ]
    return _REPORT_HTML_CSS + f"<h2>{escape(title)}</h2>" + html_table(headers, rows)


def build_personal_trainings_grouped_html_report(
    records: list[PersonalTrainingConsistencyRecord],
    *,
    title: str,
    result: PersonalTrainingConsistencyCheckResult | None = None,
    date_filter_summary: dict[str, object] | None = None,
) -> str:
    """Строит HTML-отчёт с группировкой: правило ошибки -> serviceproducts.trainingType."""
    rule_groups = {
        rule_id: [record for record in records if getattr(record, rule_id)]
        for rule_id in RULE_TITLES
    }
    nav_links = "".join(
        f'<a href="#rule-{_train_type_slug(rule_id)}">{escape(title)} ({len(rule_records)})</a>'
        for rule_id, title in RULE_TITLES.items()
        for rule_records in [rule_groups[rule_id]]
        if rule_records
    )
    sections = []
    headers = [
        "№",
        "SP Type",
        "USP ID",
        "User ID",
        "Init",
        "Count",
        "Expected",
        "Actual",
        "Tickets",
        "Hist",
        "Sessions",
        "CnlNR",
        "Manual Hist ID",
        "Manual Change",
        "Manual At",
        "Updated At",
        "Created At",
    ]

    for rule_id, rule_title in RULE_TITLES.items():
        rule_records = rule_groups[rule_id]
        if not rule_records:
            continue

        train_groups: dict[str, list[PersonalTrainingConsistencyRecord]] = defaultdict(list)
        for record in rule_records:
            train_groups[_fmt_text(record.service_product_training_type)].append(record)

        train_sections = []
        for train_type, group_records in sorted(train_groups.items(), key=lambda item: item[0].lower()):
            rows = [
                [
                    str(record.idx),
                    _html_compact(record.service_product_type),
                    _html_cell(record.usp_id),
                    _html_cell(record.user_id),
                    _html_cell(record.initial_count),
                    _html_cell(record.count),
                    _html_cell(getattr(record, f"{rule_id}_expected")),
                    _html_cell(getattr(record, f"{rule_id}_actual")),
                    _html_cell(record.tickets_count),
                    _html_cell(record.hist_count),
                    _html_cell(record.sessions_count),
                    _html_cell(record.cancel_not_restored),
                    _html_cell(record.manual_count_update_id or "N/A"),
                    _html_cell(record.manual_count_change),
                    _html_cell(_fmt_date(record.manual_count_update_at)),
                    _html_cell(_fmt_date(record.updated_at)),
                    _html_cell(_fmt_date(record.created_at)),
                ]
                for record in _sort_records_by_updated_at_desc(group_records)
            ]
            summary = (
                f'<summary>Train Type: {escape(train_type)} '
                f'<span class="pt-group-count">({len(group_records)})</span></summary>'
            )
            train_sections.append(
                f'<details class="pt-group" id="rule-{_train_type_slug(rule_id)}-train-type-{_train_type_slug(train_type)}">'
                + summary
                + '<div class="pt-group-body">'
                + html_table(headers, rows)
                + "</div></details>"
            )

        sections.append(
            f'<section class="pt-rule" id="rule-{_train_type_slug(rule_id)}">'
            + f"<h3>{escape(rule_title)} ({len(rule_records)})</h3>"
            + "".join(train_sections)
            + "</section>"
        )

    return (
        _REPORT_HTML_CSS
        + f"<h2>{escape(title)}</h2>"
        + _build_date_filter_summary(result=result, date_filter_summary=date_filter_summary)
        + _build_rule_summary(records)
        + _build_training_type_summary(records)
        + f'<nav class="pt-groups-nav">{nav_links}</nav>'
        + "".join(sections)
    )


def build_personal_trainings_summary(
    result: PersonalTrainingConsistencyCheckResult,
    *,
    backend_env: str,
    period_label: str,
) -> str:
    """Формирует summary по результату проверки."""
    return (
        f"Окружение: {backend_env.upper()}\n"
        f"Период: {period_label}\n"
        f"Всего: {len(result.records)}  OK: {result.ok_count}  FAIL: {result.failed_count}\n"
        f"Обычные расхождения: {len(result.regular_failed_records)}  "
        f"После ручного изменения count: {len(result.manual_update_failed_records)}"
    )


def build_personal_trainings_json(result: PersonalTrainingConsistencyCheckResult) -> str:
    """Формирует JSON со всеми проверенными записями."""
    serializable = []
    for record in result.records:
        serializable.append(
            {
                "idx": record.idx,
                "usp_id": record.usp_id,
                "user_id": record.user_id,
                "initial_count": record.initial_count,
                "count": record.count,
                "tickets_count": record.tickets_count,
                "hist_count": record.hist_count,
                "sessions_count": record.sessions_count,
                "cancel_not_restored": record.cancel_not_restored,
                "status": record.status,
                "updated_at": _fmt_date(record.updated_at),
                "created_at": _fmt_date(record.created_at),
            }
        )
    return json.dumps(serializable, indent=2, ensure_ascii=False)
