from datetime import datetime

from src.repositories import visits_repository


class _FakeCursor:
    def __init__(self, docs):
        self.docs = docs
        self.sort_args = None
        self.limit_value = None

    def sort(self, *args):
        self.sort_args = args
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def __iter__(self):
        return iter(self.docs)


class _FakeCollection:
    def __init__(self, docs):
        self.docs = docs
        self.find_calls = []
        self.cursor = _FakeCursor(docs)

    def find(self, query, projection):
        self.find_calls.append((query, projection))
        return self.cursor


class _FakeDb:
    def __init__(self, docs):
        self.visits = _FakeCollection(docs)

    def __getitem__(self, name):
        assert name == "visits"
        return self.visits


def test_get_recent_rabbit_visits_by_user_filters_active_purchased_visits():
    since = datetime(2026, 4, 21, 10, 26, 36)
    docs = [{"_id": "visit-1"}, {"_id": "visit-2"}, {"_id": "visit-3"}]
    db = _FakeDb(docs)

    result = visits_repository.get_recent_rabbit_visits_by_user(
        db,
        user_id="user-123",
        since=since,
        limit=3,
    )

    assert result == docs
    assert db.visits.find_calls == [
        (
            {
                "user": "user-123",
                "created_at": {"$gte": since},
                "type": "visit",
                "source": "rabbit",
                "isActive": True,
                "isDeleted": False,
                "isExpired": False,
            },
            {
                "_id": 1,
                "user": 1,
                "type": 1,
                "source": 1,
                "club": 1,
                "clubUnion": 1,
                "endDate": 1,
                "isActive": 1,
                "isDeleted": 1,
                "isExpired": 1,
                "created_at": 1,
                "updatedAt": 1,
            },
        )
    ]
    assert db.visits.cursor.sort_args == ("created_at", -1)
    assert db.visits.cursor.limit_value == 3
