from datetime import datetime

from src.repositories.payments import checks_repository


class _FakeCursor:
    def __init__(self, docs):
        self.docs = docs
        self.sort_calls = []
        self.limit_calls = []

    def __iter__(self):
        return iter(self.docs)

    def sort(self, field, direction):
        self.sort_calls.append((field, direction))
        return self

    def limit(self, limit):
        self.limit_calls.append(limit)
        return self


class _FakeCollection:
    def __init__(self, docs=None, aggregate_docs=None):
        self.docs = docs
        self.aggregate_docs = aggregate_docs or []
        self.find_calls = []
        self.aggregate_calls = []
        self.last_cursor = None

    def find(self, query, projection):
        self.find_calls.append((query, projection))
        self.last_cursor = _FakeCursor(self.docs)
        return self.last_cursor

    def aggregate(self, pipeline):
        self.aggregate_calls.append(pipeline)
        return _FakeCursor(self.aggregate_docs)


class _FakeDb:
    def __init__(self, docs):
        self.collections = {
            "accesscontrols": _FakeCollection(docs),
            "visits": _FakeCollection(docs),
        }

    def __getitem__(self, name):
        return self.collections[name]


def test_get_access_entries_for_users_requests_visit_reference_projection():
    since = datetime(2026, 4, 23, 0, 0, 0)
    now = datetime(2026, 4, 23, 23, 59, 59)
    docs = [{"_id": "entry-1"}]
    db = _FakeDb(docs)

    result = checks_repository.get_access_entries_for_users(
        db,
        user_ids=["user-1"],
        since=since,
        now=now,
    )

    assert result == docs
    assert db["accesscontrols"].find_calls == [
        (
            {
                "user": {"$in": ["user-1"]},
                "type": "enter",
                "err": {"$exists": False},
                "accessType": {"$ne": "staff"},
                "time": {"$gte": since, "$lte": now},
            },
            {"_id": 1, "user": 1, "time": 1, "accessType": 1, "club": 1, "visits": 1},
        )
    ]


def test_get_visits_map_by_ids_returns_source_by_string_id():
    docs = [
        {"_id": "visit-1", "source": "user", "type": "visit"},
        {"_id": "visit-2", "source": "subscription", "type": "unlim"},
    ]
    db = _FakeDb(docs)

    result = checks_repository.get_visits_map_by_ids(db, visit_ids=["visit-1", "visit-2"])

    assert result == {
        "visit-1": {"_id": "visit-1", "source": "user", "type": "visit"},
        "visit-2": {"_id": "visit-2", "source": "subscription", "type": "unlim"},
    }
    assert db["visits"].find_calls == [
        (
            {"_id": {"$in": ["visit-1", "visit-2"]}},
            {"_id": 1, "source": 1, "type": 1},
        )
    ]


def test_get_recent_transaction_instalment_stats_uses_aggregation_not_full_document_scan():
    since = datetime(2026, 4, 23, 0, 0, 0)
    transactions_col = _FakeCollection(
        aggregate_docs=[
            {
                "_id": "recurrent",
                "transactions_count": 3,
                "total_amount": 12000,
                "status_counts": {"success": 2, "fail": 1},
            }
        ]
    )
    db = type("_Db", (), {"__getitem__": lambda self, name: transactions_col})()

    result = checks_repository.get_recent_transaction_instalment_stats(db, since=since)

    assert result == transactions_col.aggregate_docs
    assert transactions_col.find_calls == []
    pipeline = transactions_col.aggregate_calls[0]
    assert pipeline[0] == {
        "$match": {
            "created_at": {"$gte": since},
            "source": {"$ne": "pos"},
        }
    }
    assert pipeline[-1] == {"$sort": {"_id": 1}}


def test_get_recent_transaction_fail_examples_limits_and_projects_documents():
    since = datetime(2026, 4, 23, 0, 0, 0)
    docs = [{"_id": "tx-1"}]
    transactions_col = _FakeCollection(docs=docs)
    db = type("_Db", (), {"__getitem__": lambda self, name: transactions_col})()

    result = checks_repository.get_recent_transaction_fail_examples(
        db,
        since=since,
        limit=25,
    )

    assert result == docs
    assert transactions_col.find_calls == [
        (
            {
                "created_at": {"$gte": since},
                "source": {"$ne": "pos"},
                "status": "fail",
            },
            {
                "_id": 1,
                "created_at": 1,
                "price": 1,
                "productType": 1,
                "instalmentType": 1,
                "reason": 1,
            },
        )
    ]
    assert transactions_col.last_cursor.sort_calls == [("created_at", -1)]
    assert transactions_col.last_cursor.limit_calls == [25]


def test_get_recent_recurrent_success_instalment_stats_filters_success_recurrent():
    since = datetime(2026, 4, 23, 0, 0, 0)
    transactions_col = _FakeCollection(
        aggregate_docs=[
            {
                "_id": "standard",
                "transactions_count": 2,
            }
        ]
    )
    db = type("_Db", (), {"__getitem__": lambda self, name: transactions_col})()

    result = checks_repository.get_recent_recurrent_success_instalment_stats(db, since=since)

    assert result == transactions_col.aggregate_docs
    assert transactions_col.find_calls == []
    assert transactions_col.aggregate_calls[0][0] == {
        "$match": {
            "created_at": {"$gte": since},
            "source": {"$ne": "pos"},
            "status": "success",
            "productType": "recurrent",
        }
    }
