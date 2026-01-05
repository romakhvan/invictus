from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta

from src.repositories.coachwallethistories_repository import (
    get_coach_wallet, 
    get_latest_coach_wallet_history,
    get_all_coach_wallet_transactions,
    get_transaction_by_id
)
from src.utils.debug_utils import log_function_call
from src.utils.repository_helpers import get_collection
from src.utils.id_utils import normalize_object_ids




@log_function_call
def calculate_wallet_balance_from_history(
    db, 
    coach_user_id: Any,
    start_date: Optional[datetime] = None
) -> Dict[str, float]:
    """
    Рассчитывает баланс кошелька на основе всех транзакций в истории.
    Возвращает: {"total_income": float, "total_expense": float, "calculated_balance": float}
    """
    transactions = get_all_coach_wallet_transactions(db, coach_user_id, start_date=start_date)
    
    total_income = 0.0
    total_expense = 0.0
    
    for trans in transactions:
        amount_data = trans.get("amount", {})
        operation = trans.get("operation", "")
        
        if isinstance(amount_data, dict):
            net_amount = float(amount_data.get("net", 0))
        else:
            net_amount = float(amount_data) if amount_data else 0
        
        if operation == "income":
            total_income += net_amount
        elif operation == "expense" or operation == "withdrawal":
            total_expense += net_amount
    
    calculated_balance = total_income - total_expense
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "calculated_balance": calculated_balance
    }


@log_function_call
def check_wallet_balance_consistency(db, coach_user_id: Any) -> bool:
    """
    ✅ Проверка 1: Согласованность баланса
    Проверяет, что totalAmount в coachwallets соответствует сумме всех транзакций.
    """
    print("\n=== CHECK 1: Wallet Balance Consistency ===")
    
    wallet = get_coach_wallet(db, coach_user_id)
    if not wallet:
        print(f"❌ Кошелёк для тренера {coach_user_id} не найден")
        return False
    
    wallet_balance = float(wallet.get("totalAmount", 0))
    calculated = calculate_wallet_balance_from_history(db, coach_user_id)
    
    print(f"💰 Баланс в coachwallets: {wallet_balance}")
    print(f"📊 Рассчитанный баланс из истории: {calculated['calculated_balance']}")
    print(f"   Доходы: {calculated['total_income']}")
    print(f"   Расходы: {calculated['total_expense']}")
    
    difference = abs(wallet_balance - calculated['calculated_balance'])
    tolerance = 0.01  # Допустимая погрешность
    
    if difference > tolerance:
        print(f"❌ Расхождение баланса: {difference}")
        return False
    
    print("✅ Баланс согласован")
    return True


@log_function_call
def check_commission_calculations(db, coach_user_id: Optional[Any] = None) -> bool:
    """
    ✅ Проверка 2: Корректность расчёта комиссий
    Проверяет, что gross - комиссии = net для каждой транзакции.
    """
    print("\n=== CHECK 2: Commission Calculations ===")
    
    if coach_user_id:
        transactions = get_all_coach_wallet_transactions(db, coach_user_id)
    else:
        # Проверяем последнюю транзакцию
        latest = get_latest_coach_wallet_history(db)
        transactions = [latest] if latest else []
    
    if not transactions:
        print("⚠️ Транзакции не найдены")
        return False
    
    all_valid = True
    
    for trans in transactions:
        amount_data = trans.get("amount", {})
        if not isinstance(amount_data, dict):
            continue
        
        gross = float(amount_data.get("gross", 0))
        net = float(amount_data.get("net", 0))
        commission_breakdown = trans.get("commissionBreakdown", [])
        
        # Рассчитываем сумму комиссий
        total_commission = sum(float(comm.get("amount", 0)) for comm in commission_breakdown)
        
        # Проверяем: gross - комиссии = net
        expected_net = gross - total_commission
        difference = abs(net - expected_net)
        
        if difference > 0.01:
            print(f"❌ Ошибка в транзакции {trans.get('_id')}:")
            print(f"   gross: {gross}, net: {net}, комиссии: {total_commission}")
            print(f"   Ожидаемый net: {expected_net}, фактический: {net}")
            all_valid = False
        else:
            print(f"✅ Транзакция {trans.get('_id')}: комиссии рассчитаны корректно")
    
    return all_valid


