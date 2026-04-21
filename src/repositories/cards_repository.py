"""Helpers for saved payment cards in MongoDB."""

from typing import Any

from src.utils.repository_helpers import get_collection, normalize_ids


DEFAULT_SAVED_CARD_HASH_PATTERN = "^404932.*6267$"


def attach_latest_saved_card_to_user(
    db,
    *,
    user_id: Any,
    card_hash_pattern: str = DEFAULT_SAVED_CARD_HASH_PATTERN,
) -> dict[str, Any]:
    """Attach the latest seeded saved card to the given user."""
    normalized_ids = normalize_ids([user_id])
    normalized_user_id = normalized_ids[0] if normalized_ids else user_id

    col = get_collection(db, "cards")
    query = {"hash": {"$regex": card_hash_pattern}}
    projection = {
        "_id": 1,
        "hash": 1,
        "user": 1,
        "created_at": 1,
        "createdAt": 1,
    }

    cards = list(
        col.find(query, projection)
        .sort([("created_at", -1), ("createdAt", -1), ("_id", -1)])
        .limit(1)
    )
    if not cards:
        raise ValueError(
            "Saved test card was not found in cards collection "
            f"by hash pattern {card_hash_pattern!r}."
        )

    card = cards[0]
    result = col.update_one(
        {"_id": card["_id"]},
        {"$set": {"user": normalized_user_id}},
    )
    if result.matched_count != 1:
        raise ValueError(f"Saved test card disappeared before update: {card['_id']}")

    print(
        "\nAttached saved payment card "
        f"{card['_id']} ({card.get('hash')}) to user={normalized_user_id}"
    )
    return card
