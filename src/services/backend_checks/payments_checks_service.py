"""Вычисление нарушений backend-check сценариев в домене payments."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from bson import ObjectId

from src.repositories.payments.checks_repository import (
    get_access_entries_for_users,
    get_bonus_pay_history_records,
    get_bonus_spend_transactions,
    get_recent_subscription_purchase_transactions,
    get_recent_visit_bonus_records,
    get_subscriptions_map_by_ids,
    get_active_user_subscriptions,
    get_club_names_map,
    get_discounts_map_by_ids,
    get_forbidden_bonus_spend_transactions,
    get_freeze_days_transactions,
    get_internal_error_transactions,
    get_non_recurrent_subscription_plans,
    get_subscription_bonus_history_records,
    get_subscription_bonus_spend_transactions,
    get_subscription_plans_map_by_ids,
    get_transactions_with_promo_code,
    get_visit_bonus_records_for_users,
    get_visit_bonus_user_ids,
    get_visit_transactions_with_club_type,
)


FORBIDDEN_BONUS_PRODUCT_TYPES = [
    "recurrent",
    "rabbitHoleV2",
    "saveCard",
    "fillBalance",
    "freezing",
]

PRICE_TOLERANCE = 1
BONUS_PAY_TIME_TOLERANCE_SEC = 300
BONUS_PAY_AMOUNT_TOLERANCE = 1
DEDUCTION_LIMITS_BY_INTERVAL = {
    365: 0.20,
    180: 0.10,
    90: 0.07,
    30: 0.05,
}
SUBSCRIPTION_BONUS_ACCRUAL_RATES = {
    365: 0.10,
    180: 0.07,
}
SUBSCRIPTION_BONUS_NO_ACCRUAL_INTERVALS = {90, 30}
SUBSCRIPTION_BONUS_SAMPLE_SIZE = 300
SUBSCRIPTION_BONUS_TIME_TOLERANCE_SEC = 1800
SUBSCRIPTION_BONUS_AMOUNT_TOLERANCE = 2
VISIT_BONUS_SAMPLE_SIZE = 500
VISIT_BONUS_FORWARD_SAMPLE_USERS = 200
VISIT_BONUS_TIME_TOLERANCE_SEC = 5
EXPECTED_VISIT_TOTAL_PRICE_BY_CLUB_TYPE = {
    "GO": 5000,
    "Girls": 10000,
}
EXPECTED_VISIT_UNIT_PRICE_BY_CLUB_NAME_FRAGMENT = {
    "HIGHVILL": 30000,
    "AKBULAK": 30000,
    "SEMEY": 30000,
    "GREEN MALL": 30000,
    "SADU": 40000,
    "ATYRAU": 25000,
    "NURSAT": 10000,
    "TEMIRTAU": 10000,
    "AL FARABI": 10000,
    "GAGARIN": 10000,
    "SAMAL": 10000,
}


@dataclass(frozen=True)
class FreezeDaysDuplicateViolation:
    user_subscription_id: str
    transactions: list[dict[str, Any]]


@dataclass(frozen=True)
class FreezeDaysDuplicateCheckResult:
    period_days: int
    since: datetime
    transactions_count: int
    unique_subscriptions_count: int
    skipped_without_subscription: int
    violations: list[FreezeDaysDuplicateViolation]


@dataclass(frozen=True)
class ForbiddenBonusSpendViolationGroup:
    product_type: str
    transactions: list[dict[str, Any]]


@dataclass(frozen=True)
class ForbiddenBonusSpendCheckResult:
    period_days: int
    since: datetime
    forbidden_types: list[str]
    violations_count: int
    violation_groups: list[ForbiddenBonusSpendViolationGroup]


@dataclass(frozen=True)
class BonusDeductionConsistencyViolation:
    tx_id: str
    user_id: str
    bonuses_spent: int | float
    created_at: datetime | None
    product_type: str
    price: Any
    user_pay_count: int


@dataclass(frozen=True)
class BonusDeductionConsistencyCheckResult:
    period_days: int
    since: datetime
    transactions_count: int
    pay_records_count: int
    users_count: int
    time_tolerance_sec: int
    amount_tolerance: int | float
    violations: list[BonusDeductionConsistencyViolation]


@dataclass(frozen=True)
class BonusDeductionLimitViolation:
    tx_id: str
    product_type: str
    plan_name: str
    interval: int
    full_price: int | float
    paid_price: Any
    bonuses_spent: int | float
    actual_pct: float
    limit_pct: int
    created_at: datetime | None
    club_id: Any


@dataclass(frozen=True)
class BonusDeductionLimitIntervalStat:
    interval: int | None
    transactions_count: int
    violations_count: int


@dataclass(frozen=True)
class BonusDeductionLimitsCheckResult:
    period_days: int
    since: datetime
    transactions_count: int
    plans_count: int
    skipped_unknown_plan_count: int
    interval_stats: list[BonusDeductionLimitIntervalStat]
    violations: list[BonusDeductionLimitViolation]


@dataclass(frozen=True)
class SubscriptionBonusAccrualMissingViolation:
    tx_id: str
    plan_name: str
    interval: int
    paid_price: Any
    full_price: Any
    expected_amount: int | float
    created_at: datetime | None


@dataclass(frozen=True)
class SubscriptionBonusAccrualWrongAmountViolation:
    tx_id: str
    plan_name: str
    interval: int
    paid_price: Any
    full_price: Any
    bonuses_spent: int | float
    base_price: Any
    has_promo: bool
    expected_amount: int | float
    actual_amount: int | float
    diff: int | float
    created_at: datetime | None


@dataclass(frozen=True)
class SubscriptionBonusAccrualUnexpectedViolation:
    tx_id: str
    plan_name: str
    interval: int
    paid_price: Any
    bonus_amount: int | float
    created_at: datetime | None


@dataclass(frozen=True)
class SubscriptionBonusAccrualIntervalStat:
    interval: int | None
    transactions_count: int


@dataclass(frozen=True)
class SubscriptionBonusAccrualCheckResult:
    period_days: int
    since: datetime
    sample_size: int
    transactions_count: int
    plans_count: int
    bonus_records_count: int
    skipped_count: int
    interval_stats: list[SubscriptionBonusAccrualIntervalStat]
    missing_bonus: list[SubscriptionBonusAccrualMissingViolation]
    wrong_amount: list[SubscriptionBonusAccrualWrongAmountViolation]
    unexpected_bonus: list[SubscriptionBonusAccrualUnexpectedViolation]


@dataclass(frozen=True)
class VisitBonusDuplicateDayViolation:
    user_id: str
    date: Any
    bonus_ids: list[str]


@dataclass(frozen=True)
class VisitBonusMissingVisitViolation:
    bonus_id: str
    user_id: str
    amount: Any
    time: datetime | None


@dataclass(frozen=True)
class VisitBonusAccrualCheckResult:
    period_days: int
    since: datetime
    sample_size: int
    bonus_records_count: int
    access_entries_count: int
    duplicate_days: list[VisitBonusDuplicateDayViolation]
    missing_visit_bonuses: list[VisitBonusMissingVisitViolation]


@dataclass(frozen=True)
class VisitBonusCoverageViolation:
    user_id: str
    date: Any


@dataclass(frozen=True)
class VisitBonusCoverageCheckResult:
    period_days: int
    since: datetime
    sample_users_limit: int
    sample_users_count: int
    bonus_days_count: int
    visit_days_count: int
    violations: list[VisitBonusCoverageViolation]


@dataclass(frozen=True)
class BonusUsageMonitoringClientStat:
    user_id: str
    transactions_count: int
    bonuses_spent_total: int | float
    first_transaction_at: datetime | None
    last_transaction_at: datetime | None
    spent_on_summary: str


@dataclass(frozen=True)
class BonusUsageMonitoringProductStat:
    product_type: str
    product_name: str
    transactions_count: int
    bonuses_spent_total: int | float


@dataclass(frozen=True)
class BonusUsageMonitoringTransaction:
    tx_id: str
    user_id: str
    created_at: datetime | None
    product_type: str
    product_name: str
    product_meta: str
    price: Any
    bonuses_spent: int | float


@dataclass(frozen=True)
class BonusUsageMonitoringResult:
    period_days: int
    since: datetime
    transactions_count: int
    unique_clients_count: int
    total_bonuses_spent: int | float
    clients: list[BonusUsageMonitoringClientStat]
    products: list[BonusUsageMonitoringProductStat]
    product_type_counts: dict[str, int]
    transactions: list[BonusUsageMonitoringTransaction]


@dataclass(frozen=True)
class PromoCodeDiscountViolation:
    kind: str
    label: str
    tx_id: str
    detail: str
    date: datetime | None
    discount_id: str
    discount_name: str | None = None
    user_id: str | None = None


@dataclass(frozen=True)
class PromoCodeDiscountCheckResult:
    period_days: int
    since: datetime
    transactions_count: int
    unique_discount_count: int
    violations: list[PromoCodeDiscountViolation]


@dataclass(frozen=True)
class InternalErrorClubGroup:
    club_name: str
    transactions: list[dict[str, Any]]


@dataclass(frozen=True)
class InternalErrorTransactionsCheckResult:
    period_days: int
    since: datetime
    error_transactions_count: int
    affected_clubs_count: int
    club_groups: list[InternalErrorClubGroup]
    product_type_counts: dict[str, int]


@dataclass(frozen=True)
class SubscriptionAccessViolation:
    entry_id: str
    user_id: str
    time: datetime
    access_type: str | None
    club_id: Any
    plan_id: Any


@dataclass(frozen=True)
class SubscriptionPlanWithoutClubEntry:
    entry_id: str
    user_id: str
    time: datetime
    club_id: Any
    plan_id: Any


@dataclass(frozen=True)
class SubscriptionAccessTypeCheckResult:
    period_days: int
    since: datetime
    sample_size: int
    plans_count: int
    sampled_subscriptions_count: int
    sampled_users_count: int
    entries_count: int
    entries_in_window_count: int
    outside_window_count: int
    violations: list[SubscriptionAccessViolation]
    no_clubid_entries: list[SubscriptionPlanWithoutClubEntry]
    by_club: dict[Any, dict[str, int]]
    by_plan: dict[Any, dict[str, int]]
    plan_map: dict[Any, dict[str, Any]]
    club_name_map: dict[Any, str]


@dataclass(frozen=True)
class VisitPriceViolation:
    tx_id: str
    user_id: str | None
    created_at: datetime | None
    club_name: str
    club_type: str
    club_id: Any
    club_service_id: Any
    visits_count: Any
    expected_unit_price: int | float
    expected_total_price: int | float
    actual_total_price: Any
    clubservice_price: Any


@dataclass(frozen=True)
class VisitPriceCheckResult:
    period_days: int
    since: datetime
    transactions_count: int
    checked_transactions_count: int
    violations: list[VisitPriceViolation]


def _normalize_club_name(value: str | None) -> str:
    """Normalizes club name for keyword-based price rules."""
    if not value:
        return ""
    normalized = value.upper().replace("-", " ")
    return " ".join(normalized.split())


def _resolve_expected_visit_unit_price(
    club_name: str | None,
    club_type: str | None,
    expected_price_by_club_name_fragment: dict[str, int | float],
    expected_price_by_club_type: dict[str, int | float],
) -> int | float | None:
    """Resolves expected unit price, prioritizing specific club rules over club type."""
    normalized_club_name = _normalize_club_name(club_name)
    if club_type == "Fitness":
        for fragment, price in expected_price_by_club_name_fragment.items():
            if fragment in normalized_club_name:
                return price
    if club_type in expected_price_by_club_type:
        return expected_price_by_club_type[club_type]
    return None


def run_freeze_days_no_duplicate_check(
    db,
    period_days: int,
    *,
    now: datetime | None = None,
) -> FreezeDaysDuplicateCheckResult:
    """Проверяет, что один абонемент не замораживали несколько раз."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    transactions = get_freeze_days_transactions(db, since=since)

    grouped_by_subscription: dict[str, list[dict[str, Any]]] = defaultdict(list)
    skipped_without_subscription = 0

    for transaction in transactions:
        user_subscription_id = (
            transaction.get("paidFor", {})
            .get("freezing", {})
            .get("userSubscription")
        )
        if not user_subscription_id:
            skipped_without_subscription += 1
            continue
        grouped_by_subscription[str(user_subscription_id)].append(transaction)

    violations = [
        FreezeDaysDuplicateViolation(
            user_subscription_id=user_subscription_id,
            transactions=subscription_transactions,
        )
        for user_subscription_id, subscription_transactions in grouped_by_subscription.items()
        if len(subscription_transactions) > 1
    ]
    violations.sort(key=lambda item: len(item.transactions), reverse=True)

    return FreezeDaysDuplicateCheckResult(
        period_days=period_days,
        since=since,
        transactions_count=len(transactions),
        unique_subscriptions_count=len(grouped_by_subscription),
        skipped_without_subscription=skipped_without_subscription,
        violations=violations,
    )


