"""Monitoring report for recent non-POS transactions grouped by instalmentType."""

from collections import defaultdict
from datetime import datetime, timedelta

from src.repositories.payments.checks_repository import (
    get_recent_recurrent_success_instalment_stats,
    get_recent_transaction_fail_examples,
    get_recent_transaction_instalment_stats,
)


FAIL_EXAMPLE_LIMIT = 200
FAIL_EXAMPLES_PER_TYPE = 5


def _instalment_label(value) -> str:
    return str(value) if value not in (None, "") else "Не указан"


def test_recent_transactions_grouped_by_instalment_type(db, period_days):
    """
    Reports recent non-POS transactions by instalmentType.

    The query intentionally aggregates counts in MongoDB and only fetches a
    bounded sample of failed documents, because the raw transaction set can be
    large enough for a full scan to be cancelled by MongoDB.
    """
    now = datetime.now()
    since = now - timedelta(days=period_days)

    instalment_stats = get_recent_transaction_instalment_stats(db, since=since)
    recurrent_stats = {
        _instalment_label(row.get("_id")): row.get("transactions_count", 0)
        for row in get_recent_recurrent_success_instalment_stats(db, since=since)
    }
    fail_examples = get_recent_transaction_fail_examples(
        db,
        since=since,
        limit=FAIL_EXAMPLE_LIMIT,
    )

    fail_examples_by_type = defaultdict(list)
    for transaction in fail_examples:
        fail_examples_by_type[_instalment_label(transaction.get("instalmentType"))].append(
            transaction
        )

    total_transactions = sum(row.get("transactions_count", 0) for row in instalment_stats)
    total_recurrent_success = sum(recurrent_stats.values())
    total_fail = sum(
        (row.get("status_counts") or {}).get("fail", 0)
        for row in instalment_stats
    )

    print(f"\n{'=' * 80}")
    print("RECENT NON-POS TRANSACTIONS BY instalmentType")
    print(f"{'=' * 80}")
    print(f"Period: last {period_days} days, since {since:%Y-%m-%d %H:%M:%S}")
    print(f"Total transactions: {total_transactions}")
    print(f"Successful recurrent transactions: {total_recurrent_success}")
    print(f"Failed transactions: {total_fail}")

    if not instalment_stats:
        print("\nNo transactions found for the selected period.")
        assert total_transactions >= 0
        return

    print(f"\n{'-' * 80}")
    print("GROUPED BY instalmentType")
    print(f"{'-' * 80}")

    for row in sorted(instalment_stats, key=lambda item: _instalment_label(item.get("_id"))):
        instalment_type = _instalment_label(row.get("_id"))
        status_counts = row.get("status_counts") or {}
        transactions_count = row.get("transactions_count", 0)
        total_amount = row.get("total_amount", 0)

        print(f"\n{instalment_type}: {transactions_count} transactions")
        print(f"  Total amount: {total_amount}")
        print(f"  Successful recurrent: {recurrent_stats.get(instalment_type, 0)}")
        print("  Statuses:")
        for status, count in sorted(status_counts.items()):
            print(f"    - {status}: {count}")

        examples = fail_examples_by_type.get(instalment_type, [])[:FAIL_EXAMPLES_PER_TYPE]
        if examples:
            print("  Latest failed examples:")
            for transaction in examples:
                created_at = transaction.get("created_at")
                created_at_text = (
                    created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if created_at
                    else "not set"
                )
                print(
                    "    - "
                    f"{created_at_text} | id={transaction.get('_id')} | "
                    f"price={transaction.get('price', 0)} | "
                    f"productType={transaction.get('productType', 'unknown')} | "
                    f"reason={transaction.get('reason', 'not set')}"
                )

    print(f"\n{'=' * 80}")
    assert total_transactions >= 0, "Transaction count cannot be negative"
