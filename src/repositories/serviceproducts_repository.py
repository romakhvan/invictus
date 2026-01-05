from typing import Any, Dict, Optional

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import build_projection, get_collection, normalize_ids


@log_function_call
def get_serviceproduct_by_id(
    db,
    serviceproduct_id: Any,
    *,
    include_deleted: bool = False,
    projection: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Возвращает один документ serviceproducts по _id и выводит все поля.
    """
    normalized_ids = normalize_ids([serviceproduct_id])
    if not normalized_ids:
        print("⚠️ get_serviceproduct_by_id: неверный идентификатор.")
        return None

    query: Dict[str, Any] = {"_id": normalized_ids[0]}
    if not include_deleted:
        query["isDeleted"] = False

    doc = get_collection(db, "serviceproducts").find_one(query, build_projection(projection))
    if doc:
        print(f"\n✅ Найдена запись serviceproducts {_id_to_str(doc.get('_id'))}")
    else:
        print("\n❌ Запись serviceproducts не найдена.")
    return doc


def _id_to_str(value: Any) -> str:
    """
    Безопасное представление идентификатора для вывода.
    """
    return str(value) if value is not None else "<unknown>"

