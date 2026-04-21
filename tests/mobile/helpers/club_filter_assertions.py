from __future__ import annotations

from src.utils.club_card_data import ClubCardData


def assert_club_cards_match_mongo(
    actual_cards: list[ClubCardData],
    expected_cards: list[ClubCardData],
) -> None:
    actual_by_name = {card.name: card for card in actual_cards}
    expected_by_name = {card.name: card for card in expected_cards}

    missing = sorted(name for name in expected_by_name if name not in actual_by_name)
    unexpected = sorted(name for name in actual_by_name if name not in expected_by_name)

    mismatched: list[str] = []
    for name in sorted(set(actual_by_name) & set(expected_by_name)):
        actual = actual_by_name[name]
        expected = expected_by_name[name]
        field_diffs: list[str] = []
        if actual.city != expected.city:
            field_diffs.append(f"city ui='{actual.city}' mongo='{expected.city}'")
        if actual.address != expected.address:
            field_diffs.append(f"address ui='{actual.address}' mongo='{expected.address}'")
        if field_diffs:
            mismatched.append(f"{name}: " + "; ".join(field_diffs))

    if missing or unexpected or mismatched:
        parts: list[str] = ["Сверка клубов UI vs Mongo завершилась с расхождениями."]
        if missing:
            parts.append("missing: " + ", ".join(missing))
        if unexpected:
            parts.append("unexpected: " + ", ".join(unexpected))
        if mismatched:
            parts.append("mismatched fields: " + " | ".join(mismatched))
        raise AssertionError("\n".join(parts))
