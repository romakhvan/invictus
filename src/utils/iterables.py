from collections.abc import Iterable
from typing import Any, List


def ensure_iterable(value: Any) -> List[Any]:
    """
    Приводит входное значение к списку.
    None -> []
    Строки/байтовые строки считаются единичными значениями.
    """
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value]
    if isinstance(value, Iterable):
        return list(value)
    return [value]

