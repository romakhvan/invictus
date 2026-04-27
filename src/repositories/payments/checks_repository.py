"""Чтение данных для backend-check сценариев в домене payments."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.utils.repository_helpers import get_collection


def get_freeze_days_transactions(db, since: datetime) -> list[dict[str, Any]]:
    """Возвращает успешные FREEZE_DAYS транзакции за период."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
            {
                "productType": "FREEZE_DAYS",
                "status": "success",
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "created_at": 1,
                "price": 1,
                "paidFor.freezing.userSubscription": 1,
            },
        ).sort("created_at", -1)
    )


def get_forbidden_bonus_spend_transactions(
    db,
    since: datetime,
    forbidden_types: list[str],
) -> list[dict[str, Any]]:
    """Возвращает транзакции запрещённых типов со списанием бонусов."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
            {
                "status": "success",
                "productType": {"$in": forbidden_types},
                "bonusesSpent": {"$gt": 0},
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "productType": 1,
                "bonusesSpent": 1,
                "price": 1,
                "created_at": 1,
                "clubId": 1,
                "userId": 1,
            },
        ).sort("created_at", -1)
    )


def get_bonus_spend_transactions(db, since: datetime) -> list[dict[str, Any]]:
    """Возвращает успешные транзакции со списанием бонусов за период."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
            {
                "status": "success",
                "bonusesSpent": {"$gt": 0},
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "bonusesSpent": 1,
                "created_at": 1,
                "productType": 1,
                "clubId": 1,
                "price": 1,
                "paidFor": 1,
            },
        ).sort("created_at", -1)
    )


def get_subscription_bonus_spend_transactions(db, since: datetime) -> list[dict[str, Any]]:
    """Returns successful subscription transactions with bonus deductions for limit checks."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
            {
                "status": "success",
                "bonusesSpent": {"$gt": 0},
                "paidFor.subscription.0": {"$exists": True},
                "productType": {"$ne": "recurrent"},
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "productType": 1,
                "bonusesSpent": 1,
                "price": 1,
                "created_at": 1,
                "clubId": 1,
                "userId": 1,
                "paidFor.subscription": 1,
            },
        ).sort("created_at", -1)
    )


def get_recent_subscription_purchase_transactions(
    db,
    *,
    since: datetime,
    limit: int,
) -> list[dict[str, Any]]:
    """Returns recent successful subscription purchases for accrual checks."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
            {
                "status": "success",
                "productType": {"$in": ["services", "subscription"]},
                "paidFor.subscription.0": {"$exists": True},
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "price": 1,
                "bonusesSpent": 1,
                "created_at": 1,
                "clubId": 1,
                "productType": 1,
                "paidFor.subscription": 1,
                "paidFor.discountId": 1,
            },
        ).sort("created_at", -1).limit(limit)
    )


def get_subscriptions_map_by_ids(db, subscription_ids: list[Any]) -> dict[Any, dict[str, Any]]:
    """Возвращает словарь subscriptionId -> subscription document."""
    if not subscription_ids:
        return {}

    subscriptions_col = get_collection(db, "subscriptions")
    return {
        subscription["_id"]: subscription
        for subscription in subscriptions_col.find(
            {"_id": {"$in": subscription_ids}},
            {"_id": 1, "name": 1, "interval": 1},
        )
    }


def get_subscription_plans_map_by_ids(db, subscription_ids: list[Any]) -> dict[Any, dict[str, Any]]:
    """Returns subscription plans by id with fields required for bonus checks."""
    if not subscription_ids:
        return {}

    subscriptions_col = get_collection(db, "subscriptions")
    return {
        subscription["_id"]: subscription
        for subscription in subscriptions_col.find(
            {"_id": {"$in": subscription_ids}},
            {"_id": 1, "name": 1, "interval": 1, "isRecurrent": 1},
        )
    }


def get_bonus_pay_history_records(
    db,
    *,
    user_ids: list[Any],
    window_start: datetime,
    window_end: datetime,
) -> list[dict[str, Any]]:
    """Возвращает PAY-записи бонусной истории по пользователям в окне времени."""
    if not user_ids:
        return []

    bonus_col = get_collection(db, "userbonuseshistories")
    return list(
        bonus_col.find(
            {
                "type": "PAY",
                "user": {"$in": user_ids},
                "time": {"$gte": window_start, "$lte": window_end},
            },
            {"_id": 1, "user": 1, "amount": 1, "time": 1},
        )
    )