def run_forbidden_bonus_spend_check(
    db,
    period_days: int,
    *,
    forbidden_types: list[str] | None = None,
    now: datetime | None = None,
) -> ForbiddenBonusSpendCheckResult:
    """Проверяет, что запрещённые типы транзакций не списывают бонусы."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    forbidden_product_types = forbidden_types or FORBIDDEN_BONUS_PRODUCT_TYPES
    violations = get_forbidden_bonus_spend_transactions(
        db,
        since=since,
        forbidden_types=forbidden_product_types,
    )

    violations_by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for violation in violations:
        violations_by_type[violation.get("productType", "—")].append(violation)

    grouped_violations = [
        ForbiddenBonusSpendViolationGroup(
            product_type=product_type,
            transactions=product_transactions,
        )
        for product_type, product_transactions in violations_by_type.items()
    ]
    grouped_violations.sort(key=lambda item: len(item.transactions), reverse=True)

    return ForbiddenBonusSpendCheckResult(
        period_days=period_days,
        since=since,
        forbidden_types=list(forbidden_product_types),
        violations_count=len(violations),
        violation_groups=grouped_violations,
    )


def run_bonus_deduction_consistency_check(
    db,
    period_days: int,
    *,
    time_tolerance_sec: int = BONUS_PAY_TIME_TOLERANCE_SEC,
    amount_tolerance: int | float = BONUS_PAY_AMOUNT_TOLERANCE,
    now: datetime | None = None,
) -> BonusDeductionConsistencyCheckResult:
    """Проверяет, что списание бонусов отражено PAY-записью в userbonuseshistories."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    transactions = get_bonus_spend_transactions(db, since=since)

    if not transactions:
        return BonusDeductionConsistencyCheckResult(
            period_days=period_days,
            since=since,
            transactions_count=0,
            pay_records_count=0,
            users_count=0,
            time_tolerance_sec=time_tolerance_sec,
            amount_tolerance=amount_tolerance,
            violations=[],
        )

    user_ids = list({transaction["userId"] for transaction in transactions if transaction.get("userId")})
    times = [transaction["created_at"] for transaction in transactions if transaction.get("created_at")]
    if times:
        window_start = min(times) - timedelta(seconds=time_tolerance_sec)
        window_end = max(times) + timedelta(seconds=time_tolerance_sec)
    else:
        window_start = since
        window_end = current_time

    pay_records = get_bonus_pay_history_records(
        db,
        user_ids=user_ids,
        window_start=window_start,
        window_end=window_end,
    )

    pay_lookup: dict[str, list[tuple[datetime, Any, Any]]] = defaultdict(list)
    for pay_record in pay_records:
        user_id = pay_record.get("user")
        pay_time = pay_record.get("time")
        if user_id is None or pay_time is None:
            continue
        pay_lookup[str(user_id)].append(
            (pay_time, pay_record.get("amount"), pay_record.get("_id"))
        )

    violations: list[BonusDeductionConsistencyViolation] = []
    for transaction in transactions:
        user_id = str(transaction.get("userId", ""))
        bonuses_spent = transaction.get("bonusesSpent", 0)
        tx_time = transaction.get("created_at")
        expected_amount = -bonuses_spent
        user_pays = pay_lookup.get(user_id, [])

        matched = False
        if tx_time is not None:
            for pay_time, pay_amount, _pay_id in user_pays:
                time_diff = abs((pay_time - tx_time).total_seconds())
                if (
                    time_diff <= time_tolerance_sec
                    and pay_amount is not None
                    and abs(pay_amount - expected_amount) <= amount_tolerance
                ):
                    matched = True
                    break

        if not matched:
            violations.append(
                BonusDeductionConsistencyViolation(
                    tx_id=str(transaction["_id"]),
                    user_id=user_id,
                    bonuses_spent=bonuses_spent,
                    created_at=tx_time,
                    product_type=transaction.get("productType", "—"),
                    price=transaction.get("price"),
                    user_pay_count=len(user_pays),
                )
            )

    return BonusDeductionConsistencyCheckResult(
        period_days=period_days,
        since=since,
        transactions_count=len(transactions),
        pay_records_count=len(pay_records),
        users_count=len(user_ids),
        time_tolerance_sec=time_tolerance_sec,
        amount_tolerance=amount_tolerance,
        violations=violations,
    )


