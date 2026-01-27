from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from pprint import pprint
from collections import defaultdict

from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import get_collection
from src.repositories.coaches_repository import get_coach_collaboration_type
from src.repositories.coachwallethistories_repository import check_wallet_history_by_transaction


@log_function_call
def get_transactions_with_coach(
    db,
    source: Optional[str] = None,
    limit: Optional[int] = None,
    days: int = 7,
    projection: Optional[Dict[str, int]] = None,
    coach_id: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Получает транзакции, в которых есть coachId в paidFor.serviceProducts.
    
    Args:
        db: Database connection
        source: Фильтр по источнику транзакции ('mobile', 'website' и т.д.)
        limit: Ограничение количества записей
        days: Количество дней для выборки (по умолчанию 7)
        projection: Проекция полей MongoDB (какие поля включить/исключить)
                   Например: {"__v": 0, "metadata": 0} - исключить поля
                            {"_id": 1, "price": 1} - включить только эти поля
        coach_id: Фильтр по конкретному ID тренера (опционально)
    
    Returns:
        List[Dict]: Список найденных транзакций
    """
    from src.utils.id_utils import normalize_object_ids
    
    col = get_collection(db, "transactions")
    
    # Вычисляем дату N дней назад
    days_ago = datetime.now() - timedelta(days=days)
    
    query = {
        "paidFor.serviceProducts.coachId": {"$exists": True},
        "created_at": {"$gte": days_ago}
    }
    
    if source:
        query["source"] = source
    
    if coach_id:
        normalized_ids = normalize_object_ids([coach_id])
        if normalized_ids:
            query["paidFor.serviceProducts.coachId"] = normalized_ids[0]
    
    print(f"\n🔍 Запрос к коллекции transactions:")
    print(f"   Период: последние {days} дней (с {days_ago.strftime('%Y-%m-%d %H:%M:%S')})")
    if coach_id:
        print(f"   Фильтр по тренеру: {coach_id}")
    print(f"   Query: {query}")
    if projection:
        print(f"   Projection: {projection}")
    if limit:
        print(f"   Limit: {limit}")
    
    cursor = col.find(query, projection).sort("created_at", -1)
    
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
    days: int = 7,
    projection: Optional[Dict[str, int]] = None,
    coach_id: Optional[Any] = None
) -> None:
    """
    Выводит структуру транзакций с тренерами для анализа.
    
    Args:
        db: Database connection
        source: Фильтр по источнику транзакции
        limit: Ограничение количества записей для вывода
        days: Количество дней для выборки (по умолчанию 7)
        projection: Проекция полей MongoDB (какие поля включить/исключить)
        coach_id: Фильтр по конкретному ID тренера (опционально)
    """
    transactions = get_transactions_with_coach(
        db, source=source, limit=limit, days=days, projection=projection, coach_id=coach_id
    )
    
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
    days: int = 7,
    projection: Optional[Dict[str, int]] = None,
    coach_id: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Получает статистику по транзакциям с тренерами.
    
    Args:
        db: Database connection
        source: Фильтр по источнику транзакции
        days: Количество дней для выборки (по умолчанию 7)
        projection: Проекция полей MongoDB (какие поля включить/исключить)
        coach_id: Фильтр по конкретному ID тренера (опционально)
    
    Returns:
        Dict: Статистика по транзакциям
    """
    transactions = get_transactions_with_coach(
        db, source=source, days=days, projection=projection, coach_id=coach_id
    )
    
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
        "days": days,
        "coach_id_filter": coach_id
    }
    
    print("\n" + "=" * 80)
    print("📊 СТАТИСТИКА ТРАНЗАКЦИЙ С ТРЕНЕРАМИ")
    print("=" * 80)
    print(f"Период: последние {days} дней")
    if coach_id:
        print(f"Фильтр по тренеру: {coach_id}")
    print(f"Всего транзакций: {summary['total_transactions']}")
    print(f"Уникальных тренеров: {summary['unique_coaches']}")
    print(f"Фильтр по source: {summary['source_filter']}")
    print(f"\nРаспределение по типам:")
    for trans_type, count in sorted(transaction_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {trans_type}: {count}")
    print("=" * 80)
    
    return summary


@log_function_call
def analyze_transactions_collaboration_types(
    db,
    source: str = "mobile",
    days: int = 7,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """
    Анализирует транзакции и определяет типы сотрудничества (buhta/staff) для каждого тренера.
    
    Args:
        db: Database connection
        source: Фильтр по источнику транзакции
        days: Количество дней для выборки
        limit: Ограничение количества транзакций для анализа
    
    Returns:
        Dict: Статистика по типам сотрудничества
    """
    transactions = get_transactions_with_coach(db, source=source, days=days, limit=limit)
    
    print(f"\n{'=' * 100}")
    print(f"📊 АНАЛИЗ ТИПОВ СОТРУДНИЧЕСТВА В ТРАНЗАКЦИЯХ")
    print(f"{'=' * 100}")
    
    collaboration_stats = {
        "buhta": 0,
        "buhta_with_wallet": 0,
        "buhta_without_wallet": 0,
        "staff": 0,
        "not_found": 0,
        "no_club": 0
    }
    
    details = []
    
    for idx, trans in enumerate(transactions, 1):
        trans_id = trans.get("_id")
        club_id = trans.get("clubId")
        created_at = trans.get("created_at")
        
        if not club_id:
            collaboration_stats["no_club"] += 1
            continue
        
        paid_for = trans.get("paidFor", {})
        service_products = paid_for.get("serviceProducts", [])
        
        for sp in service_products:
            coach_id = sp.get("coachId")
            if not coach_id:
                continue
            
            # Определяем тип сотрудничества
            collab_type = get_coach_collaboration_type(db, coach_id, club_id)
            
            # Для типа "buhta" проверяем наличие записи в coachwallethistories
            wallet_record = None
            has_wallet_entry = False
            
            if collab_type == "buhta":
                wallet_record = check_wallet_history_by_transaction(db, trans_id)
                has_wallet_entry = wallet_record is not None
            
            detail = {
                "transaction_id": str(trans_id),
                "coach_id": str(coach_id),
                "club_id": str(club_id),
                "collaboration_type": collab_type,
                "has_wallet_entry": has_wallet_entry if collab_type == "buhta" else None,
                "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else None
            }
            
            details.append(detail)
            
            if collab_type == "buhta":
                collaboration_stats["buhta"] += 1
                if has_wallet_entry:
                    collaboration_stats["buhta_with_wallet"] += 1
                else:
                    collaboration_stats["buhta_without_wallet"] += 1
            elif collab_type == "staff":
                collaboration_stats["staff"] += 1
            else:
                collaboration_stats["not_found"] += 1
    
    # Вывод статистики
    print(f"\nПроанализировано транзакций: {len(transactions)}")
    print(f"\n{'─' * 60}")
    print(f"Статистика по типам сотрудничества:")
    print(f"{'─' * 60}")
    print(f"  📗 BUHTA (бухта): {collaboration_stats['buhta']}")
    print(f"     ✅ С записью в кошельке:  {collaboration_stats['buhta_with_wallet']}")
    print(f"     ❌ Без записи в кошельке: {collaboration_stats['buhta_without_wallet']}")
    print(f"  👔 STAFF (штат):  {collaboration_stats['staff']}")
    print(f"  ❓ Не найдено:     {collaboration_stats['not_found']}")
    print(f"  ⚠️  Без клуба:      {collaboration_stats['no_club']}")
    print(f"{'─' * 60}")
    
    # Показываем примеры каждого типа
    print(f"\n{'─' * 100}")
    print(f"ПРИМЕРЫ ТРАНЗАКЦИЙ (первые 10)")
    print(f"{'─' * 100}")
    
    for idx, detail in enumerate(details[:10], 1):
        print(f"\n#{idx}")
        print(f"  Transaction ID: {detail['transaction_id']}")
        print(f"  Coach ID:       {detail['coach_id']}")
        print(f"  Club ID:        {detail['club_id']}")
        print(f"  Collaboration:  {detail['collaboration_type'] or 'НЕ НАЙДЕНО'}")
        
        if detail['collaboration_type'] == 'buhta':
            wallet_status = "✅ ЕСТЬ" if detail['has_wallet_entry'] else "❌ НЕТ"
            print(f"  Запись в кошельке: {wallet_status}")
        
        print(f"  Дата:           {detail['created_at']}")
    
    print(f"\n{'=' * 100}")
    
    return {
        "stats": collaboration_stats,
        "details": details,
        "total_analyzed": len(transactions)
    }

