import pytest_check as check
from src.validators.coach_wallet_validator import (
    validate_coach_wallet,
    check_wallet_balance_consistency,
    check_commission_calculations,
    check_duplicate_transactions,
    check_transaction_sequence,
    check_negative_balance,
    check_data_integrity,
    check_transactions_data
)
from src.repositories.transactions_repository import (
    display_transactions_structure,
    get_transactions_with_coach_summary,
    analyze_transactions_collaboration_types
)

# ID тренера для тестирования (можно изменить при необходимости)
COACH_USER_ID = "66d030cf0f02c0003eed0eb9"

def test_coach_wallet_full_validation(db):
    """
    🧪 Комплексная проверка кошелька тренера.
    Выполняет все проверки для выявления ошибок поступления/списания денег.
    """
    
    print("\n" + "=" * 80)
    print("ТЕСТ: Комплексная проверка кошелька тренера")
    print("=" * 80)
    
    results = validate_coach_wallet(db, COACH_USER_ID)
    
    # Проверяем, что все тесты прошли
    for check_name, result in results.items():
        check.is_true(
            result,
            f"❌ Проверка {check_name} не прошла"
        )


def test_coach_wallet_balance_consistency(db):
    """
    🧪 Проверка согласованности баланса кошелька.
    """
    result = check_wallet_balance_consistency(db, COACH_USER_ID)
    check.is_true(result, "Баланс кошелька не согласован с историей транзакций")


def test_coach_wallet_commissions(db):
    """
    🧪 Проверка корректности расчёта комиссий.
    """
    result = check_commission_calculations(db, COACH_USER_ID)
    check.is_true(result, "Обнаружены ошибки в расчёте комиссий")


def test_coach_wallet_no_duplicates(db):
    """
    🧪 Проверка на отсутствие дубликатов транзакций.
    """
    result = check_duplicate_transactions(db, COACH_USER_ID, days=30)
    check.is_true(result, "Обнаружены дублирующиеся транзакции")


def test_coach_wallet_sequence(db):
    """
    🧪 Проверка последовательности транзакций.
    """
    result = check_transaction_sequence(db, COACH_USER_ID)
    check.is_true(result, "Обнаружены нарушения в последовательности транзакций")


def test_coach_wallet_no_negative_balance(db):
    """
    🧪 Проверка отсутствия отрицательных балансов.
    """
    result = check_negative_balance(db)
    check.is_true(result, "Обнаружены кошельки с отрицательным балансом")


def test_coach_wallet_data_integrity(db):
    """
    🧪 Проверка целостности данных.
    """
    result = check_data_integrity(db, COACH_USER_ID)
    check.is_true(result, "Обнаружены проблемы целостности данных")


def test_coach_wallet_transactions_data(db):
    """
    🧪 Проверка данных в transactions.
    """
    result = check_transactions_data(db, COACH_USER_ID)
    check.is_true(result, "Обнаружены проблемы в данных transactions")


def test_display_mobile_transactions_with_coach(db):
    """
    🧪 Вывод транзакций с тренерами из источника 'mobile'.
    Показывает структуру транзакций для анализа появления операций в кошельке тренера.
    """
    print("\n" + "=" * 80)
    print("ТЕСТ: Вывод транзакций с тренерами (source='mobile')")
    print("=" * 80)
    
    # Исключаем ненужные поля для более читаемого вывода
    projection = {
        "__v": 0,
        "metadata": 0,
        "kaspiId": 0,
        "parts": 0,
    }
    
    # Выводим статистику
    get_transactions_with_coach_summary(db, source="mobile", projection=projection)
    
    # Выводим первые 5 записей для анализа структуры
    display_transactions_structure(db, source="mobile", limit=1, projection=projection)


def test_analyze_coach_collaboration_types(db):
    """
    🧪 Анализ типов сотрудничества тренеров в транзакциях.
    Определяет, является ли тренер "buhta" или "staff" для каждого клуба.
    """
    print("\n" + "=" * 80)
    print("ТЕСТ: Анализ типов сотрудничества тренеров")
    print("=" * 80)
    
    # Анализируем транзакции за последние 7 дней
    result = analyze_transactions_collaboration_types(
        db,
        source="mobile",
        days=7,
        limit=50  # Анализируем первые 50 транзакций
    )
    
    # Проверяем, что анализ выполнен
    check.is_not_none(result, "Результат анализа должен быть получен")
    check.greater(result["total_analyzed"], 0, "Должны быть проанализированы транзакции")

