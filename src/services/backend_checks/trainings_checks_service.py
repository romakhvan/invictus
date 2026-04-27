"""Вычисление нарушений backend-check сценариев в домене trainings."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from src.repositories.trainings.checks_repository import (
    get_cancel_not_restored_counts,
    get_latest_history_counts,
    get_manual_count_update_infos,
    get_personal_training_usps,
    get_service_product_infos,
    get_training_sessions_counts,
    get_training_tickets_counts,
)


@dataclass(frozen=True)
class RelativeDateOffset:
    years: int = 0
    months: int = 0
    days: int = 0


@dataclass(frozen=True)
class RuleViolation:
    rule_id: str
    title: str
    expected: str
    actual: str


RULE_TITLES = {
    "tickets_mismatch": "count != active trainingtickets",
    "history_count_mismatch": "count != latest history currentCount",
    "tickets_history_mismatch": "active trainingtickets != latest history currentCount",
    "sessions_usage_mismatch": "trainingsessions + cancel_not_restored != initialCount - count",
}


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
    service_product_title: str = "N/A"
    service_product_type: str = "N/A"
    service_product_training_type: str = "N/A"
    manual_count_update_id: str | None = None
    manual_count_update_at: Any = "N/A"
    manual_count_change: str = "N/A"
    tickets_mismatch: bool = False
    tickets_mismatch_expected: str = "N/A"
    tickets_mismatch_actual: str = "N/A"
    history_count_mismatch: bool = False
    history_count_mismatch_expected: str = "N/A"
    history_count_mismatch_actual: str = "N/A"
    tickets_history_mismatch: bool = False
    tickets_history_mismatch_expected: str = "N/A"
    tickets_history_mismatch_actual: str = "N/A"
    sessions_usage_mismatch: bool = False
    sessions_usage_mismatch_expected: str = "N/A"
    sessions_usage_mismatch_actual: str = "N/A"

    @property
    def rule_violations(self) -> list[RuleViolation]:
        violations = []
        for rule_id in RULE_TITLES:
            if getattr(self, rule_id):
                violations.append(
                    RuleViolation(
                        rule_id=rule_id,
                        title=RULE_TITLES[rule_id],
                        expected=getattr(self, f"{rule_id}_expected"),
                        actual=getattr(self, f"{rule_id}_actual"),
                    )
                )
        return violations


@dataclass(frozen=True)
class PersonalTrainingConsistencyCheckResult:
    specific_usp_id: str | None
    updated_offset: RelativeDateOffset
    created_offset: RelativeDateOffset
    updated_from: datetime | None
    created_from: datetime | None
    records: list[PersonalTrainingConsistencyRecord]
    failed_records: list[PersonalTrainingConsistencyRecord]
    regular_failed_records: list[PersonalTrainingConsistencyRecord]
    manual_update_failed_records: list[PersonalTrainingConsistencyRecord]
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
    service_product_ids = list(
        {
            usp["serviceProduct"]
            for usp in usps
            if usp.get("serviceProduct") is not None
        }
    )
    service_product_infos = get_service_product_infos(db, service_product_ids)
    usps = [
        usp
        for usp in usps
        if not _is_inbody_service_product(
            service_product_infos.get(usp.get("serviceProduct"), {})
        )
    ]
    usp_ids = [usp["_id"] for usp in usps]

    tickets_counts = get_training_tickets_counts(db, usp_ids)
    history_counts = get_latest_history_counts(db, usp_ids)
    sessions_counts = get_training_sessions_counts(db, usp_ids)
    cancel_not_restored_counts = get_cancel_not_restored_counts(db, usp_ids)
    manual_count_update_infos = get_manual_count_update_infos(db, usp_ids)

    records: list[PersonalTrainingConsistencyRecord] = []
    for idx, usp in enumerate(usps, start=1):
        usp_id = usp["_id"]
        initial_count = usp.get("initialCount", "N/A")
        count = usp.get("count", "N/A")
        tickets_count = tickets_counts.get(usp_id, 0)
        hist_count = history_counts.get(usp_id, "N/A")
        sessions_count = sessions_counts.get(usp_id, 0)
        cancel_not_restored = cancel_not_restored_counts.get(usp_id, 0)
        manual_count_update_info = manual_count_update_infos.get(usp_id)
        service_product_info = service_product_infos.get(usp.get("serviceProduct"), {})

        tickets_mismatch = False
        tickets_mismatch_expected = "N/A"
        tickets_mismatch_actual = "N/A"
        history_count_mismatch = False
        history_count_mismatch_expected = "N/A"
        history_count_mismatch_actual = "N/A"
        tickets_history_mismatch = False
        tickets_history_mismatch_expected = "N/A"
        tickets_history_mismatch_actual = "N/A"
        sessions_usage_mismatch = False
        sessions_usage_mismatch_expected = "N/A"
        sessions_usage_mismatch_actual = "N/A"

        if count != "N/A" and tickets_count != count:
            tickets_mismatch = True
            tickets_mismatch_expected = f"count={count}"
            tickets_mismatch_actual = f"activeTickets={tickets_count}"
        if count != "N/A" and hist_count != "N/A" and hist_count != count:
            history_count_mismatch = True
            history_count_mismatch_expected = f"count={count}"
            history_count_mismatch_actual = f"hist={hist_count}"
        if hist_count != "N/A" and tickets_count != hist_count and history_count_mismatch:
            tickets_history_mismatch = True
            tickets_history_mismatch_expected = f"tickets={tickets_count}"
            tickets_history_mismatch_actual = f"hist={hist_count}"
        if (
            initial_count != "N/A"
            and count != "N/A"
            and (sessions_count + cancel_not_restored) != (initial_count - count)
        ):
            sessions_usage_mismatch = True
            sessions_usage_mismatch_expected = f"initial-count={initial_count}-{count}"
            sessions_usage_mismatch_actual = f"sessions+cancel={sessions_count}+{cancel_not_restored}"

        status = "FAIL" if any(
            [
                tickets_mismatch,
                history_count_mismatch,
                tickets_history_mismatch,
                sessions_usage_mismatch,
            ]
        ) else "OK"

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
                service_product_title=service_product_info.get("title", "N/A"),
                service_product_type=service_product_info.get("type", "N/A"),
                service_product_training_type=service_product_info.get("trainingType", "N/A"),
                manual_count_update_id=(
                    str(manual_count_update_info["history_id"]) if manual_count_update_info else None
                ),
                manual_count_update_at=(
                    manual_count_update_info["changed_at"] if manual_count_update_info else "N/A"
                ),
                manual_count_change=manual_count_update_info["change"] if manual_count_update_info else "N/A",
                tickets_mismatch=tickets_mismatch,
                tickets_mismatch_expected=tickets_mismatch_expected,
                tickets_mismatch_actual=tickets_mismatch_actual,
                history_count_mismatch=history_count_mismatch,
                history_count_mismatch_expected=history_count_mismatch_expected,
                history_count_mismatch_actual=history_count_mismatch_actual,
                tickets_history_mismatch=tickets_history_mismatch,
                tickets_history_mismatch_expected=tickets_history_mismatch_expected,
                tickets_history_mismatch_actual=tickets_history_mismatch_actual,
                sessions_usage_mismatch=sessions_usage_mismatch,
                sessions_usage_mismatch_expected=sessions_usage_mismatch_expected,
                sessions_usage_mismatch_actual=sessions_usage_mismatch_actual,
            )
        )

    failed_records = [record for record in records if record.status == "FAIL"]
    manual_update_failed_records = [
        record for record in failed_records if record.manual_count_update_id is not None
    ]
    regular_failed_records = [
        record for record in failed_records if record.manual_count_update_id is None
    ]
    ok_count = sum(1 for record in records if record.status == "OK")

    return PersonalTrainingConsistencyCheckResult(
        specific_usp_id=specific_usp_id,
        updated_offset=effective_updated_offset,
        created_offset=effective_created_offset,
        updated_from=updated_from,
        created_from=created_from,
        records=records,
        failed_records=failed_records,
        regular_failed_records=regular_failed_records,
        manual_update_failed_records=manual_update_failed_records,
        ok_count=ok_count,
        failed_count=len(failed_records),
    )


def _is_inbody_service_product(service_product_info: dict[str, Any]) -> bool:
    return "inbody" in str(service_product_info.get("title", "")).lower()
