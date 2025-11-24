from src.config.db_config import get_db

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