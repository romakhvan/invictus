"""Чтение купленных visit-записей из MongoDB."""

from datetime import datetime
from typing import Any

from src.utils.repository_helpers import get_collection


def get_recent_rabbit_visits_by_user(
    db,
    *,
    user_id: Any,
    since: datetime,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Возвращает свежие активные visits, выданные Rabbit Hole пользователю."""
    col = get_collection(db, "visits")
    query: dict[str, Any] = {
        "user": user_id,
        "created_at": {"$gte": since},
        "type": "visit",
        "source": "rabbit",
        "isActive": True,
        "isDeleted": False,
        "isExpired": False,
    }
    projection = {
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
    }

    visits = list(col.find(query, projection).sort("created_at", -1).limit(limit))

    print(f"\nПоиск свежих rabbit visits по user={user_id}")
    print(f"   since: {since.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   найдено: {len(visits)}")
    return visits