def run_bonus_deduction_limits_check(
    db,
    period_days: int,
    *,
    deduction_limits_by_interval: dict[int, float] | None = None,
    now: datetime | None = None,
) -> BonusDeductionLimitsCheckResult:
    """Checks that bonus deductions do not exceed the configured plan percentage limits."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    deduction_limits = deduction_limits_by_interval or DEDUCTION_LIMITS_BY_INTERVAL

    transactions = get_subscription_bonus_spend_transactions(db, since=since)
    if not transactions:
        return BonusDeductionLimitsCheckResult(
            period_days=period_days,
            since=since,
            transactions_count=0,
            plans_count=0,
            skipped_unknown_plan_count=0,
            interval_stats=[],
            violations=[],
        )

    subscription_ids = {
        subscription.get("subscriptionId")
        for transaction in transactions
        for subscription in (transaction.get("paidFor") or {}).get("subscription", [])[:1]
        if subscription.get("subscriptionId") is not None
    }
    plan_map = get_subscription_plans_map_by_ids(
        db,
        subscription_ids=[subscription_id for subscription_id in subscription_ids if subscription_id is not None],
    )

    interval_stats: dict[int | None, dict[str, int]] = defaultdict(
        lambda: {"transactions": 0, "violations": 0}
    )
    violations: list[BonusDeductionLimitViolation] = []
    skipped_unknown_plan_count = 0

    for transaction in transactions:
        subscriptions = (transaction.get("paidFor") or {}).get("subscription", [])
        if not subscriptions:
            continue

        subscription_item = subscriptions[0] or {}
        full_price = subscription_item.get("price")
        subscription_id = subscription_item.get("subscriptionId")
        if not full_price or not subscription_id:
            continue

        plan = plan_map.get(subscription_id)
        if not plan:
            skipped_unknown_plan_count += 1
            interval_stats[None]["transactions"] += 1
            continue

        interval = plan.get("interval")
        if interval not in deduction_limits:
            skipped_unknown_plan_count += 1
            interval_stats[interval]["transactions"] += 1
            continue

        bonuses_spent = transaction.get("bonusesSpent", 0) or 0
        actual_fraction = bonuses_spent / full_price
        max_fraction = deduction_limits[interval]

        interval_stats[interval]["transactions"] += 1
        if actual_fraction > max_fraction + 1e-9:
            interval_stats[interval]["violations"] += 1
            violations.append(
                BonusDeductionLimitViolation(
                    tx_id=str(transaction["_id"]),
                    product_type=transaction.get("productType") or "—",
                    plan_name=plan.get("name") or "—",
                    interval=interval,
                    full_price=full_price,
                    paid_price=transaction.get("price"),
                    bonuses_spent=bonuses_spent,
                    actual_pct=round(actual_fraction * 100, 2),
                    limit_pct=int(max_fraction * 100),
                    created_at=transaction.get("created_at"),
                    club_id=transaction.get("clubId"),
                )
            )

    normalized_interval_stats = [
        BonusDeductionLimitIntervalStat(
            interval=interval,
            transactions_count=stat["transactions"],
            violations_count=stat["violations"],
        )
        for interval, stat in sorted(
            interval_stats.items(),
            key=lambda item: (
                item[0] is None,
                10_000 if item[0] is None else item[0],
            ),
        )
    ]

    return BonusDeductionLimitsCheckResult(
        period_days=period_days,
        since=since,
        transactions_count=len(transactions),
        plans_count=len(plan_map),
        skipped_unknown_plan_count=skipped_unknown_plan_count,
        interval_stats=normalized_interval_stats,
        violations=violations,
    )


def run_subscription_bonus_accrual_check(
    db,
    period_days: int,
    *,
    sample_size: int = SUBSCRIPTION_BONUS_SAMPLE_SIZE,
    time_tolerance_sec: int = SUBSCRIPTION_BONUS_TIME_TOLERANCE_SEC,
    amount_tolerance: int | float = SUBSCRIPTION_BONUS_AMOUNT_TOLERANCE,
    accrual_rates: dict[int, float] | None = None,
    no_accrual_intervals: set[int] | None = None,
    now: datetime | None = None,
) -> SubscriptionBonusAccrualCheckResult:
    """Checks that subscription purchase bonus accruals match plan rules and amounts."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    expected_accrual_rates = accrual_rates or SUBSCRIPTION_BONUS_ACCRUAL_RATES
    expected_no_accrual_intervals = no_accrual_intervals or SUBSCRIPTION_BONUS_NO_ACCRUAL_INTERVALS

    transactions = get_recent_subscription_purchase_transactions(
        db,
        since=since,
        limit=sample_size,
    )
    if not transactions:
        return SubscriptionBonusAccrualCheckResult(
            period_days=period_days,
            since=since,
            sample_size=sample_size,
            transactions_count=0,
            plans_count=0,
            bonus_records_count=0,
            skipped_count=0,
            interval_stats=[],
            missing_bonus=[],
            wrong_amount=[],
            unexpected_bonus=[],
        )

    subscription_ids = {
        subscription.get("subscriptionId")
        for transaction in transactions
        for subscription in (transaction.get("paidFor") or {}).get("subscription", [])[:1]
        if subscription.get("subscriptionId") is not None
    }
    plan_map = get_subscription_plans_map_by_ids(
        db,
        subscription_ids=[subscription_id for subscription_id in subscription_ids if subscription_id is not None],
    )

    user_ids = list({transaction["userId"] for transaction in transactions if transaction.get("userId")})
    times = [transaction["created_at"] for transaction in transactions if transaction.get("created_at") is not None]
    if times:
        window_start = min(times) - timedelta(seconds=time_tolerance_sec)
        window_end = max(times) + timedelta(seconds=time_tolerance_sec)
    else:
        window_start = since
        window_end = current_time

    bonus_records = get_subscription_bonus_history_records(
        db,
        user_ids=user_ids,
        window_start=window_start,
        window_end=window_end,
    )
    bonus_lookup: dict[str, list[tuple[datetime, Any, Any]]] = defaultdict(list)
    for bonus_record in bonus_records:
        user_id = bonus_record.get("user")
        bonus_time = bonus_record.get("time")
        if user_id is None or bonus_time is None:
            continue
        bonus_lookup[str(user_id)].append(
            (bonus_time, bonus_record.get("amount"), bonus_record.get("_id"))
        )

    interval_counts: dict[int | None, int] = defaultdict(int)
    missing_bonus: list[SubscriptionBonusAccrualMissingViolation] = []
    wrong_amount: list[SubscriptionBonusAccrualWrongAmountViolation] = []
    unexpected_bonus: list[SubscriptionBonusAccrualUnexpectedViolation] = []
    skipped_count = 0

    for transaction in transactions:
        subscriptions = (transaction.get("paidFor") or {}).get("subscription", [])
        subscription_id = subscriptions[0].get("subscriptionId") if subscriptions else None
        plan = plan_map.get(subscription_id) if subscription_id else None

        interval = plan.get("interval") if plan else None
        interval_counts[interval] += 1

        if not plan:
            skipped_count += 1
            continue

        if plan.get("isRecurrent", False):
            skipped_count += 1
            continue

        if interval not in expected_accrual_rates and interval not in expected_no_accrual_intervals:
            skipped_count += 1
            continue

        tx_time = transaction.get("created_at")
        paid_price = transaction.get("price", 0)
        subscription_price = subscriptions[0].get("price", 0) if subscriptions else 0
        if paid_price == 0 or subscription_price == 0 or tx_time is None:
            skipped_count += 1
            continue

        user_id = str(transaction.get("userId", ""))
        bonuses_spent = transaction.get("bonusesSpent", 0) or 0
        has_promo = bool((transaction.get("paidFor") or {}).get("discountId"))
        base_price = paid_price

        candidates = [
            (bonus_time, bonus_amount, bonus_id)
            for bonus_time, bonus_amount, bonus_id in bonus_lookup.get(user_id, [])
            if abs((bonus_time - tx_time).total_seconds()) <= time_tolerance_sec
        ]

        if interval in expected_accrual_rates:
            expected_amount = round(base_price * expected_accrual_rates[interval])
            if not candidates:
                missing_bonus.append(
                    SubscriptionBonusAccrualMissingViolation(
                        tx_id=str(transaction["_id"]),
                        plan_name=plan.get("name") or "—",
                        interval=interval,
                        paid_price=paid_price,
                        full_price=subscription_price,
                        expected_amount=expected_amount,
                        created_at=tx_time,
                    )
                )
                continue

            best_bonus = min(candidates, key=lambda item: abs((item[1] or 0) - expected_amount))
            actual_amount = best_bonus[1] or 0
            if abs(actual_amount - expected_amount) > amount_tolerance:
                wrong_amount.append(
                    SubscriptionBonusAccrualWrongAmountViolation(
                        tx_id=str(transaction["_id"]),
                        plan_name=plan.get("name") or "—",
                        interval=interval,
                        paid_price=paid_price,
                        full_price=subscription_price,
                        bonuses_spent=bonuses_spent,
                        base_price=base_price,
                        has_promo=has_promo,
                        expected_amount=expected_amount,
                        actual_amount=actual_amount,
                        diff=actual_amount - expected_amount,
                        created_at=tx_time,
                    )
                )
        elif candidates:
            unexpected_bonus.append(
                SubscriptionBonusAccrualUnexpectedViolation(
                    tx_id=str(transaction["_id"]),
                    plan_name=plan.get("name") or "—",
                    interval=interval,
                    paid_price=paid_price,
                    bonus_amount=candidates[0][1] or 0,
                    created_at=tx_time,
                )
            )

    interval_stats = [
        SubscriptionBonusAccrualIntervalStat(
            interval=interval,
            transactions_count=count,
        )
        for interval, count in sorted(
            interval_counts.items(),
            key=lambda item: (-item[1], item[0] is None, item[0] or 0),
        )
    ]

    return SubscriptionBonusAccrualCheckResult(
        period_days=period_days,
        since=since,
        sample_size=sample_size,
        transactions_count=len(transactions),
        plans_count=len(plan_map),
        bonus_records_count=len(bonus_records),
        skipped_count=skipped_count,
        interval_stats=interval_stats,
        missing_bonus=missing_bonus,
        wrong_amount=wrong_amount,
        unexpected_bonus=unexpected_bonus,
    )


