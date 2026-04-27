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


def get_manual_count_update_infos(db, usp_ids: list[Any]) -> dict[Any, dict[str, Any]]:
    """Возвращает последнюю ручную правку count по USP."""
    if not usp_ids:
        return {}

    histories_col = get_collection(db, "userserviceproductshistories")
    return {
        document["_id"]: {
            "history_id": document["lastRecord"].get("_id"),
            "changed_at": document["lastRecord"].get("created_at", "N/A"),
            "change": _format_count_change(document["lastRecord"].get("changes", [])),
        }
        for document in histories_col.aggregate(
            [
                {
                    "$match": {
                        "userServiceProduct": {"$in": usp_ids},
                        "type": "UPDATE",
                        "changes.field": "count",
                    }
                },
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


def _format_count_change(changes: list[dict[str, Any]]) -> str:
    for change in changes:
        if change.get("field") == "count":
            return f"{change.get('from', 'N/A')} -> {change.get('to', 'N/A')}"
    return "N/A"


def get_service_product_infos(db, service_product_ids: list[Any]) -> dict[Any, dict[str, Any]]:
    """Возвращает поля serviceproducts для отображения в отчёте."""
    if not service_product_ids:
        return {}

    serviceproducts_col = get_collection(db, "serviceproducts")
    return {
        document["_id"]: {
            "title": document.get("title", "N/A"),
            "type": document.get("type", "N/A"),
            "trainingType": document.get("trainingType", "N/A"),
        }
        for document in serviceproducts_col.aggregate(
            [
                {"$match": {"_id": {"$in": service_product_ids}}},
                {"$project": {"_id": 1, "title": 1, "type": 1, "trainingType": 1}},
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
