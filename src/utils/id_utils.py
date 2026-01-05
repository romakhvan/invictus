from typing import Iterable, List, Union, Any

from bson import ObjectId

from src.utils.iterables import ensure_iterable


def normalize_object_ids(values: Union[Any, Iterable[Any]]) -> List[Any]:
    """
    Преобразует все значения, похожие на ObjectId, в реальные ObjectId.
    Остальные значения возвращает без изменений.
    """
    normalized: List[Any] = []
    for raw_value in ensure_iterable(values):
        if isinstance(raw_value, ObjectId):
            normalized.append(raw_value)
        elif isinstance(raw_value, str) and ObjectId.is_valid(raw_value):
            normalized.append(ObjectId(raw_value))
        else:
            normalized.append(raw_value)
    return normalized

