from pprint import pprint

from src.repositories.coaches_repository import get_coach_by_user_id
from src.repositories.coachwallethistories_repository import check_coach_payment, get_latest_coach_wallet_history
from src.repositories.masterspecialists_repository import get_master_specialist_by_id
from src.repositories.serviceproducts_repository import get_serviceproduct_by_id
from src.repositories.specialists_repository import get_specialist_by_id
from src.repositories.userserviceproducts_repository import get_userserviceproduct_by_id


def display_userserviceproduct_chain(db, userserviceproduct_id: str, width: int = 120):
    """
    Выводит информацию по userserviceproduct и всей цепочке связанных сущностей:
    userserviceproduct -> serviceproduct -> specialist -> master_specialist
    """
    userserviceproduct = get_userserviceproduct_by_id(db, userserviceproduct_id)
    if not userserviceproduct:
        print("⚠️ UserServiceProduct не найден.")
        return

    pprint(userserviceproduct, sort_dicts=False, width=width)

    serviceproduct_id = userserviceproduct.get("serviceProduct")
    if not serviceproduct_id:
        print("⚠️ В userserviceproduct отсутствует поле serviceProduct.")
        return

    serviceproduct = get_serviceproduct_by_id(db, serviceproduct_id)
    if not serviceproduct:
        print("⚠️ Service product не найден.")
        return

    pprint(serviceproduct, sort_dicts=False, width=width)

    specialist_id = serviceproduct.get("specialist")
    if not specialist_id:
        print("⚠️ В serviceproduct отсутствует поле specialist.")
        return

    specialist = get_specialist_by_id(db, specialist_id)
    if not specialist:
        print("⚠️ Specialist не найден.")
        return

    pprint(specialist, sort_dicts=False, width=width)

    master_specialist_id = specialist.get("masterSpecialist")
    if not master_specialist_id:
        print("⚠️ В specialist отсутствует поле masterSpecialist.")
        return

    master_specialist = get_master_specialist_by_id(db, master_specialist_id)
    if master_specialist:
        pprint(master_specialist, sort_dicts=False, width=width)
    else:
        print("⚠️ Master specialist не найден.")


def display_coach_by_user_id(db, user_id: str, width: int = 120):
    """
    Выводит информацию о coach по user_id.
    """
    coach = get_coach_by_user_id(db, user_id)
    if coach:
        pprint(coach, sort_dicts=False, width=width)
    else:
        print("⚠️ Coach не найден.")


def display_coach_wallet_payment(db, coach_user_id: str = None, expected_amount: float = None):
    """
    Выводит информацию о последнем начислении денег тренеру из coachwallethistories.
    
    Args:
        db: База данных MongoDB
        coach_user_id: ID тренера (опционально)
        expected_amount: Ожидаемая сумма начисления (опционально)
    """
    result = check_coach_payment(db, coach_user_id, expected_amount)
    return result

