from datetime import datetime

from bson import ObjectId

from src.repositories import users_repository


class _FakeCursor:
    def __init__(self, docs):
        self.docs = docs
        self.sort_args = None

    def sort(self, *args):
        self.sort_args = args
        if args == ("created_at", -1):
            self.docs = sorted(
                self.docs,
                key=lambda doc: doc.get("created_at") or datetime.min,
                reverse=True,
            )
        return self

    def __iter__(self):
        return iter(self.docs)


class _FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.find_calls = []
        self.find_one_calls = []
        self.count_documents_calls = []
        self.cursor = _FakeCursor(self.docs)

    def find(self, query, projection=None, sort=None):
        self.find_calls.append((query, projection))
        docs = [doc for doc in self.docs if _matches_query(doc, query)]
        if sort == [("_id", -1)]:
            docs = sorted(docs, key=lambda doc: doc.get("_id"), reverse=True)
        self.cursor = _FakeCursor(docs)
        return self.cursor

    def find_one(self, query, projection=None):
        self.find_one_calls.append((query, projection))
        for doc in self.docs:
            if _matches_query(doc, query):
                return doc
        return None

    def count_documents(self, query):
        self.count_documents_calls.append(query)
        return sum(1 for doc in self.docs if _matches_query(doc, query))


class _FakeDb:
    def __init__(
        self,
        *,
        visits,
        users,
        subscriptions,
        usermetadatas=None,
        rabbitholev2=None,
        accesscontrols=None,
    ):
        self.collections = {
            "visits": _FakeCollection(visits),
            "users": _FakeCollection(users),
            "usersubscriptions": _FakeCollection(subscriptions),
            "usermetadatas": _FakeCollection(usermetadatas),
            "rabbitholev2": _FakeCollection(rabbitholev2),
            "accesscontrols": _FakeCollection(accesscontrols),
            "userserviceproducts": _FakeCollection([]),
            "coaches": _FakeCollection([]),
        }

    def __getitem__(self, name):
        return self.collections[name]


def _matches_query(doc, query):
    for key, expected in query.items():
        if key == "$or":
            if not any(_matches_query(doc, branch) for branch in expected):
                return False
            continue

        actual = doc.get(key)
        if isinstance(expected, dict):
            if "$exists" in expected and (key in doc) != expected["$exists"]:
                return False
            if "$in" in expected and actual not in expected["$in"]:
                return False
            continue
        if actual != expected:
            return False
    return True


def test_get_phone_for_active_rabbit_hole_user_returns_latest_valid_user_without_subscription():
    user_with_subscription = "user-sub"
    stale_valid_user = "user-stale"
    latest_valid_user = "user-latest"
    visits = [
        *_rabbit_visits(user_with_subscription, datetime(2026, 4, 20, 10, 0, 0)),
        *_rabbit_visits(stale_valid_user, datetime(2026, 4, 21, 10, 0, 0)),
        *_rabbit_visits(latest_valid_user, datetime(2026, 4, 22, 10, 0, 0)),
    ]
    db = _FakeDb(
        visits=visits,
        users=[
            {"_id": user_with_subscription, "phone": "7000000001"},
            {"_id": stale_valid_user, "phone": "7000000002"},
            {"_id": latest_valid_user, "phoneNumber": "+77000000003"},
        ],
        subscriptions=[
            {"_id": "sub-1", "user": user_with_subscription, "isActive": True, "isDeleted": False}
        ],
    )

    assert users_repository.get_phone_for_active_rabbit_hole_user(db) == "7000000003"

    assert db["visits"].find_calls == [
        (
            {
                "type": "visit",
                "source": "rabbit",
                "isActive": True,
                "isDeleted": False,
                "isExpired": False,
                "user": {"$exists": True},
            },
            {"user": 1, "created_at": 1},
        )
    ]
    assert db["visits"].cursor.sort_args == ("created_at", -1)


def test_get_phone_for_active_rabbit_hole_user_ignores_ineligible_candidates():
    valid_user = "user-valid"
    visits = [
        *_rabbit_visits("two-visits-only", datetime(2026, 4, 22, 12, 0, 0), count=2),
        *_rabbit_visits("inactive", datetime(2026, 4, 22, 11, 0, 0), isActive=False),
        *_rabbit_visits("deleted", datetime(2026, 4, 22, 10, 0, 0), isDeleted=True),
        *_rabbit_visits("expired", datetime(2026, 4, 22, 9, 0, 0), isExpired=True),
        *_rabbit_visits(valid_user, datetime(2026, 4, 22, 8, 0, 0)),
    ]
    db = _FakeDb(
        visits=visits,
        users=[{"_id": valid_user, "phone": "7000000004"}],
        subscriptions=[],
    )

    assert users_repository.get_phone_for_active_rabbit_hole_user(db) == "7000000004"


