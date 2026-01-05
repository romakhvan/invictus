from typing import Any, Optional, Dict, List
from datetime import datetime
from pprint import pprint

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import get_collection


@log_function_call
def get_coach_wallet(db, coach_user_id: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """
    Получает запись из коллекции coachwallets.
    Если передан coach_user_id, возвращает запись для конкретного тренера.
    Иначе возвращает первую найденную запись.
    """
    from src.utils.id_utils import normalize_object_ids
    
    col = get_collection(db, "coachwallets")
    
    query = {}
    if coach_user_id:
        normalized_ids = normalize_object_ids([coach_user_id])
        if normalized_ids:
            query["coach"] = normalized_ids[0]
    
    doc = col.find_one(query)
    
    if doc:
        print(f"\n✅ Найдена запись в coachwallets")
        if coach_user_id:
            print(f"👤 Для тренера: {coach_user_id}")
    else:
        print("\n❌ Запись в coachwallets не найдена.")
    
    return doc


@log_function_call
def get_latest_coach_wallet_history(db, coach_user_id: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """
    Получает последнюю запись из коллекции coachwallethistories.
    Если передан coach_user_id, возвращает последнюю запись для конкретного тренера.
    Сортирует по createdAt (или _id если createdAt отсутствует).
    """
    from src.utils.id_utils import normalize_object_ids
    
    col = get_collection(db, "coachwallethistories")
    
    query = {}
    if coach_user_id:
        normalized_ids = normalize_object_ids([coach_user_id])
        if normalized_ids:
            query["coach"] = normalized_ids[0]
    
    # Сортируем по createdAt (основное поле для даты создания)
    doc = col.find_one(query, sort=[("createdAt", -1)])
    
    # Если не нашли, пробуем по _id
    if not doc:
        doc = col.find_one(query, sort=[("_id", -1)])
    
    if doc:
        print(f"\n✅ Найдена последняя запись в coachwallethistories")
        if coach_user_id:
            print(f"👤 Для тренера: {coach_user_id}")
    else:
        print("\n❌ Записи в coachwallethistories не найдены.")
    
    return doc


@log_function_call
def check_coach_payment(db, coach_user_id: Optional[Any] = None, expected_amount: Optional[float] = None) -> Dict[str, Any]:
    """
    Проверяет начисление денег тренеру по последней записи в coachwallethistories.
    
    Args:
        db: База данных MongoDB
        coach_user_id: ID тренера (опционально, если None - проверяет последнюю запись для любого тренера)
        expected_amount: Ожидаемая сумма начисления (опционально, для валидации)
    
    Returns:
        Словарь с результатами проверки:
        {
            "found": bool,
            "coach": str,
            "amount": float,
            "created_at": datetime,
            "type": str,
            "is_valid": bool,
            "message": str
        }
    """
    result = {
        "found": False,
        "coach": None,
        "amount": None,
        "created_at": None,
        "type": None,
        "is_valid": False,
        "message": ""
    }
    
    doc = get_latest_coach_wallet_history(db, coach_user_id)
    
    if not doc:
        result["message"] = "Запись не найдена"
        return result
    
    result["found"] = True
    result["coach"] = str(doc.get("coach", ""))
    
    # amount может быть словарем с gross и net, или числом
    amount_data = doc.get("amount", {})
    if isinstance(amount_data, dict):
        result["amount"] = float(amount_data.get("net", 0))  # Используем net сумму
        result["amount_gross"] = float(amount_data.get("gross", 0))
    else:
        result["amount"] = float(amount_data) if amount_data else 0
        result["amount_gross"] = result["amount"]
    
    result["created_at"] = doc.get("createdAt") or doc.get("created_at")
    result["type"] = doc.get("operation", "")  # operation вместо type
    result["source_type"] = doc.get("sourceType", "")
    result["source"] = str(doc.get("source", ""))
    result["commission_breakdown"] = doc.get("commissionBreakdown", [])
    
    # Выводим информацию о записи
    print(f"\n📋 Информация о начислении:")
    print(f"   Тренер: {result['coach']}")
    print(f"   Сумма (net): {result['amount']}")
    if result.get("amount_gross"):
        print(f"   Сумма (gross): {result['amount_gross']}")
    print(f"   Операция: {result['type']}")
    print(f"   Источник: {result['source_type']} ({result['source']})")
    print(f"   Дата: {result['created_at']}")
    
    # Проверяем валидность
    is_valid = True
    validation_messages = []
    
    if result["amount"] is None or result["amount"] == 0:
        is_valid = False
        validation_messages.append("Сумма начисления отсутствует или равна нулю")
    
    if expected_amount is not None:
        if abs(result["amount"] - expected_amount) > 0.01:  # Учитываем возможные погрешности float
            is_valid = False
            validation_messages.append(
                f"Сумма не совпадает: ожидалось {expected_amount}, получено {result['amount']}"
            )
    
    if coach_user_id:
        from src.utils.id_utils import normalize_object_ids
        normalized_ids = normalize_object_ids([coach_user_id])
        expected_coach_id = str(normalized_ids[0]) if normalized_ids else str(coach_user_id)
        if result["coach"] != expected_coach_id:
            is_valid = False
            validation_messages.append(
                f"Запись относится к другому тренеру: ожидался {expected_coach_id}, получен {result['coach']}"
            )
    
    result["is_valid"] = is_valid
    result["message"] = "; ".join(validation_messages) if validation_messages else "Начисление корректно"
    
    if is_valid:
        print(f"✅ {result['message']}")
    else:
        print(f"❌ {result['message']}")
    
    # Выводим полную структуру записи для анализа
    print(f"\n📄 Полная структура записи:")
    pprint(doc, sort_dicts=False, width=120)
    
    return result


@log_function_call
def get_all_coach_wallet_transactions(
    db, 
    coach_user_id: Any, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Получает все транзакции тренера из coachwallethistories.
    
    Args:
        db: База данных MongoDB
        coach_user_id: ID тренера
        start_date: Начальная дата для фильтрации (опционально)
        end_date: Конечная дата для фильтрации (опционально)
    
    Returns:
        Список транзакций, отсортированных по дате создания
    """
    from src.utils.id_utils import normalize_object_ids
    
    col = get_collection(db, "coachwallethistories")
    
    normalized_ids = normalize_object_ids([coach_user_id])
    if not normalized_ids:
        return []
    
    query = {"coach": normalized_ids[0], "isDeleted": False}
    
    if start_date or end_date:
        query["createdAt"] = {}
        if start_date:
            query["createdAt"]["$gte"] = start_date
        if end_date:
            query["createdAt"]["$lte"] = end_date
    
    transactions = list(col.find(query).sort("createdAt", 1))
    return transactions


@log_function_call
def get_transaction_by_id(db, transaction_id: Any) -> Optional[Dict[str, Any]]:
    """
    Получает запись из коллекции transactions по ID.
    
    Args:
        db: База данных MongoDB
        transaction_id: ID транзакции
    
    Returns:
        Запись транзакции или None
    """
    from src.utils.id_utils import normalize_object_ids
    
    col = get_collection(db, "transactions")
    
    normalized_ids = normalize_object_ids([transaction_id])
    if not normalized_ids:
        return None
    
    doc = col.find_one({"_id": normalized_ids[0]})
    return doc

