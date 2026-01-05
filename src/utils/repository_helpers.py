from typing import Any, Dict, Iterable, List, Optional

from pymongo.collection import Collection

from src.utils.id_utils import normalize_object_ids


def get_collection(db, collection_name: str) -> Collection:
    """
    Единая точка получения коллекции MongoDB.
    Оборачиваем доступ, чтобы упростить подмену/моки в тестах.
    """
    return db[collection_name]


def build_projection(projection: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    MongoDB ожидает None либо действительный словарь.
    """
    return projection or None


def normalize_ids(raw_ids: Iterable[Any]) -> List[Any]:
    """
    Унифицированный хелпер вокруг normalize_object_ids.
    """
    return normalize_object_ids(raw_ids)