@log_function_call
def check_duplicate_transactions(db, coach_user_id: Optional[Any] = None, days: int = 7) -> bool:
    """
    ✅ Проверка 3: Дубликаты транзакций
    Проверяет наличие дублирующихся транзакций (одинаковый source, transaction, сумма).
    """
    print("\n=== CHECK 3: Duplicate Transactions ===")
    
    if coach_user_id:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        transactions = get_all_coach_wallet_transactions(db, coach_user_id, start_date, end_date)
    else:
        # Проверяем последние N транзакций
        col = get_collection(db, "coachwallethistories")
        transactions = list(col.find({"isDeleted": False}).sort("createdAt", -1).limit(100))
    
    if not transactions:
        print("⚠️ Транзакции не найдены")
        return True
    
    # Группируем по ключевым полям
    seen = {}
    duplicates = []
    
    for trans in transactions:
        key = (
            str(trans.get("coach", "")),
            str(trans.get("source", "")),
            str(trans.get("transaction", "")),
            str(trans.get("amount", {})),
            trans.get("operation", "")
        )
        
        if key in seen:
            duplicates.append((seen[key], trans))
        else:
            seen[key] = trans
    
    if duplicates:
        print(f"❌ Найдено {len(duplicates)} дублирующихся транзакций:")
        for dup1, dup2 in duplicates[:5]:  # Показываем первые 5
            print(f"   Транзакция 1: {dup1.get('_id')} от {dup1.get('createdAt')}")
            print(f"   Транзакция 2: {dup2.get('_id')} от {dup2.get('createdAt')}")
        return False
    
    print("✅ Дубликаты не найдены")
    return True


@log_function_call
def check_transaction_sequence(db, coach_user_id: Any) -> bool:
    """
    ✅ Проверка 4: Последовательность транзакций
    Проверяет, что транзакции идут в хронологическом порядке и нет пропусков.
    """
    print("\n=== CHECK 4: Transaction Sequence ===")
    
    transactions = get_all_coach_wallet_transactions(db, coach_user_id)
    
    if len(transactions) < 2:
        print("⚠️ Недостаточно транзакций для проверки последовательности")
        return True
    
    issues = []
    
    for i in range(1, len(transactions)):
        prev = transactions[i - 1]
        curr = transactions[i]
        
        prev_date = prev.get("createdAt")
        curr_date = curr.get("createdAt")
        
        if prev_date and curr_date and curr_date < prev_date:
            issues.append({
                "issue": "Нарушена хронология",
                "prev": {"id": prev.get("_id"), "date": prev_date},
                "curr": {"id": curr.get("_id"), "date": curr_date}
            })
    
    if issues:
        print(f"❌ Найдено {len(issues)} нарушений последовательности:")
        for issue in issues[:5]:
            print(f"   {issue}")
        return False
    
    print("✅ Последовательность транзакций корректна")
    return True


@log_function_call
def check_negative_balance(db, coach_user_id: Optional[Any] = None) -> bool:
    """
    ✅ Проверка 5: Отрицательный баланс
    Проверяет, что баланс кошелька не становится отрицательным (если это недопустимо).
    """
    print("\n=== CHECK 5: Negative Balance Check ===")
    
    if coach_user_id:
        wallet = get_coach_wallet(db, coach_user_id)
        if not wallet:
            print(f"⚠️ Кошелёк для тренера {coach_user_id} не найден")
            return True
        
        balance = float(wallet.get("totalAmount", 0))
        if balance < 0:
            print(f"❌ Отрицательный баланс: {balance}")
            return False
        
        print(f"✅ Баланс положительный: {balance}")
        return True
    else:
        # Проверяем все кошельки
        col = get_collection(db, "coachwallets")
        wallets = list(col.find({"isDeleted": False}))
        
        negative_wallets = [w for w in wallets if float(w.get("totalAmount", 0)) < 0]
        
        if negative_wallets:
            print(f"❌ Найдено {len(negative_wallets)} кошельков с отрицательным балансом:")
            for w in negative_wallets[:5]:
                print(f"   Тренер: {w.get('coach')}, баланс: {w.get('totalAmount')}")
            return False
        
        print(f"✅ Все кошельки имеют неотрицательный баланс ({len(wallets)} проверено)")
        return True


@log_function_call
def check_data_integrity(db, coach_user_id: Any) -> bool:
    """
    ✅ Проверка 6: Целостность данных
    Проверяет связность данных: coach существует, source существует, transaction существует.
    """
    print("\n=== CHECK 6: Data Integrity ===")
    
    transactions = get_all_coach_wallet_transactions(db, coach_user_id)
    
    if not transactions:
        print("⚠️ Транзакции не найдены")
        return True
    
    issues = []
    
    # Проверяем существование coach
    coaches_col = get_collection(db, "coaches")
    coach = coaches_col.find_one({"_id": transactions[0].get("coach")})
    if not coach:
        issues.append("Тренер не найден в коллекции coaches")
    
    # Проверяем source для UserServiceProducts
    for trans in transactions[:10]:  # Проверяем первые 10
        source_type = trans.get("sourceType")
        source_id = trans.get("source")
        
        if source_type == "UserServiceProducts" and source_id:
            usp_col = get_collection(db, "userserviceproducts")
            usp = usp_col.find_one({"_id": source_id})
            if not usp:
                issues.append(f"Source UserServiceProduct {source_id} не найден")
    
    if issues:
        print(f"❌ Найдено {len(issues)} проблем целостности:")
        for issue in issues[:5]:
            print(f"   {issue}")
        return False
    
    print("✅ Целостность данных в порядке")
    return True


