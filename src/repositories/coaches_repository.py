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


@log_function_call
def get_coach_collaboration_type(
    db,
    coach_id: Any,
    club_id: Any
) -> Optional[str]:
    """
    Определяет тип сотрудничества (collaborationType) тренера с клубом.
    
    Args:
        db: Database connection
        coach_id: _id записи тренера из коллекции coaches
        club_id: ID клуба
    
    Returns:
        str: "buhta", "staff" или None если не найдено
    """
    from src.utils.id_utils import normalize_object_ids
    
    normalized_coach_ids = normalize_object_ids([coach_id])
    normalized_club_ids = normalize_object_ids([club_id])
    
    if not normalized_coach_ids or not normalized_club_ids:
        return None
    
    coach_id_obj = normalized_coach_ids[0]
    club_id_obj = normalized_club_ids[0]
    
    # Получаем тренера с полем instances по _id (не по user!)
    coach = get_collection(db, "coaches").find_one(
        {"_id": coach_id_obj},
        {"instances": 1, "_id": 1}
    )
    
    if not coach:
        return None
    
    instances = coach.get("instances", [])
    if not instances:
        return None
    
    # Ищем instance с нужным клубом
    for instance in instances:
        instance_club_id = instance.get("club")
        if instance_club_id == club_id_obj:
            return instance.get("collaborationType")
    
    return None


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