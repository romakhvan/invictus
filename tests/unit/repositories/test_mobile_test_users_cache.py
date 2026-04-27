import json
import uuid
from pathlib import Path

from src.repositories.mobile_test_users_cache import (
    CACHE_CATEGORIES,
    MobileTestUsersCache,
)


def _cache_path() -> Path:
    workspace = Path("tests/.tmp/mobile-test-users-cache")
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace / f"{uuid.uuid4().hex}.json"


def test_cache_creates_all_mobile_user_categories():
    cache_path = _cache_path()
    cache = MobileTestUsersCache(cache_path)

    data = cache.load()

    assert data["version"] == 1
    assert set(data["categories"]) == set(CACHE_CATEGORIES)
    assert all(data["categories"][category] == [] for category in CACHE_CATEGORIES)


def test_cache_appends_user_to_requested_category():
    cache = MobileTestUsersCache(_cache_path())

    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7001234567",
        user_id="user-123",
        expected_home_state="new_user",
        role="potential",
    )

    users = cache.get_category_users("POTENTIAL_USER")
    assert len(users) == 1
    assert users[0]["phone"] == "7001234567"
    assert users[0]["user_id"] == "user-123"
    assert users[0]["status"] == "valid"
    assert users[0]["invalid_reason"] is None
    assert cache.get_category_users("SUBSCRIBED_USER") == []


def test_cache_upserts_existing_user_instead_of_duplicating():
    cache = MobileTestUsersCache(_cache_path())
    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7001234567",
        user_id="user-123",
        expected_home_state="new_user",
        role="potential",
    )

    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7001234567",
        user_id="user-123",
        expected_home_state="new_user",
        role="potential",
    )

    users = cache.get_category_users("POTENTIAL_USER")
    assert len(users) == 1
    assert users[0]["user_id"] == "user-123"
    assert users[0]["status"] == "valid"


def test_cache_marks_invalid_without_deleting_entry():
    cache = MobileTestUsersCache(_cache_path())
    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7001234567",
        user_id="user-123",
        expected_home_state="new_user",
        role="potential",
    )

    cache.mark_invalid("POTENTIAL_USER", "user-123", "has related visits")

    users = cache.get_category_users("POTENTIAL_USER")
    assert len(users) == 1
    assert users[0]["status"] == "invalid"
    assert users[0]["invalid_reason"] == "has related visits"


def test_cache_ignores_invalid_json_and_recreates_shape():
    cache_path = _cache_path()
    cache_path.write_text("{broken", encoding="utf-8")

    data = MobileTestUsersCache(cache_path).load()

    assert data["version"] == 1
    assert set(data["categories"]) == set(CACHE_CATEGORIES)


def test_cache_preserves_invalid_entries_when_appending_new_valid_user():
    cache = MobileTestUsersCache(_cache_path())
    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7000000001",
        user_id="old-user",
        expected_home_state="new_user",
        role="potential",
    )
    cache.mark_invalid("POTENTIAL_USER", "old-user", "no metadata")

    cache.append_valid_user(
        "POTENTIAL_USER",
        phone="7000000002",
        user_id="new-user",
        expected_home_state="new_user",
        role="potential",
    )

    users = cache.get_category_users("POTENTIAL_USER")
    assert [user["user_id"] for user in users] == ["old-user", "new-user"]
    assert [user["status"] for user in users] == ["invalid", "valid"]


def test_cache_loads_existing_file_with_missing_categories():
    cache_path = _cache_path()
    cache_path.write_text(
        json.dumps({"version": 1, "categories": {"POTENTIAL_USER": []}}),
        encoding="utf-8",
    )

    data = MobileTestUsersCache(cache_path).load()

    assert set(data["categories"]) == set(CACHE_CATEGORIES)
