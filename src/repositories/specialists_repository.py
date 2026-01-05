from typing import Any, Optional

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import build_projection, get_collection, normalize_ids

DEFAULT_SPECIALIST_PROJECTION = {
    "_id": 1,
    "isDeleted": 1,
    "title": 1,
    "level": 1,
    "masterSpecialist": 1,
}


@log_function_call
def get_specialist_by_id(
    db,
    specialist_id: Any,
    *,
    include_deleted: bool = False,
    projection: Optional[dict] = None,
) -> Optional[dict]:
    """
    Возвращает один документ specialists по _id.
    """
    normalized_ids = normalize_ids([specialist_id])
    if not normalized_ids:
        print("⚠️ get_specialist_by_id: неверный идентификатор.")
        return None

    query = {"_id": normalized_ids[0]}
    if not include_deleted:
        query["isDeleted"] = False

    effective_projection = projection or DEFAULT_SPECIALIST_PROJECTION

    doc = get_collection(db, "specialists").find_one(
        query,
        build_projection(effective_projection),
    )
    if doc:
        print(f"\n✅ Найдена запись specialists {_id_to_str(doc.get('_id'))}")
    else:
        print("❌ Запись specialists не найдена.")
    return doc


def _id_to_str(value: Any) -> str:
    return str(value) if value is not None else "<unknown>"

