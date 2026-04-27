from datetime import datetime

from src.services.backend_checks import payments_checks_service as service


def test_run_visit_bonus_coverage_check_ignores_user_owned_visit_referenced_by_id(monkeypatch):
    visit_time = datetime(2026, 4, 23, 9, 30, 0)

    monkeypatch.setattr(
        service,
        "get_visit_bonus_user_ids",
        lambda db, since, limit: ["user-1"],
    )
    monkeypatch.setattr(
        service,
        "get_visit_bonus_records_for_users",
        lambda db, since, user_ids: [],
    )
    monkeypatch.setattr(
        service,
        "get_access_entries_for_users",
        lambda db, user_ids, since, now: [
            {
                "_id": "entry-1",
                "user": "user-1",
                "time": visit_time,
                "accessType": "visits",
                "visits": "visit-1",
            }
        ],
    )
    monkeypatch.setattr(
        service,
        "get_visits_map_by_ids",
        lambda db, visit_ids: {"visit-1": {"source": "user"}},
        raising=False,
    )

    result = service.run_visit_bonus_coverage_check(
        db=object(),
        period_days=7,
        now=datetime(2026, 4, 23, 23, 59, 59),
    )

    assert result.visit_days_count == 0
    assert result.violations == []


def test_run_visit_bonus_coverage_check_matches_bonus_from_same_boundary_date(monkeypatch):
    boundary_day_bonus = datetime(2026, 4, 17, 4, 11, 44)
    visit_time = datetime(2026, 4, 17, 12, 30, 0)
    day_start = datetime(2026, 4, 17, 0, 0, 0)

    monkeypatch.setattr(
        service,
        "get_visit_bonus_user_ids",
        lambda db, since, limit: ["user-1"],
    )

    def get_bonus_records(db, since, user_ids):
        if since <= day_start:
            return [
                {
                    "_id": "bonus-1",
                    "user": "user-1",
                    "time": boundary_day_bonus,
                    "amount": 130,
                }
            ]
        return []

    monkeypatch.setattr(
        service,
        "get_visit_bonus_records_for_users",
        get_bonus_records,
    )
    monkeypatch.setattr(
        service,
        "get_access_entries_for_users",
        lambda db, user_ids, since, now: [
            {
                "_id": "access-1",
                "user": "user-1",
                "time": visit_time,
                "accessType": "subscription",
            }
        ],
    )

    result = service.run_visit_bonus_coverage_check(
        db=object(),
        period_days=7,
        now=datetime(2026, 4, 24, 12, 0, 0),
    )

    assert result.bonus_days_count == 1
    assert result.visit_days_count == 1
    assert result.violations == []


def test_run_visit_bonus_coverage_check_reports_accesscontrol_id_for_missing_bonus(monkeypatch):
    visit_time = datetime(2026, 4, 23, 9, 30, 0)

    monkeypatch.setattr(
        service,
        "get_visit_bonus_user_ids",
        lambda db, since, limit: ["user-1"],
    )
    monkeypatch.setattr(
        service,
        "get_visit_bonus_records_for_users",
        lambda db, since, user_ids: [],
    )
    monkeypatch.setattr(
        service,
        "get_access_entries_for_users",
        lambda db, user_ids, since, now: [
            {
                "_id": "access-1",
                "user": "user-1",
                "time": visit_time,
                "accessType": "subscription",
                "visits": {"source": "club"},
            }
        ],
    )

    result = service.run_visit_bonus_coverage_check(
        db=object(),
        period_days=7,
        now=datetime(2026, 4, 23, 23, 59, 59),
    )

    assert len(result.violations) == 1
    assert result.violations[0].accesscontrol_id == "access-1"
    assert result.violations[0].user_id == "user-1"
    assert result.violations[0].date == visit_time.date()


def test_run_visit_bonus_coverage_check_ignores_user_owned_visit_entries(monkeypatch):
    visit_time = datetime(2026, 4, 23, 9, 30, 0)

    monkeypatch.setattr(
        service,
        "get_visit_bonus_user_ids",
        lambda db, since, limit: ["user-1"],
    )
    monkeypatch.setattr(
        service,
        "get_visit_bonus_records_for_users",
        lambda db, since, user_ids: [],
    )
    monkeypatch.setattr(
        service,
        "get_access_entries_for_users",
        lambda db, user_ids, since, now: [
            {
                "_id": "entry-1",
                "user": "user-1",
                "time": visit_time,
                "accessType": "visits",
                "visits": {"source": "user"},
            }
        ],
    )

    result = service.run_visit_bonus_coverage_check(
        db=object(),
        period_days=7,
        now=datetime(2026, 4, 23, 23, 59, 59),
    )

    assert result.sample_users_count == 1
    assert result.bonus_days_count == 0
    assert result.visit_days_count == 0
    assert result.violations == []


def test_run_visit_bonus_accrual_check_flags_bonus_on_user_owned_visit_entry(monkeypatch):
    bonus_time = datetime(2026, 4, 23, 9, 30, 0)

    monkeypatch.setattr(
        service,
        "get_recent_visit_bonus_records",
        lambda db, since, limit: [
            {
                "_id": "bonus-1",
                "user": "user-1",
                "time": bonus_time,
                "amount": 500,
            }
        ],
    )
    monkeypatch.setattr(
        service,
        "get_access_entries_for_users",
        lambda db, user_ids, since, now: [
            {
                "_id": "entry-1",
                "user": "user-1",
                "time": bonus_time,
                "accessType": "visits",
                "visits": {"source": "user"},
            }
        ],
    )

    result = service.run_visit_bonus_accrual_check(
        db=object(),
        period_days=7,
        now=datetime(2026, 4, 23, 23, 59, 59),
    )

    assert result.bonus_records_count == 1
    assert result.access_entries_count == 0
    assert result.duplicate_days == []
    assert [violation.bonus_id for violation in result.missing_visit_bonuses] == ["bonus-1"]
