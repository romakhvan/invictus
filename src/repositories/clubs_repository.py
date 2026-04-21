from __future__ import annotations

from typing import Any

from src.utils.club_card_data import ClubCardData, normalize_club_text
from src.utils.repository_helpers import get_collection


_CLUBS_PROJECTION = {
    "_id": 1,
    "name": 1,
    "city": 1,
    "cityName": 1,
    "address": 1,
    "fullAddress": 1,
    "shortAddress": 1,
    "location": 1,
    "isDeleted": 1,
    "showInMobile": 1,
    "visibleInMobile": 1,
    "isVisibleInMobile": 1,
    "showInApp": 1,
    "visible": 1,
}


def get_mobile_clubs_by_city(db, city_name: str | None = None) -> list[ClubCardData]:
    clubs_col = get_collection(db, "clubs")
    docs = list(
        clubs_col.find(
            {
                "isDeleted": {"$ne": True},
                "name": {"$exists": True, "$ne": None},
            },
            _CLUBS_PROJECTION,
        )
    )

    normalized_city = normalize_club_text(city_name).casefold() if city_name else None
    result: dict[tuple[str, str, str], ClubCardData] = {}

    for doc in docs:
        if not _is_mobile_visible(doc):
            continue

        card = ClubCardData(
            name=doc.get("name", ""),
            city=_extract_city(doc),
            address=_extract_address(doc),
        )

        if not card.name.startswith("Invictus"):
            continue
        if not card.city or not card.address:
            continue
        if normalized_city and card.city.casefold() != normalized_city:
            continue

        result[card.key] = card

    return sorted(result.values(), key=lambda item: item.key)


def _is_mobile_visible(doc: dict[str, Any]) -> bool:
    for field in ("showInMobile", "visibleInMobile", "isVisibleInMobile", "showInApp"):
        if field in doc and doc.get(field) is False:
            return False
    return True


def _extract_city(doc: dict[str, Any]) -> str:
    city = doc.get("city")
    if isinstance(city, dict):
        for key in ("name", "title", "label"):
            if city.get(key):
                return normalize_club_text(city[key])
    if city:
        return normalize_club_text(city)

    location = doc.get("location")
    if isinstance(location, dict):
        for key in ("city", "cityName"):
            if location.get(key):
                return normalize_club_text(location[key])

    return normalize_club_text(doc.get("cityName"))


def _extract_address(doc: dict[str, Any]) -> str:
    address = doc.get("address")
    if isinstance(address, dict):
        for key in ("full", "fullAddress", "address", "street", "title"):
            if address.get(key):
                return normalize_club_text(address[key])
    if address:
        return normalize_club_text(address)

    for field in ("fullAddress", "shortAddress"):
        if doc.get(field):
            return normalize_club_text(doc[field])

    location = doc.get("location")
    if isinstance(location, dict):
        for key in ("address", "fullAddress", "shortAddress"):
            if location.get(key):
                return normalize_club_text(location[key])

    return ""