def _time_bucket(dt: datetime, sec: int) -> int:
    """Floors datetime to a stable time bucket used for visit bonus matching."""
    return (int(dt.timestamp()) // sec) * sec


def run_visit_bonus_accrual_check(
    db,
    period_days: int,
    *,
    sample_size: int = VISIT_BONUS_SAMPLE_SIZE,
    time_tolerance_sec: int = VISIT_BONUS_TIME_TOLERANCE_SEC,
    now: datetime | None = None,
) -> VisitBonusAccrualCheckResult:
    """Checks that VISIT bonuses map to real visits and are not duplicated per day."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)

    visit_bonuses = get_recent_visit_bonus_records(
        db,
        since=since,
        limit=sample_size,
    )
    if not visit_bonuses:
        return VisitBonusAccrualCheckResult(
            period_days=period_days,
            since=since,
            sample_size=sample_size,
            bonus_records_count=0,
            access_entries_count=0,
            duplicate_days=[],
            missing_visit_bonuses=[],
        )

    day_map: dict[tuple[str, Any], list[str]] = defaultdict(list)
    for bonus in visit_bonuses:
        bonus_time = bonus.get("time")
        if bonus_time is None:
            continue
        key = (str(bonus.get("user")), bonus_time.date())
        day_map[key].append(str(bonus["_id"]))

    duplicate_days = [
        VisitBonusDuplicateDayViolation(user_id=user_id, date=date, bonus_ids=bonus_ids)
        for (user_id, date), bonus_ids in day_map.items()
        if len(bonus_ids) > 1
    ]
    duplicate_days.sort(key=lambda item: (-len(item.bonus_ids), item.user_id, str(item.date)))

    user_ids = list({bonus["user"] for bonus in visit_bonuses if bonus.get("user") is not None})
    bonus_times = [bonus["time"] for bonus in visit_bonuses if bonus.get("time") is not None]
    if bonus_times:
        window_start = min(bonus_times) - timedelta(seconds=time_tolerance_sec)
        window_end = max(bonus_times) + timedelta(seconds=time_tolerance_sec)
    else:
        window_start = since
        window_end = current_time

    entries = get_access_entries_for_users(
        db,
        user_ids=user_ids,
        since=window_start,
        now=window_end,
    )
    entry_set = {
        (str(entry["user"]), _time_bucket(entry["time"], time_tolerance_sec))
        for entry in entries
        if entry.get("user") is not None and entry.get("time") is not None
    }

    missing_visit_bonuses: list[VisitBonusMissingVisitViolation] = []
    for bonus in visit_bonuses:
        bonus_time = bonus.get("time")
        user_id = str(bonus.get("user"))
        if bonus_time is None:
            continue
        bucket = _time_bucket(bonus_time, time_tolerance_sec)
        found = any(
            (user_id, bucket + offset) in entry_set
            for offset in (-time_tolerance_sec, 0, time_tolerance_sec)
        )
        if not found:
            missing_visit_bonuses.append(
                VisitBonusMissingVisitViolation(
                    bonus_id=str(bonus["_id"]),
                    user_id=user_id,
                    amount=bonus.get("amount"),
                    time=bonus_time,
                )
            )

    return VisitBonusAccrualCheckResult(
        period_days=period_days,
        since=since,
        sample_size=sample_size,
        bonus_records_count=len(visit_bonuses),
        access_entries_count=len(entries),
        duplicate_days=duplicate_days,
        missing_visit_bonuses=missing_visit_bonuses,
    )


def run_visit_bonus_coverage_check(
    db,
    period_days: int,
    *,
    sample_users_limit: int = VISIT_BONUS_FORWARD_SAMPLE_USERS,
    now: datetime | None = None,
) -> VisitBonusCoverageCheckResult:
    """Checks that visit days for sampled bonus users have at least one VISIT bonus."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)

    bonus_user_ids = get_visit_bonus_user_ids(
        db,
        since=since,
        limit=sample_users_limit,
    )
    if not bonus_user_ids:
        return VisitBonusCoverageCheckResult(
            period_days=period_days,
            since=since,
            sample_users_limit=sample_users_limit,
            sample_users_count=0,
            bonus_days_count=0,
            visit_days_count=0,
            violations=[],
        )

    bonuses = get_visit_bonus_records_for_users(
        db,
        since=since,
        user_ids=bonus_user_ids,
    )
    entries = get_access_entries_for_users(
        db,
        user_ids=bonus_user_ids,
        since=since,
        now=current_time,
    )

    bonus_days = {
        (str(bonus["user"]), bonus["time"].date())
        for bonus in bonuses
        if bonus.get("user") is not None and bonus.get("time") is not None
    }
    visit_days = {
        (str(entry["user"]), entry["time"].date())
        for entry in entries
        if entry.get("user") is not None and entry.get("time") is not None
    }
    violations = [
        VisitBonusCoverageViolation(user_id=user_id, date=date)
        for user_id, date in sorted(visit_days - bonus_days)
    ]

    return VisitBonusCoverageCheckResult(
        period_days=period_days,
        since=since,
        sample_users_limit=sample_users_limit,
        sample_users_count=len(bonus_user_ids),
        bonus_days_count=len(bonus_days),
        visit_days_count=len(visit_days),
        violations=violations,
    )


def _normalize_object_id(value: Any) -> ObjectId | None:
    """Пытается привести значение к ObjectId."""
    if isinstance(value, ObjectId):
        return value
    if value is None:
        return None
    try:
        return ObjectId(str(value))
    except Exception:
        return None


def _normalize_datetime(dt: datetime) -> datetime:
    """Убирает tzinfo для безопасного сравнения дат из Mongo."""
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def _to_display_string(value: Any) -> str:
    """Converts optional values to a stable display string for reports."""
    if value is None or value == "":
        return "—"
    return str(value)


def _extract_product_name_and_meta(
    transaction: dict[str, Any],
    subscriptions_map: dict[Any, dict[str, Any]],
) -> tuple[str, str]:
    """Best-effort resolver for transaction product labels used in monitoring reports."""
    paid_for = transaction.get("paidFor") or {}

    subscriptions = paid_for.get("subscription") or []
    if subscriptions:
        subscription_item = subscriptions[0] or {}
        subscription_id = subscription_item.get("subscriptionId")
        subscription = subscriptions_map.get(subscription_id) if subscription_id else None
        product_name = (
            (subscription or {}).get("name")
            or subscription_item.get("name")
            or "—"
        )
        meta_parts = []
        interval = (subscription or {}).get("interval")
        if interval is not None:
            meta_parts.append(f"interval={interval}")
        if subscription_id is not None:
            meta_parts.append(f"subscriptionId={subscription_id}")
        return product_name, ", ".join(meta_parts) or "—"

    visits = paid_for.get("visits") or []
    if visits:
        visit_item = visits[0] if isinstance(visits, list) else visits
        meta_parts = []
        club_service_id = visit_item.get("clubServiceId")
        visits_count = visit_item.get("visitsCount")
        if club_service_id is not None:
            meta_parts.append(f"clubServiceId={club_service_id}")
        if visits_count is not None:
            meta_parts.append(f"visitsCount={visits_count}")
        return "—", ", ".join(meta_parts) or "—"

    freezing = paid_for.get("freezing") or {}
    if freezing:
        meta_parts = []
        user_subscription = freezing.get("userSubscription")
        freeze_days = freezing.get("days")
        if user_subscription is not None:
            meta_parts.append(f"userSubscription={user_subscription}")
        if freeze_days is not None:
            meta_parts.append(f"days={freeze_days}")
        return "—", ", ".join(meta_parts) or "—"

    club_id = transaction.get("clubId")
    if club_id is not None:
        return "—", f"clubId={club_id}"

    return "—", "—"


def run_bonus_usage_monitoring(
    db,
    period_days: int,
    *,
    now: datetime | None = None,
) -> BonusUsageMonitoringResult:
    """Builds a monitoring snapshot for bonus usage by clients and products."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    transactions = get_bonus_spend_transactions(db, since=since)

    if not transactions:
        return BonusUsageMonitoringResult(
            period_days=period_days,
            since=since,
            transactions_count=0,
            unique_clients_count=0,
            total_bonuses_spent=0,
            clients=[],
            products=[],
            product_type_counts={},
            transactions=[],
        )

    subscription_ids = {
        (transaction.get("paidFor") or {}).get("subscription", [{}])[0].get("subscriptionId")
        for transaction in transactions
        if (transaction.get("paidFor") or {}).get("subscription")
    }
    subscriptions_map = get_subscriptions_map_by_ids(
        db,
        subscription_ids=[subscription_id for subscription_id in subscription_ids if subscription_id is not None],
    )

    client_stats: dict[str, dict[str, int | float]] = defaultdict(
        lambda: {
            "transactions_count": 0,
            "bonuses_spent_total": 0,
            "first_transaction_at": None,
            "last_transaction_at": None,
        }
    )
    product_stats: dict[tuple[str, str], dict[str, int | float]] = defaultdict(
        lambda: {"transactions_count": 0, "bonuses_spent_total": 0}
    )
    product_type_counts: dict[str, int] = defaultdict(int)
    client_product_names: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    normalized_transactions: list[BonusUsageMonitoringTransaction] = []
    total_bonuses_spent = 0

    for transaction in transactions:
        bonuses_spent = transaction.get("bonusesSpent") or 0
        user_id = _to_display_string(transaction.get("userId"))
        product_type = transaction.get("productType") or "—"
        product_name, product_meta = _extract_product_name_and_meta(transaction, subscriptions_map)

        client_stats[user_id]["transactions_count"] += 1
        client_stats[user_id]["bonuses_spent_total"] += bonuses_spent
        created_at = transaction.get("created_at")
        first_transaction_at = client_stats[user_id]["first_transaction_at"]
        last_transaction_at = client_stats[user_id]["last_transaction_at"]
        if created_at is not None:
            if first_transaction_at is None or created_at < first_transaction_at:
                client_stats[user_id]["first_transaction_at"] = created_at
            if last_transaction_at is None or created_at > last_transaction_at:
                client_stats[user_id]["last_transaction_at"] = created_at
        product_label = product_name if product_name != "—" else product_type
        client_product_names[user_id][product_label] += 1

        product_key = (product_type, product_name)
        product_stats[product_key]["transactions_count"] += 1
        product_stats[product_key]["bonuses_spent_total"] += bonuses_spent
        product_type_counts[product_type] += 1
        total_bonuses_spent += bonuses_spent

        normalized_transactions.append(
            BonusUsageMonitoringTransaction(
                tx_id=str(transaction["_id"]),
                user_id=user_id,
                created_at=transaction.get("created_at"),
                product_type=product_type,
                product_name=product_name,
                product_meta=product_meta,
                price=transaction.get("price"),
                bonuses_spent=bonuses_spent,
            )
        )

    clients = [
            BonusUsageMonitoringClientStat(
                user_id=user_id,
                transactions_count=int(stats["transactions_count"]),
                bonuses_spent_total=stats["bonuses_spent_total"],
                first_transaction_at=stats["first_transaction_at"],
                last_transaction_at=stats["last_transaction_at"],
                spent_on_summary=", ".join(
                    (
                        f"{product} ({count})"
                        for product, count in sorted(
                            client_product_names[user_id].items(),
                            key=lambda item: (-item[1], item[0]),
                        )
                    )
                ) or "—",
            )
        for user_id, stats in sorted(
            client_stats.items(),
            key=lambda item: (-item[1]["transactions_count"], -item[1]["bonuses_spent_total"], item[0]),
        )
    ]
    products = [
        BonusUsageMonitoringProductStat(
            product_type=product_type,
            product_name=product_name,
            transactions_count=int(stats["transactions_count"]),
            bonuses_spent_total=stats["bonuses_spent_total"],
        )
        for (product_type, product_name), stats in sorted(
            product_stats.items(),
            key=lambda item: (
                -item[1]["bonuses_spent_total"],
                -item[1]["transactions_count"],
                item[0][0],
                item[0][1],
            ),
        )
    ]
    normalized_transactions.sort(
        key=lambda item: (
            item.created_at is None,
            item.created_at if item.created_at is not None else datetime.min,
        ),
        reverse=True,
    )

    return BonusUsageMonitoringResult(
        period_days=period_days,
        since=since,
        transactions_count=len(transactions),
        unique_clients_count=len(client_stats),
        total_bonuses_spent=total_bonuses_spent,
        clients=clients,
        products=products,
        product_type_counts=dict(
            sorted(product_type_counts.items(), key=lambda item: (-item[1], item[0]))
        ),
        transactions=normalized_transactions,
    )


def run_promo_code_discount_check(
    db,
    period_days: int,
    *,
    now: datetime | None = None,
) -> PromoCodeDiscountCheckResult:
    """Проверяет корректность применения промокодов в транзакциях."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    transactions = get_transactions_with_promo_code(db, since=since)

    raw_discount_ids = [
        transaction.get("paidFor", {}).get("discountId")
        for transaction in transactions
        if transaction.get("paidFor", {}).get("discountId")
    ]
    discount_object_ids = []
    for discount_id in raw_discount_ids:
        normalized = _normalize_object_id(discount_id)
        if normalized is not None:
            discount_object_ids.append(normalized)

    unique_discount_object_ids = list({discount_id for discount_id in discount_object_ids})
    discounts_map = get_discounts_map_by_ids(db, discount_ids=unique_discount_object_ids)

    violations: list[PromoCodeDiscountViolation] = []
    for transaction in transactions:
        paid_for = transaction.get("paidFor", {})
        discount_id_raw = paid_for.get("discountId")
        if not discount_id_raw:
            continue

        discount_id = str(discount_id_raw)
        transaction_id = str(transaction["_id"])
        transaction_date = transaction.get("created_at")
        user_id = str(transaction.get("userId", "—"))
        discount = discounts_map.get(discount_id)

        if not discount:
            violations.append(
                PromoCodeDiscountViolation(
                    kind="A",
                    label="Скидка не найдена",
                    tx_id=transaction_id,
                    discount_id=discount_id,
                    user_id=user_id,
                    date=transaction_date,
                    detail=f"discountId={discount_id} не найден в коллекции discounts",
                )
            )
            continue

        discount_name = discount.get("name", discount_id)

        if discount.get("isDeleted"):
            violations.append(
                PromoCodeDiscountViolation(
                    kind="B",
                    label="Скидка удалена",
                    tx_id=transaction_id,
                    discount_id=discount_id,
                    discount_name=discount_name,
                    user_id=user_id,
                    date=transaction_date,
                    detail=f"промокод {discount_name} помечен isDeleted=true",
                )
            )

        if transaction_date:
            start_date = discount.get("startDate")
            end_date = discount.get("endDate")
            if start_date and end_date:
                transaction_date_cmp = _normalize_datetime(transaction_date)
                start_cmp = _normalize_datetime(start_date)
                end_cmp = _normalize_datetime(end_date)
                if not (start_cmp <= transaction_date_cmp <= end_cmp):
                    violations.append(
                        PromoCodeDiscountViolation(
                            kind="C",
                            label="Скидка неактивна на дату транзакции",
                            tx_id=transaction_id,
                            discount_id=discount_id,
                            discount_name=discount_name,
                            user_id=user_id,
                            date=transaction_date,
                            detail=(
                                f"промокод {discount_name}: "
                                f"период {start_date.date()} — {end_date.date()}, "
                                f"транзакция {transaction_date.date()}"
                            ),
                        )
                    )

        subscriptions = paid_for.get("subscription") or []
        discounted_price = paid_for.get("discountedPrice")
        if subscriptions and discounted_price is not None:
            original_price = subscriptions[0].get("price")
            discount_type = discount.get("type", "")
            amount = discount.get("amount", 0)

            expected = None
            if original_price is not None:
                if discount_type in ("percentage", "%"):
                    expected = round(original_price * (1 - amount / 100))
                elif discount_type == "cash":
                    expected = original_price - amount

            if expected is not None and abs(discounted_price - expected) > PRICE_TOLERANCE:
                violations.append(
                    PromoCodeDiscountViolation(
                        kind="D",
                        label="Неверная сумма скидки",
                        tx_id=transaction_id,
                        discount_id=discount_id,
                        discount_name=discount_name,
                        user_id=user_id,
                        date=transaction_date,
                        detail=(
                            f"промокод {discount_name} ({discount_type} {amount}): "
                            f"ожидалось={expected} тг, факт discountedPrice={discounted_price} тг, "
                            f"catalog price={original_price} тг"
                        ),
                    )
                )

    return PromoCodeDiscountCheckResult(
        period_days=period_days,
        since=since,
        transactions_count=len(transactions),
        unique_discount_count=len(discounts_map),
        violations=violations,
    )


def run_internal_error_transactions_check(
    db,
    period_days: int,
    *,
    now: datetime | None = None,
) -> InternalErrorTransactionsCheckResult:
    """Проверяет отсутствие internalError транзакций за период."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    error_transactions = get_internal_error_transactions(db, since=since)

    club_ids = list({transaction["clubId"] for transaction in error_transactions if transaction.get("clubId")})
    club_id_to_name = get_club_names_map(db, club_ids=club_ids)

    transactions_by_club: dict[str, list[dict[str, Any]]] = defaultdict(list)
    product_type_counts: dict[str, int] = defaultdict(int)

    for transaction in error_transactions:
        club_id = transaction.get("clubId")
        club_name = club_id_to_name.get(club_id, f"Unknown ({club_id})") if club_id else "Без клуба"
        transactions_by_club[club_name].append(transaction)
        product_type_counts[transaction.get("productType") or "—"] += 1

    club_groups = [
        InternalErrorClubGroup(club_name=club_name, transactions=club_transactions)
        for club_name, club_transactions in transactions_by_club.items()
    ]
    club_groups.sort(key=lambda item: len(item.transactions), reverse=True)

    return InternalErrorTransactionsCheckResult(
        period_days=period_days,
        since=since,
        error_transactions_count=len(error_transactions),
        affected_clubs_count=len(transactions_by_club),
        club_groups=club_groups,
        product_type_counts=dict(
            sorted(product_type_counts.items(), key=lambda item: item[1], reverse=True)
        ),
    )


def run_visit_price_check(
    db,
    period_days: int,
    *,
    expected_unit_price_by_club_name_fragment: dict[str, int | float] | None = None,
    expected_total_price_by_club_type: dict[str, int | float] | None = None,
    now: datetime | None = None,
) -> VisitPriceCheckResult:
    """Checks that visits transactions have the expected total price for specific club types."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)
    expected_prices_by_name = (
        expected_unit_price_by_club_name_fragment or EXPECTED_VISIT_UNIT_PRICE_BY_CLUB_NAME_FRAGMENT
    )
    expected_prices = expected_total_price_by_club_type or EXPECTED_VISIT_TOTAL_PRICE_BY_CLUB_TYPE

    transactions = get_visit_transactions_with_club_type(db, since=since)
    violations: list[VisitPriceViolation] = []
    checked_transactions_count = 0

    for transaction in transactions:
        club = transaction.get("club") or {}
        club_name = club.get("name")
        club_type = club.get("type")
        expected_unit_price = _resolve_expected_visit_unit_price(
            club_name=club_name,
            club_type=club_type,
            expected_price_by_club_name_fragment=expected_prices_by_name,
            expected_price_by_club_type=expected_prices,
        )
        if expected_unit_price is None:
            continue

        checked_transactions_count += 1
        paid_for = transaction.get("paidFor") or {}
        visit_item = (paid_for.get("visits") or {})
        actual_total_price = paid_for.get("totalPrice")
        visits_count = visit_item.get("visitsCount")
        expected_total_price = (
            expected_unit_price * visits_count
            if isinstance(visits_count, (int, float))
            else expected_unit_price
        )

        if actual_total_price != expected_total_price:
            violations.append(
                VisitPriceViolation(
                    tx_id=str(transaction["_id"]),
                    user_id=str(transaction.get("userId")) if transaction.get("userId") is not None else None,
                    created_at=transaction.get("created_at"),
                    club_name=club_name or "Unknown club",
                    club_type=club_type,
                    club_id=club.get("_id"),
                    club_service_id=visit_item.get("clubServiceId"),
                    visits_count=visits_count,
                    expected_unit_price=expected_unit_price,
                    expected_total_price=expected_total_price,
                    actual_total_price=actual_total_price,
                    clubservice_price=(transaction.get("clubservice") or {}).get("price"),
                )
            )

    return VisitPriceCheckResult(
        period_days=period_days,
        since=since,
        transactions_count=len(transactions),
        checked_transactions_count=checked_transactions_count,
        violations=violations,
    )


def run_subscription_access_type_check(
    db,
    period_days: int,
    *,
    sample_size: int = 300,
    now: datetime | None = None,
) -> SubscriptionAccessTypeCheckResult:
    """Проверяет, что вход по абонементу фиксируется с accessType=subscription."""
    current_time = now or datetime.now()
    since = current_time - timedelta(days=period_days)

    plans = get_non_recurrent_subscription_plans(db)
    plan_map = {plan["_id"]: plan for plan in plans}

    user_subscriptions = get_active_user_subscriptions(
        db,
        subscription_ids=list(plan_map.keys()),
        now=current_time,
        since=since,
        limit=sample_size,
    )

    user_windows: dict[Any, list[tuple[datetime, datetime | None, Any]]] = defaultdict(list)
    for user_subscription in user_subscriptions:
        user_windows[user_subscription["user"]].append(
            (
                user_subscription["startDate"],
                user_subscription.get("endDate"),
                user_subscription.get("subscriptionId"),
            )
        )

    user_ids = list(user_windows.keys())
    entries = get_access_entries_for_users(
        db,
        user_ids=user_ids,
        since=since,
        now=current_time,
    )

    def find_window(user_id, entry_time, entry_club):
        """Ищет подходящее окно абонемента по пользователю, времени и клубу."""
        no_clubid_match = None
        for start, end, subscription_id in user_windows.get(user_id, []):
            if entry_time >= start and (end is None or entry_time <= end):
                plan_club = plan_map.get(subscription_id, {}).get("clubId")
                if plan_club == entry_club:
                    return subscription_id, True
                if plan_club is None and no_clubid_match is None:
                    no_clubid_match = subscription_id
        if no_clubid_match is not None:
            return no_clubid_match, False
        return None

    violations: list[SubscriptionAccessViolation] = []
    no_clubid_entries: list[SubscriptionPlanWithoutClubEntry] = []
    outside_window_count = 0
    by_club: dict[Any, dict[str, int]] = defaultdict(lambda: {"total": 0, "violations": 0})
    by_plan: dict[Any, dict[str, int]] = defaultdict(lambda: {"total": 0, "violations": 0})

    for entry in entries:
        result = find_window(entry["user"], entry["time"], entry.get("club"))
        if result is None:
            outside_window_count += 1
            continue

        matched_plan_id, club_matched = result
        if not club_matched:
            no_clubid_entries.append(
                SubscriptionPlanWithoutClubEntry(
                    entry_id=str(entry["_id"]),
                    user_id=str(entry["user"]),
                    time=entry["time"],
                    club_id=entry.get("club"),
                    plan_id=matched_plan_id,
                )
            )
            continue

        club_id = entry.get("club")
        by_club[club_id]["total"] += 1
        by_plan[matched_plan_id]["total"] += 1

        if entry.get("accessType") != "subscription":
            violations.append(
                SubscriptionAccessViolation(
                    entry_id=str(entry["_id"]),
                    user_id=str(entry["user"]),
                    time=entry["time"],
                    access_type=entry.get("accessType"),
                    club_id=club_id,
                    plan_id=matched_plan_id,
                )
            )
            by_club[club_id]["violations"] += 1
            by_plan[matched_plan_id]["violations"] += 1

    club_ids_used = list(
        {
            club_id
            for club_id in list(by_club.keys()) + [entry.club_id for entry in no_clubid_entries]
            if club_id is not None
        }
    )
    club_name_map = get_club_names_map(db, club_ids=club_ids_used)

    return SubscriptionAccessTypeCheckResult(
        period_days=period_days,
        since=since,
        sample_size=sample_size,
        plans_count=len(plans),
        sampled_subscriptions_count=len(user_subscriptions),
        sampled_users_count=len(user_ids),
        entries_count=len(entries),
        entries_in_window_count=len(entries) - outside_window_count,
        outside_window_count=outside_window_count,
        violations=violations,
        no_clubid_entries=no_clubid_entries,
        by_club=dict(by_club),
        by_plan=dict(by_plan),
        plan_map=plan_map,
        club_name_map=club_name_map,
    )