def test_get_phone_for_potential_user_skips_candidate_without_metadata():
    db = _FakeDb(
        users=[
            _potential_user("without-metadata", "7000000005"),
            _potential_user("with-metadata", "7000000006"),
        ],
        usermetadatas=[{"_id": "metadata-1", "user": "with-metadata"}],
        visits=[],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert users_repository.get_phone_for_potential_user(db) == "7000000006"


def test_get_phone_for_potential_user_returns_candidate_with_metadata_and_no_history():
    db = _FakeDb(
        users=[_potential_user("new-user", "+77000000007")],
        usermetadatas=[{"_id": "metadata-1", "userId": "new-user"}],
        visits=[],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert users_repository.get_phone_for_potential_user(db) == "7000000007"


def test_get_phone_for_potential_user_skips_candidate_with_any_related_record():
    related_collections = [
        "rabbitholev2",
        "visits",
        "usersubscriptions",
        "accesscontrols",
    ]

    for collection_name in related_collections:
        related_docs = {
            "rabbitholev2": [],
            "visits": [],
            "usersubscriptions": [],
            "accesscontrols": [],
        }
        related_docs[collection_name] = [
            {"_id": f"{collection_name}-1", "user": "with-history"}
        ]
        db = _FakeDb(
            users=[
                _potential_user("with-history", "7000000008"),
                _potential_user("new-user", "7000000009"),
            ],
            usermetadatas=[
                {"_id": "metadata-1", "user": "with-history"},
                {"_id": "metadata-2", "user": "new-user"},
            ],
            visits=related_docs["visits"],
            subscriptions=related_docs["usersubscriptions"],
            rabbitholev2=related_docs["rabbitholev2"],
            accesscontrols=related_docs["accesscontrols"],
        )

        assert users_repository.get_phone_for_potential_user(db) == "7000000009"


def test_get_phone_for_potential_user_checks_related_records_by_user_id_too():
    db = _FakeDb(
        users=[
            _potential_user("with-history", "7000000010"),
            _potential_user("new-user", "7000000011"),
        ],
        usermetadatas=[
            {"_id": "metadata-1", "user": "with-history"},
            {"_id": "metadata-2", "user": "new-user"},
        ],
        visits=[{"_id": "visit-1", "userId": "with-history"}],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert users_repository.get_phone_for_potential_user(db) == "7000000011"


def test_get_phone_for_potential_user_checks_candidates_in_batches():
    db = _FakeDb(
        users=[
            _potential_user("with-history", "7000000012"),
            _potential_user("without-metadata", "7000000013"),
            _potential_user("new-user", "7000000014"),
        ],
        usermetadatas=[
            {"_id": "metadata-1", "user": "with-history"},
            {"_id": "metadata-2", "userId": "new-user"},
        ],
        visits=[{"_id": "visit-1", "user": "with-history"}],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert users_repository.get_phone_for_potential_user(db) == "7000000014"

    assert db["usermetadatas"].find_calls == [
        (
            {
                "$or": [
                    {"user": {"$in": ["without-metadata", "with-history", "new-user"]}},
                    {"userId": {"$in": ["without-metadata", "with-history", "new-user"]}},
                ]
            },
            {"user": 1, "userId": 1},
        )
    ]
    assert db["usermetadatas"].find_one_calls == []
    assert db["visits"].count_documents_calls == []


def test_get_phone_for_potential_user_excludes_invalid_cached_users():
    db = _FakeDb(
        users=[
            _potential_user("invalid-user", "7000000015"),
            _potential_user("valid-user", "7000000016"),
        ],
        usermetadatas=[
            {"_id": "metadata-1", "user": "invalid-user"},
            {"_id": "metadata-2", "user": "valid-user"},
        ],
        visits=[],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert (
        users_repository.get_phone_for_potential_user(
            db,
            excluded_user_ids={"invalid-user"},
        )
        == "7000000016"
    )


def test_get_phone_for_potential_user_excludes_cached_object_id_strings():
    invalid_user = ObjectId("69eb49e5303ecac50e70a2f4")
    valid_user = ObjectId("69eb49e5303ecac50e70a2f3")
    db = _FakeDb(
        users=[
            _potential_user(invalid_user, "7000000020"),
            _potential_user(valid_user, "7000000021"),
        ],
        usermetadatas=[
            {"_id": "metadata-1", "user": invalid_user},
            {"_id": "metadata-2", "user": valid_user},
        ],
        visits=[],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert (
        users_repository.get_phone_for_potential_user(
            db,
            excluded_user_ids={str(invalid_user)},
        )
        == "7000000021"
    )


def test_validate_potential_test_user_rejects_history():
    db = _FakeDb(
        users=[_potential_user("with-history", "7000000017")],
        usermetadatas=[{"_id": "metadata-1", "user": "with-history"}],
        visits=[{"_id": "visit-1", "user": "with-history"}],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    valid, reason = users_repository.validate_potential_test_user(
        db,
        "with-history",
        "7000000017",
    )

    assert valid is False
    assert "visits" in reason


def test_validate_potential_test_user_accepts_string_object_id_from_cache():
    user_id = ObjectId("69eb49e5303ecac50e70a2f4")
    db = _FakeDb(
        users=[_potential_user(user_id, "7000000022")],
        usermetadatas=[{"_id": "metadata-1", "user": user_id}],
        visits=[],
        subscriptions=[],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert users_repository.validate_potential_test_user(db, str(user_id), "7000000022") == (
        True,
        None,
    )


def test_validate_subscribed_test_user_accepts_active_subscription():
    db = _FakeDb(
        users=[{"_id": "sub-user", "phone": "7000000018"}],
        usermetadatas=[],
        visits=[],
        subscriptions=[
            {"_id": "sub-1", "user": "sub-user", "isActive": True, "isDeleted": False}
        ],
        rabbitholev2=[],
        accesscontrols=[],
    )

    assert users_repository.validate_subscribed_test_user(db, "sub-user", "7000000018") == (
        True,
        None,
    )


def _potential_user(user_id, phone):
    return {
        "_id": user_id,
        "role": "potential",
        "firstName": "Test",
        "phone": phone,
    }


def _rabbit_visits(user, created_at, count=3, **overrides):
    docs = []
    for index in range(count):
        doc = {
            "_id": f"{user}-visit-{index}",
            "user": user,
            "created_at": created_at,
            "type": "visit",
            "source": "rabbit",
            "isActive": True,
            "isDeleted": False,
            "isExpired": False,
        }
        doc.update(overrides)
        docs.append(doc)
    return docs
