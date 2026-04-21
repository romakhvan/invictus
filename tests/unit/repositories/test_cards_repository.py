from datetime import datetime

from bson import ObjectId

from src.repositories import cards_repository


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
        return iter(self.docs[: self.limit_value])


class _FakeCollection:
    def __init__(self, docs):
        self.docs = docs
        self.find_calls = []
        self.update_one_calls = []
        self.cursor = _FakeCursor(docs)

    def find(self, query, projection):
        self.find_calls.append((query, projection))
        return self.cursor

    def update_one(self, query, update):
        self.update_one_calls.append((query, update))

        class _Result:
            matched_count = 1
            modified_count = 1

        return _Result()


class _FakeDb:
    def __init__(self, docs):
        self.cards = _FakeCollection(docs)

    def __getitem__(self, name):
        assert name == "cards"
        return self.cards


def test_attach_latest_saved_card_to_user_updates_latest_matching_card():
    card_id = ObjectId("662742f0fb8f1a613ea73001")
    user_id = ObjectId("662742f0fb8f1a613ea73002")
    created_at = datetime(2026, 4, 21, 10, 0, 0)
    db = _FakeDb(
        [
            {
                "_id": card_id,
                "hash": "4049320000006267",
                "user": ObjectId("662742f0fb8f1a613ea73003"),
                "created_at": created_at,
            }
        ]
    )

    result = cards_repository.attach_latest_saved_card_to_user(
        db,
        user_id=str(user_id),
    )

    assert result["_id"] == card_id
    assert db.cards.find_calls == [
        (
            {"hash": {"$regex": "^404932.*6267$"}},
            {
                "_id": 1,
                "hash": 1,
                "user": 1,
                "created_at": 1,
                "createdAt": 1,
            },
        )
    ]
    assert db.cards.cursor.sort_args == ([("created_at", -1), ("createdAt", -1), ("_id", -1)],)
    assert db.cards.cursor.limit_value == 1
    assert db.cards.update_one_calls == [
        (
            {"_id": card_id},
            {"$set": {"user": user_id}},
        )
    ]


def test_attach_latest_saved_card_to_user_raises_when_card_not_found():
    db = _FakeDb([])

    try:
        cards_repository.attach_latest_saved_card_to_user(db, user_id="user-123")
    except ValueError as exc:
        assert "cards" in str(exc)
        assert "404932" in str(exc)
    else:
        raise AssertionError("Expected ValueError when saved card is absent")