def get_subscription_bonus_history_records(
    db,
    *,
    user_ids: list[Any],
    window_start: datetime,
    window_end: datetime,
) -> list[dict[str, Any]]:
    """Returns SUBSCRIPTION bonus history records for users in a time window."""
    if not user_ids:
        return []

    bonus_col = get_collection(db, "userbonuseshistories")
    return list(
        bonus_col.find(
            {
                "type": "SUBSCRIPTION",
                "user": {"$in": user_ids},
                "time": {"$gte": window_start, "$lte": window_end},
            },
            {"_id": 1, "user": 1, "amount": 1, "time": 1},
        )
    )


def get_recent_visit_bonus_records(
    db,
    *,
    since: datetime,
    limit: int,
) -> list[dict[str, Any]]:
    """Returns recent VISIT bonus records excluding manual description-based entries."""
    bonus_col = get_collection(db, "userbonuseshistories")
    return list(
        bonus_col.find(
            {
                "type": "VISIT",
                "time": {"$gte": since},
                "description": {"$exists": False},
            },
            {"_id": 1, "user": 1, "time": 1, "amount": 1},
        ).sort("time", -1).limit(limit)
    )


def get_visit_bonus_records_for_users(
    db,
    *,
    since: datetime,
    user_ids: list[Any],
) -> list[dict[str, Any]]:
    """Returns VISIT bonus records for the provided users within the period."""
    if not user_ids:
        return []

    bonus_col = get_collection(db, "userbonuseshistories")
    return list(
        bonus_col.find(
            {
                "type": "VISIT",
                "time": {"$gte": since},
                "description": {"$exists": False},
                "user": {"$in": user_ids},
            },
            {"_id": 1, "user": 1, "time": 1, "amount": 1},
        )
    )


def get_visit_bonus_user_ids(
    db,
    *,
    since: datetime,
    limit: int,
) -> list[Any]:
    """Returns distinct users who received VISIT bonuses in the period."""
    bonus_col = get_collection(db, "userbonuseshistories")
    return bonus_col.distinct(
        "user",
        {
            "type": "VISIT",
            "time": {"$gte": since},
            "description": {"$exists": False},
        },
    )[:limit]


def get_visits_map_by_ids(db, visit_ids: list[Any]) -> dict[str, dict[str, Any]]:
    """Returns visit documents by id with fields required for bonus eligibility checks."""
    if not visit_ids:
        return {}

    visits_col = get_collection(db, "visits")
    return {
        str(visit["_id"]): visit
        for visit in visits_col.find(
            {"_id": {"$in": visit_ids}},
            {"_id": 1, "source": 1, "type": 1},
        )
    }


def get_transactions_with_promo_code(db, since: datetime) -> list[dict[str, Any]]:
    """Возвращает успешные транзакции с применённым промокодом за период."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
            {
                "paidFor.discountId": {"$exists": True},
                "status": "success",
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "userId": 1,
                "created_at": 1,
                "price": 1,
                "productType": 1,
                "paidFor.discountId": 1,
                "paidFor.discountedPrice": 1,
                "paidFor.totalPrice": 1,
                "paidFor.subscription": 1,
            },
        ).sort("created_at", -1)
    )


def get_discounts_map_by_ids(db, discount_ids: list[Any]) -> dict[str, dict[str, Any]]:
    """Возвращает скидки по списку ObjectId в виде словаря по строковому ключу."""
    if not discount_ids:
        return {}

    discounts_col = get_collection(db, "discounts")
    return {
        str(discount["_id"]): discount
        for discount in discounts_col.find({"_id": {"$in": discount_ids}})
    }


def get_internal_error_transactions(db, since: datetime) -> list[dict[str, Any]]:
    """Возвращает транзакции со статусом internalError за период."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
            {
                "status": "internalError",
                "created_at": {"$gte": since},
            },
            {
                "_id": 1,
                "clubId": 1,
                "price": 1,
                "created_at": 1,
                "productType": 1,
                "source": 1,
                "instalmentType": 1,
                "userId": 1,
                "reason": 1,
            },
        ).sort("created_at", -1)
    )


