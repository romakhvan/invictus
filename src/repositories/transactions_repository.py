from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from pprint import pprint

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import get_collection


@log_function_call
def get_transactions_with_coach(
    db,
    source: Optional[str] = None,
    limit: Optional[int] = None,
    days: int = 7
) -> List[Dict[str, Any]]:
    """
    Получает транзакции, в которых есть coachId в paidFor.serviceProducts.
    
    Args:
        db: Database connection
        source: Фильтр по источнику транзакции ('mobile', 'website' и т.д.)
        limit: Ограничение количества записей
        days: Количество дней для выборки (по умолчанию 7)
    
    Returns:
        List[Dict]: Список найденных транзакций
    """
    col = get_collection(db, "transactions")
    
    # Вычисляем дату N дней назад
    days_ago = datetime.now() - timedelta(days=days)
    
    query = {
        "paidFor.serviceProducts.coachId": {"$exists": True},
        "created_at": {"$gte": days_ago}
    }
    
    if source:
        query["source"] = source
    
    print(f"\n🔍 Запрос к коллекции transactions:")
    print(f"   Период: последние {days} дней (с {days_ago.strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"   Query: {query}")
    if limit:
        print(f"   Limit: {limit}")
    
    cursor = col.find(query).sort("created_at", -1)
    
    if limit:
        cursor = cursor.limit(limit)
    
    transactions = list(cursor)
    
    print(f"\n✅ Найдено транзакций: {len(transactions)}")
    
    if transactions:
        # Показываем диапазон дат
        first_date = transactions[0].get("created_at")
        last_date = transactions[-1].get("created_at")
        if first_date and last_date:
            print(f"   Диапазон дат: {last_date.strftime('%Y-%m-%d %H:%M:%S')} - {first_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return transactions


@log_function_call
def display_transactions_structure(
    db,
    source: str = "mobile",
    limit: int = 5,
    days: int = 7
) -> None:
    """
    Выводит структуру транзакций с тренерами для анализа.
    
    Args:
        db: Database connection
        source: Фильтр по источнику транзакции
        limit: Ограничение количества записей для вывода
        days: Количество дней для выборки (по умолчанию 7)
    """
    transactions = get_transactions_with_coach(db, source=source, limit=limit, days=days)
    
    if not transactions:
        print("\n❌ Транзакции не найдены")
        return
    
    print("\n" + "=" * 100)
    print(f"📋 СТРУКТУРА ТРАНЗАКЦИЙ (последние {limit} записей)")
    print("=" * 100)
    
    for idx, trans in enumerate(transactions, 1):
        print(f"\n{'─' * 100}")
        print(f"Транзакция #{idx}")
        created_at = trans.get("created_at")
        if created_at:
            print(f"Дата: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'─' * 100}")
        pprint(trans, sort_dicts=False, width=120)
    
    print("\n" + "=" * 100)
    print(f"Всего выведено: {len(transactions)} из найденных")
    print("=" * 100)


@log_function_call
def get_transactions_with_coach_summary(
    db,
    source: Optional[str] = None,
    days: int = 7
) -> Dict[str, Any]:
    """
    Получает статистику по транзакциям с тренерами.
    
    Args:
        db: Database connection
        source: Фильтр по источнику транзакции
        days: Количество дней для выборки (по умолчанию 7)
    
    Returns:
        Dict: Статистика по транзакциям
    """
    transactions = get_transactions_with_coach(db, source=source, days=days)
    
    coach_ids = set()
    transaction_types = {}
    
    for trans in transactions:
        paid_for = trans.get("paidFor", {})
        service_products = paid_for.get("serviceProducts", [])
        
        for sp in service_products:
            coach_id = sp.get("coachId")
            if coach_id:
                coach_ids.add(str(coach_id))
        
        trans_type = trans.get("type", "unknown")
        transaction_types[trans_type] = transaction_types.get(trans_type, 0) + 1
    
    summary = {
        "total_transactions": len(transactions),
        "unique_coaches": len(coach_ids),
        "transaction_types": transaction_types,
        "source_filter": source or "all",
        "days": days
    }
    
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА ТРАНЗАКЦИЙ С ТРЕНЕРАМИ")
    print("=" * 80)
    print(f"Период: последние {days} дней")
    print(f"Всего транзакций: {summary['total_transactions']}")
    print(f"Уникальных тренеров: {summary['unique_coaches']}")
    print(f"Фильтр по source: {summary['source_filter']}")
    print(f"\nРаспределение по типам:")
    for trans_type, count in sorted(transaction_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {trans_type}: {count}")
    print("=" * 80)
    
    return summary

