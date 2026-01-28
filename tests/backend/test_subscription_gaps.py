from src.repositories.subscriptions_repository import find_last_10_subscriptions_with_big_gap

def test_check_subscriptions_gap(db):
    result = find_last_10_subscriptions_with_big_gap(db, months=2)
    assert 1