@log_function_call
def check_transactions_data(db, coach_user_id: Optional[Any] = None) -> bool:
    """
    ✅ Проверка 7: Данные в transactions
    Проверяет корректность данных в коллекции transactions, связанных с coachwallethistories.
    """
    print("\n=== CHECK 7: Transactions Data Validation ===")
    
    if coach_user_id:
        wallet_history = get_all_coach_wallet_transactions(db, coach_user_id)
    else:
        # Проверяем последние транзакции
        col = get_collection(db, "coachwallethistories")
        wallet_history = list(col.find({"isDeleted": False}).sort("createdAt", -1).limit(50))
    
    if not wallet_history:
        print("⚠️ Записи в coachwallethistories не найдены")
        return True
    
    issues = []
    checked_count = 0
    
    for wh_record in wallet_history:
        transaction_id = wh_record.get("transaction")
        if not transaction_id:
            continue
        
        transaction = get_transaction_by_id(db, transaction_id)
        if not transaction:
            issues.append(f"Транзакция {transaction_id} не найдена в коллекции transactions")
            continue
        
        checked_count += 1
        
        # 1. Проверка суммы: transactions.price должен совпадать с coachwallethistories.amount.gross
        wh_amount = wh_record.get("amount", {})
        if isinstance(wh_amount, dict):
            wh_gross = float(wh_amount.get("gross", 0))
        else:
            wh_gross = float(wh_amount) if wh_amount else 0
        
        trans_price = float(transaction.get("price", 0))
        
        if abs(wh_gross - trans_price) > 0.01:
            issues.append(
                f"Несоответствие суммы: coachwallethistories.gross={wh_gross}, "
                f"transactions.price={trans_price} (transaction_id={transaction_id})"
            )
        
        # 2. Проверка статуса транзакции
        trans_status = transaction.get("status", "")
        if trans_status != "success":
            issues.append(
                f"Транзакция {transaction_id} имеет статус '{trans_status}', ожидался 'success'"
            )
        
        # 3. Проверка соответствия coachId в transactions и coach в coachwallethistories
        wh_coach = str(wh_record.get("coach", ""))
        
        # Ищем coachId в paidFor.serviceProducts
        paid_for = transaction.get("paidFor", {})
        service_products = paid_for.get("serviceProducts", [])
        
        coach_found = False
        for sp in service_products:
            sp_coach_id = str(sp.get("coachId", ""))
            if sp_coach_id == wh_coach:
                coach_found = True
                break
        
        if not coach_found and service_products:
            issues.append(
                f"Coach {wh_coach} не найден в transactions.paidFor.serviceProducts "
                f"для транзакции {transaction_id}"
            )
        
        # 4. Проверка соответствия userServiceProductId
        wh_source = str(wh_record.get("source", ""))
        wh_source_type = wh_record.get("sourceType", "")
        
        if wh_source_type == "UserServiceProducts":
            usp_found = False
            for sp in service_products:
                sp_usp_id = str(sp.get("userServiceProductId", ""))
                if sp_usp_id == wh_source:
                    usp_found = True
                    break
            
            if not usp_found:
                issues.append(
                    f"UserServiceProduct {wh_source} не найден в transactions.paidFor.serviceProducts "
                    f"для транзакции {transaction_id}"
                )
        
        # 5. Проверка времени: transactions.time должен быть раньше coachwallethistories.createdAt
        wh_created = wh_record.get("createdAt")
        trans_time = transaction.get("time") or transaction.get("created_at")
        
        if wh_created and trans_time:
            if trans_time > wh_created:
                issues.append(
                    f"Временная последовательность нарушена: transactions.time ({trans_time}) "
                    f"позже coachwallethistories.createdAt ({wh_created}) для транзакции {transaction_id}"
                )
    
    if issues:
        print(f"❌ Найдено {len(issues)} проблем в данных transactions:")
        for issue in issues[:10]:  # Показываем первые 10
            print(f"   {issue}")
        return False
    
    print(f"✅ Данные в transactions корректны (проверено {checked_count} транзакций)")
    return True


@log_function_call
def validate_coach_wallet(db, coach_user_id: Any) -> Dict[str, bool]:
    """
    Комплексная проверка кошелька тренера.
    Выполняет все проверки и возвращает результаты.
    """
    print(f"\n{'=' * 80}")
    print(f"КОМПЛЕКСНАЯ ПРОВЕРКА КОШЕЛЬКА ТРЕНЕРА: {coach_user_id}")
    print(f"{'=' * 80}")
    
    results = {
        "balance_consistency": check_wallet_balance_consistency(db, coach_user_id),
        "commission_calculations": check_commission_calculations(db, coach_user_id),
        "duplicate_transactions": check_duplicate_transactions(db, coach_user_id),
        "transaction_sequence": check_transaction_sequence(db, coach_user_id),
        "negative_balance": check_negative_balance(db, coach_user_id),
        "data_integrity": check_data_integrity(db, coach_user_id),
        "transactions_data": check_transactions_data(db, coach_user_id)
    }
    
    print(f"\n{'=' * 80}")
    print("ИТОГИ ПРОВЕРКИ:")
    print(f"{'=' * 80}")
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {check_name}")
    
    all_passed = all(results.values())
    print(f"\n{'✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ' if all_passed else '❌ НАЙДЕНЫ ОШИБКИ'}")
    
    return results

