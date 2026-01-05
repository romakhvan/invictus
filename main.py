from pprint import pprint

from pymongo import MongoClient

from src.config.db_config import DB_NAME, MONGO_URI
from src.repositories.coachwallethistories_repository import get_latest_coach_wallet_history, get_coach_wallet
from src.utils.display_utils import display_coach_by_user_id, display_userserviceproduct_chain

COACH_USER_ID = '638349f9a61a9500271df16a'  # подставьте желаемый user_id для просмотра coach-записи


if __name__ == "__main__":
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Просмотр записи из coachwallets
    print("=" * 80)
    print("Просмотр записи из coachwallets")
    print("=" * 80)
    wallet_record = get_coach_wallet(db)
    if wallet_record:
        print("\n📄 Структура записи coachwallets:")
        pprint(wallet_record, sort_dicts=False, width=120)
    
    # Просмотр последней записи из coachwallethistories
    print("\n" + "=" * 80)
    print("Просмотр последней записи из coachwallethistories")
    print("=" * 80)
    latest_record = get_latest_coach_wallet_history(db)
    if latest_record:
        print("\n📄 Структура последней записи:")
        pprint(latest_record, sort_dicts=False, width=120)
    
    # Просмотр записи из transactions
    print("\n" + "=" * 80)
    print("Просмотр записи из transactions")
    print("=" * 80)
    if latest_record and latest_record.get("transaction"):
        from src.utils.repository_helpers import get_collection
        transactions_col = get_collection(db, "transactions")
        transaction_id = latest_record.get("transaction")
        transaction_record = transactions_col.find_one({"_id": transaction_id})
        if transaction_record:
            print("\n📄 Структура записи transactions:")
            pprint(transaction_record, sort_dicts=False, width=120)
        else:
            print(f"\n❌ Транзакция {transaction_id} не найдена в коллекции transactions")
    
    # Проверка начисления денег тренеру
    print("\n" + "=" * 80)
    print("Проверка начисления денег тренеру")
    print("=" * 80)
    from src.repositories.coachwallethistories_repository import check_coach_payment
    payment_result = check_coach_payment(db)

    if COACH_USER_ID:
        display_coach_by_user_id(db, COACH_USER_ID)

    display_userserviceproduct_chain(db, "6920c9b9376bbb406d592d7c")