def get_recent_transaction_instalment_stats(db, since: datetime) -> list[dict[str, Any]]:
    """Returns transaction counts by instalmentType without loading all documents."""
    transactions_col = get_collection(db, "transactions")
    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": since},
                "source": {"$ne": "pos"},
            }
        },
        {
            "$group": {
                "_id": {
                    "instalmentType": {"$ifNull": ["$instalmentType", "Не указан"]},
                    "status": {"$ifNull": ["$status", "unknown"]},
                },
                "transactions_count": {"$sum": 1},
                "total_amount": {"$sum": {"$ifNull": ["$price", 0]}},
            }
        },
        {
            "$group": {
                "_id": "$_id.instalmentType",
                "transactions_count": {"$sum": "$transactions_count"},
                "total_amount": {"$sum": "$total_amount"},
                "status_counts": {
                    "$push": {
                        "k": "$_id.status",
                        "v": "$transactions_count",
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 1,
                "transactions_count": 1,
                "total_amount": 1,
                "status_counts": {"$arrayToObject": "$status_counts"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return list(transactions_col.aggregate(pipeline))


def get_recent_recurrent_success_instalment_stats(db, since: datetime) -> list[dict[str, Any]]:
    """Returns successful recurrent transaction counts by instalmentType."""
    transactions_col = get_collection(db, "transactions")
    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": since},
                "source": {"$ne": "pos"},
                "status": "success",
                "productType": "recurrent",
            }
        },
        {
            "$group": {
                "_id": {"$ifNull": ["$instalmentType", "Не указан"]},
                "transactions_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return list(transactions_col.aggregate(pipeline))


def get_recent_transaction_fail_examples(
    db,
    since: datetime,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    """Returns a bounded sample of recent failed transactions for reporting."""
    transactions_col = get_collection(db, "transactions")
    return list(
        transactions_col.find(
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
        ).sort("created_at", -1).limit(limit)
    )


def get_visit_transactions_with_club_type(db, since: datetime) -> list[dict[str, Any]]:
    """Returns successful visits transactions enriched with club service and club data."""
    transactions_col = get_collection(db, "transactions")
    pipeline = [
        {
            "$match": {
                "productType": "visits",
                "status": "success",
                "created_at": {"$gte": since},
                "paidFor.visits.0": {"$exists": True},
            }
        },
        {"$unwind": "$paidFor.visits"},
        {"$match": {"paidFor.visits.clubServiceId": {"$exists": True}}},
        {
            "$lookup": {
                "from": "clubservices",
                "localField": "paidFor.visits.clubServiceId",
                "foreignField": "_id",
                "as": "clubservice",
            }
        },
        {"$unwind": "$clubservice"},
        {
            "$lookup": {
                "from": "clubs",
                "localField": "clubservice.club",
                "foreignField": "_id",
                "as": "club",
            }
        },
        {"$unwind": "$club"},
        {
            "$project": {
                "_id": 1,
                "userId": 1,
                "created_at": 1,
                "price": 1,
                "paidFor.totalPrice": 1,
                "paidFor.visits.clubServiceId": 1,
                "paidFor.visits.visitsCount": 1,
                "clubservice._id": 1,
                "clubservice.price": 1,
                "club._id": 1,
                "club.name": 1,
                "club.type": 1,
            }
        },
        {"$sort": {"created_at": -1}},
    ]
    return list(transactions_col.aggregate(pipeline))


def get_club_names_map(db, club_ids: list[Any]) -> dict[Any, str]:
    """Возвращает словарь clubId -> club name."""
    if not club_ids:
        return {}

    clubs_col = get_collection(db, "clubs")
    clubs = clubs_col.find({"_id": {"$in": club_ids}}, {"_id": 1, "name": 1})
    return {club["_id"]: club["name"] for club in clubs}


def get_non_recurrent_subscription_plans(db) -> list[dict[str, Any]]:
    """Возвращает активные нерекуррентные планы абонементов."""
    subscriptions_col = get_collection(db, "subscriptions")
    return list(
        subscriptions_col.find(
            {"isRecurrent": {"$ne": True}, "isDeleted": False},
            {"_id": 1, "name": 1, "interval": 1, "clubId": 1},
        )
    )


def get_active_user_subscriptions(
    db,
    subscription_ids: list[Any],
    *,
    now: datetime,
    since: datetime,
    limit: int,
) -> list[dict[str, Any]]:
    """Возвращает пользовательские абонементы, активные в анализируемом периоде."""
    usersubscriptions_col = get_collection(db, "usersubscriptions")
    return list(
        usersubscriptions_col.find(
            {
                "subscriptionId": {"$in": subscription_ids},
                "isDeleted": False,
                "startDate": {"$lte": now},
                "$or": [
                    {"endDate": {"$gte": since}},
                    {"endDate": None},
                ],
            },
            {"user": 1, "startDate": 1, "endDate": 1, "subscriptionId": 1},
        ).limit(limit)
    )


def get_access_entries_for_users(
    db,
    user_ids: list[Any],
    *,
    since: datetime,
    now: datetime,
) -> list[dict[str, Any]]:
    """Возвращает входы в клуб по списку пользователей за период."""
    accesscontrols_col = get_collection(db, "accesscontrols")
    return list(
        accesscontrols_col.find(
            {
                "user": {"$in": user_ids},
                "type": "enter",
                "err": {"$exists": False},
                "accessType": {"$ne": "staff"},
                "time": {"$gte": since, "$lte": now},
            },
            {"_id": 1, "user": 1, "time": 1, "accessType": 1, "club": 1, "visits": 1},
        )
    )
