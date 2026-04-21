"""Вычисление нарушений backend-check сценариев в домене trainings."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from src.repositories.trainings.checks_repository import (
    get_cancel_not_restored_counts,
    get_latest_history_counts,
    get_personal_training_usps,
    get_training_sessions_counts,
    get_training_tickets_counts,
)


@dataclass(frozen=True)
class RelativeDateOffset:
    years: int = 0
    months: int = 0
    days: int = 0


@dataclass(frozen=True)
class PersonalTrainingConsistencyRecord:
    idx: int
    usp_id: str
    user_id: str
    initial_count: Any
    count: Any
    tickets_count: int
    hist_count: Any
    sessions_count: int
    cancel_not_restored: int
    status: str
    updated_at: Any
    created_at: Any


@dataclass(frozen=True)
class PersonalTrainingConsistencyCheckResult:
    specific_usp_id: str | None
    updated_offset: RelativeDateOffset
    created_offset: RelativeDateOffset
    updated_from: datetime | None
    created_from: datetime | None
    records: list[PersonalTrainingConsistencyRecord]
    failed_records: list[PersonalTrainingConsistencyRecord]
    ok_count: int
    failed_count: int


def compute_relative_datetime(offset: RelativeDateOffset, *, now: datetime | None = None) -> datetime | None:
    """Возвращает now - offset, либо None если offset пустой."""
    if not (offset.years or offset.months or offset.days):
        return None

    current_time = now or datetime.now()
    target_month = current_time.month - offset.months
    target_year = current_time.year - offset.years
    while target_month <= 0:
        target_month += 12
        target_year -= 1

    max_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(current_time.day, max_day)
    return datetime(
        target_year,
        target_month,
        target_day,
        current_time.hour,
        current_time.minute,
        current_time.second,
    ) - timedelta(days=offset.days)


def build_personal_trainings_period_label(
    specific_usp_id: str | None,
    updated_offset: RelativeDateOffset,
    created_offset: RelativeDateOffset,
) -> str:
    """Формирует человекочитаемое описание фильтра периода."""
    if specific_usp_id:
        return f"Конкретная запись: {specific_usp_id}"

    parts = []
    if updated_offset.years or updated_offset.months or updated_offset.days:
        parts.append(
            f"updated_at: {updated_offset.years}г {updated_offset.months}м {updated_offset.days}д назад"
        )
    if created_offset.years or created_offset.months or created_offset.days:
        parts.append(
            f"created_at: {created_offset.years}г {created_offset.months}м {created_offset.days}д назад"
        )
    return ", ".join(parts) if parts else "без фильтра по дате"


def run_personal_trainings_consistency_check(
    db,
    *,
    specific_usp_id: str | None = None,
    updated_offset: RelativeDateOffset | None = None,
    created_offset: RelativeDateOffset | None = None,
    now: datetime | None = None,
) -> PersonalTrainingConsistencyCheckResult:
    """Проверяет консистентность персональных тренировок между коллекциями."""
    current_time = now or datetime.now()
    effective_updated_offset = updated_offset or RelativeDateOffset()
    effective_created_offset = created_offset or RelativeDateOffset()
    updated_from = compute_relative_datetime(effective_updated_offset, now=current_time)
    created_from = compute_relative_datetime(effective_created_offset, now=current_time)

    usps = get_personal_training_usps(
        db,
        specific_usp_id=specific_usp_id,
        updated_from=updated_from,
        created_from=created_from,
    )
    usp_ids = [usp["_id"] for usp in usps]

    tickets_counts = get_training_tickets_counts(db, usp_ids)
    history_counts = get_latest_history_counts(db, usp_ids)
    sessions_counts = get_training_sessions_counts(db, usp_ids)
    cancel_not_restored_counts = get_cancel_not_restored_counts(db, usp_ids)

    records: list[PersonalTrainingConsistencyRecord] = []
    for idx, usp in enumerate(usps, start=1):
        usp_id = usp["_id"]
        initial_count = usp.get("initialCount", "N/A")
        count = usp.get("count", "N/A")
        tickets_count = tickets_counts.get(usp_id, 0)
        hist_count = history_counts.get(usp_id, "N/A")
        sessions_count = sessions_counts.get(usp_id, 0)
        cancel_not_restored = cancel_not_restored_counts.get(usp_id, 0)

        status = "OK"
        if count != "N/A" and tickets_count != count:
            status = "FAIL"
        if count != "N/A" and hist_count != "N/A" and hist_count != count:
            status = "FAIL"
        if hist_count != "N/A" and tickets_count != hist_count:
            status = "FAIL"
        if (
            initial_count != "N/A"
            and count != "N/A"
            and (sessions_count + cancel_not_restored) != (initial_count - count)
        ):
            status = "FAIL"

        records.append(
            PersonalTrainingConsistencyRecord(
                idx=idx,
                usp_id=str(usp_id),
                user_id=str(usp["user"]),
                initial_count=initial_count,
                count=count,
                tickets_count=tickets_count,
                hist_count=hist_count,
                sessions_count=sessions_count,
                cancel_not_restored=cancel_not_restored,
                status=status,
                updated_at=usp.get("updated_at", "N/A"),
                created_at=usp.get("created_at", "N/A"),
            )
        )

    failed_records = [record for record in records if record.status == "FAIL"]
    ok_count = sum(1 for record in records if record.status == "OK")

    return PersonalTrainingConsistencyCheckResult(
        specific_usp_id=specific_usp_id,
        updated_offset=effective_updated_offset,
        created_offset=effective_created_offset,
        updated_from=updated_from,
        created_from=created_from,
        records=records,
        failed_records=failed_records,
        ok_count=ok_count,
        failed_count=len(failed_records),
    )
