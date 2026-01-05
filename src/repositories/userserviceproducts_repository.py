from typing import Any, Dict, Iterable, List, Optional

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import (
    build_projection,
    get_collection,
    normalize_ids,
)

DEFAULT_USERSERVICEPRODUCT_PROJECTION = {
    "_id": 1,
    "isActive": 1,
    "isDeleted": 1,
    "serviceProduct": 1,
    "user": 1,
    "club": 1,
    "initialCount": 1,
    "count": 1,
    "startDate": 1,
    "endDate": 1,
    "price": 1,
    "coach": 1,
    "child": 1,
}


@log_function_call
def find_service_products_by_users(
    db,
    user_ids: Iterable[Any],
    *,
    include_deleted: bool = False,
    projection: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Возвращает все записи userserviceproducts для переданных пользователей.
    По умолчанию исключает помеченные как удалённые записи.
    """
    normalized_user_ids = normalize_ids(user_ids)
    if not normalized_user_ids:
        print("⚠️ find_service_products_by_users: пустой список user_ids.")
        return []

    query: Dict[str, Any] = {"user": {"$in": normalized_user_ids}}
    if not include_deleted:
        query["isDeleted"] = False

    effective_projection = projection or DEFAULT_USERSERVICEPRODUCT_PROJECTION

    docs = list(
        get_collection(db, "userserviceproducts").find(
            query, build_projection(effective_projection)
        )
    )
    print(f"📦 Найдено сервис-продуктов: {len(docs)}")
    return docs


@log_function_call
def get_userserviceproduct_details(
    db,
    userserviceproduct_ids: Iterable[Any],
    *,
    include_deleted: bool = False,
    projection: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Возвращает список документов по их _id.
    """
    normalized_ids = normalize_ids(userserviceproduct_ids)
    if not normalized_ids:
        print("⚠️ get_userserviceproduct_details: пустой список идентификаторов.")
        return []

    query: Dict[str, Any] = {"_id": {"$in": normalized_ids}}
    if not include_deleted:
        query["isDeleted"] = False

    effective_projection = projection or DEFAULT_USERSERVICEPRODUCT_PROJECTION

    docs = list(
        get_collection(db, "userserviceproducts").find(
            query, build_projection(effective_projection)
        )
    )
    print(f"🧾 Найдено документов userserviceproducts: {len(docs)}")
    return docs


@log_function_call
def get_userserviceproduct_by_id(
    db,
    userserviceproduct_id: Any,
    *,
    include_deleted: bool = False,
    projection: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Возвращает один документ userserviceproducts по _id.
    """
    normalized_ids = normalize_ids([userserviceproduct_id])
    if not normalized_ids:
        print("⚠️ get_userserviceproduct_by_id: неверный идентификатор.")
        return None

    query: Dict[str, Any] = {"_id": normalized_ids[0]}
    if not include_deleted:
        query["isDeleted"] = False

    effective_projection = projection or DEFAULT_USERSERVICEPRODUCT_PROJECTION

    doc = get_collection(db, "userserviceproducts").find_one(
        query, build_projection(effective_projection)
    )
    if doc:
        print(f"\n✅ Найдена запись userserviceproducts {_id_to_str(doc.get('_id'))}")
    else:
        print("\n❌ Запись userserviceproducts не найдена.")
    return doc


def _id_to_str(value: Any) -> str:
    """
    Безопасное представление идентификатора для вывода.
    """
    return str(value) if value is not None else "<unknown>"

