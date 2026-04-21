"""Чтение данных для backend-check сценариев в домене trainings."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bson import ObjectId

from src.utils.repository_helpers import get_collection


def get_personal_training_usps(
    db,
    *,
    specific_usp_id: str | None = None,
    updated_from: datetime | None = None,
    created_from: datetime | None = None,
) -> list[dict[str, Any]]:
    """Возвращает записи userserviceproducts для проверки персональных тренировок."""
    userserviceproducts_col = get_collection(db, "userserviceproducts")

    if specific_usp_id:
        record = userserviceproducts_col.find_one(
            {
                "_id": ObjectId(specific_usp_id),
                "isDeleted": False,
                "type": "SPECIALIST",
            }
        )
        return [record] if record else []

    query: dict[str, Any] = {"isDeleted": False, "isActive": True, "type": "SPECIALIST"}
    if updated_from is not None:
        query["updated_at"] = {"$gte": updated_from}
    if created_from is not None:
        query["created_at"] = {"$gte": created_from}

    sort_field = "updated_at" if updated_from is not None else "created_at" if created_from is not None else "_id"
    return list(userserviceproducts_col.find(query).sort(sort_field, -1))


def get_training_tickets_counts(db, usp_ids: list[Any]) -> dict[Any, int]:
    """Возвращает количество активных неиспользованных билетов по USP."""
    if not usp_ids:
        return {}

    trainingtickets_col = get_collection(db, "trainingtickets")
    return {
        document["_id"]: document["count"]
        for document in trainingtickets_col.aggregate(
            [
                {
                    "$match": {
                        "userServiceProduct": {"$in": usp_ids},
                        "isUsed": False,
                        "status": "active",
                        "isDeleted": False,
                    }
                },
                {"$group": {"_id": "$userServiceProduct", "count": {"$sum": 1}}},
            ]
        )
    }


def get_latest_history_counts(db, usp_ids: list[Any]) -> dict[Any, Any]:
    """Возвращает currentCount из последней записи истории по USP."""
    if not usp_ids:
        return {}

    histories_col = get_collection(db, "userserviceproductshistories")
    return {
        document["_id"]: document["lastRecord"].get("currentCount", "N/A")
        for document in histories_col.aggregate(
            [
                {"$match": {"userServiceProduct": {"$in": usp_ids}}},
                {"$sort": {"created_at": -1}},
                {
                    "$group": {
                        "_id": "$userServiceProduct",
                        "lastRecord": {"$first": "$$ROOT"},
                    }
                },
            ]
        )
    }


def get_training_sessions_counts(db, usp_ids: list[Any]) -> dict[Any, int]:
    """Возвращает количество training sessions по USP."""
    if not usp_ids:
        return {}

    trainingsessions_col = get_collection(db, "trainingsessions")
    return {
        document["_id"]: document["count"]
        for document in trainingsessions_col.aggregate(
            [
                {"$match": {"participantsList.userServiceProduct": {"$in": usp_ids}}},
                {"$unwind": "$participantsList"},
                {"$match": {"participantsList.userServiceProduct": {"$in": usp_ids}}},
                {"$group": {"_id": "$participantsList.userServiceProduct", "count": {"$sum": 1}}},
            ]
        )
    }


def get_cancel_not_restored_counts(db, usp_ids: list[Any]) -> dict[Any, int]:
    """Возвращает количество отмен без восстановления по USP."""
    if not usp_ids:
        return {}

    histories_col = get_collection(db, "userserviceproductshistories")
    return {
        document["_id"]: document["count"]
        for document in histories_col.aggregate(
            [
                {
                    "$match": {
                        "userServiceProduct": {"$in": usp_ids},
                        "type": "CANCEL_BOOKING",
                        "isRestored": False,
                    }
                },
                {"$group": {"_id": "$userServiceProduct", "count": {"$sum": 1}}},
            ]
        )
    }
