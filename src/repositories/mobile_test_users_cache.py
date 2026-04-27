import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CACHE_VERSION = 1
CACHE_CATEGORIES = (
    "POTENTIAL_USER",
    "SUBSCRIBED_USER",
    "MEMBER_USER",
    "RABBIT_HOLE_USER",
    "COACH_USER",
)
DEFAULT_CACHE_PATH = Path("data") / "mobile_test_users_cache.json"


class MobileTestUsersCache:
    """Local JSON cache for reusable mobile test users."""

    def __init__(self, path: str | Path = DEFAULT_CACHE_PATH):
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return self._empty_cache()

        if not isinstance(raw, dict) or raw.get("version") != CACHE_VERSION:
            return self._empty_cache()

        categories = raw.get("categories")
        if not isinstance(categories, dict):
            return self._empty_cache()

        normalized = self._empty_cache()
        for category in CACHE_CATEGORIES:
            users = categories.get(category, [])
            normalized["categories"][category] = (
                self._dedupe_users_by_id(users) if isinstance(users, list) else []
            )
        return normalized

    def get_category_users(self, category: str) -> list[dict[str, Any]]:
        return list(self.load()["categories"].get(category, []))

    def append_valid_user(
        self,
        category: str,
        *,
        phone: str,
        user_id: str,
        expected_home_state: str | None,
        role: str | None,
    ) -> None:
        data = self.load()
        users = data["categories"].setdefault(category, [])
        new_entry = {
            "phone": phone,
            "user_id": user_id,
            "status": "valid",
            "expected_home_state": expected_home_state,
            "role": role,
            "updated_at": self._now(),
            "invalid_reason": None,
        }
        users[:] = [user for user in users if str(user.get("user_id")) != str(user_id)]
        users.append(new_entry)
        self.save(data)

    def mark_invalid(self, category: str, user_id: str, reason: str) -> None:
        data = self.load()
        users = data["categories"].setdefault(category, [])
        for user in users:
            if str(user.get("user_id")) == str(user_id):
                user["status"] = "invalid"
                user["invalid_reason"] = reason
                user["updated_at"] = self._now()
                break
        self.save(data)

    def save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @staticmethod
    def _empty_cache() -> dict[str, Any]:
        return {
            "version": CACHE_VERSION,
            "categories": {category: [] for category in CACHE_CATEGORIES},
        }

    @staticmethod
    def _dedupe_users_by_id(users: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped_by_id: dict[str, dict[str, Any]] = {}
        users_without_id = []
        for user in users:
            if not isinstance(user, dict):
                continue
            user_id = user.get("user_id")
            if user_id:
                deduped_by_id[str(user_id)] = user
            else:
                users_without_id.append(user)
        return users_without_id + list(deduped_by_id.values())

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
