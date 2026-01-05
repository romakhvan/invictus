from typing import Any, Optional

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import build_projection, get_collection, normalize_ids

DEFAULT_COACH_PROJECTION = {
    "_id": 1,
    "user": 1,
    "isDeleted": 1,
    "skills": 1,
    "galleryPhotos": 1,
    "specialists": 1,
    "awards": 1,
    "instances": 1,
    "created_at": 1,
    "updated_at": 1,
    "__v": 1,
    "bio": 1,
    "links": 1,
    "profilePhoto": 1,
    "isInBlackList": 1,
}


@log_function_call
def get_coach_by_user_id(
    db,
    user_id: Any,
    *,
    include_deleted: bool = False,
    projection: Optional[dict] = None,
) -> Optional[dict]:
    """
    Возвращает запись coaches по полю user.
    """
    normalized_ids = normalize_ids([user_id])
    if not normalized_ids:
        print("⚠️ get_coach_by_user_id: неверный идентификатор пользователя.")
        return None

    query = {"user": normalized_ids[0]}
    if not include_deleted:
        query["isDeleted"] = False

    effective_projection = projection or DEFAULT_COACH_PROJECTION

    doc = get_collection(db, "coaches").find_one(
        query,
        build_projection(effective_projection),
    )
    if doc:
        print(f"\n✅ Найдена запись coaches пользователя {_id_to_str(doc.get('user'))}")
    else:
        print("\n❌ Запись coaches не найдена.")
    return doc


def _id_to_str(value: Any) -> str:
    return str(value) if value is not None else "<unknown>"

def find_coaches_coaches_isdeleted_false(db):
    """
    🎂 Возвращает coaches, у которых isDeleted = false.
    """
    users_col = db["coaches"]

    coaches_isdeleted_false = {
        "isDeleted": False
    }

    projection = {"_id": 1, "user": 1, "fullName": 1}

    coaches_isdeleted_false_list= list(users_col.find(coaches_isdeleted_false, projection))
    print(f"🎂 Найдено coaches isDeleted false: {len(coaches_isdeleted_false_list)}")

    return coaches_isdeleted_false_list

find_coaches_coaches_isdeleted_false()