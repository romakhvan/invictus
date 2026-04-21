"""Текстовые и HTML report builders для backend-check сценариев trainings."""

from __future__ import annotations

import json

from src.services.backend_checks.trainings_checks_service import (
    PersonalTrainingConsistencyCheckResult,
    PersonalTrainingConsistencyRecord,
)
from src.utils.allure_html import HTML_CSS, html_table

_COL_HEADER = (
    f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} "
    f"{'Tickets':<8} {'Hist':<5} {'Sessions':<9} {'CnlNR':<7} "
    f"{'Status':<7} {'Updated At':<22} {'Created At':<22}"
)
_COL_SEP = "=" * 210


def _fmt_date(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt != "N/A" else "N/A"


def _result_to_line(record: PersonalTrainingConsistencyRecord) -> str:
    return (
        f"{record.idx:<4} {record.usp_id:<26} {record.user_id:<26} "
        f"{str(record.initial_count):<5} {str(record.count):<6} "
        f"{str(record.tickets_count):<8} {str(record.hist_count):<5} "
        f"{str(record.sessions_count):<9} {str(record.cancel_not_restored):<7} "
        f"{record.status:<7} {_fmt_date(record.updated_at):<22} {_fmt_date(record.created_at):<22}"
    )


def build_personal_trainings_text_table(records: list[PersonalTrainingConsistencyRecord]) -> str:
    """Строит текстовую таблицу результатов."""
    lines = [_COL_HEADER, _COL_SEP] + [_result_to_line(record) for record in records]
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
        "Tickets",
        "Hist",
        "Sessions",
        "CnlNR",
        "Status",
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
            str(record.tickets_count),
            str(record.hist_count),
            str(record.sessions_count),
            str(record.cancel_not_restored),
            record.status,
            _fmt_date(record.updated_at),
            _fmt_date(record.created_at),
        ]
        for record in records
    ]
    return HTML_CSS + f"<h2>{title}</h2>" + html_table(headers, rows)


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
        f"Всего: {len(result.records)}  OK: {result.ok_count}  FAIL: {result.failed_count}"
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
