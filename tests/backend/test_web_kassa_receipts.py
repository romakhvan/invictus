"""
Тест проверки создания чеков с транзакциями для клубов с web-кассами.
"""

import pytest
import pymongo
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from src.utils.repository_helpers import get_collection
from src.config.db_config import MONGO_URI_PROD, DB_NAME


@pytest.fixture(scope="module")
def db():
    """
    Фикстура для подключения к MongoDB PROD.
    """
    print("\nConnecting to MongoDB PROD...")
    client = pymongo.MongoClient(MONGO_URI_PROD)
    db = client[DB_NAME]
    yield db
    print("\nClosing Mongo PROD connection.")
    client.close()


def normalize_club_name(name: str) -> str:
    """
    Нормализует название клуба для сравнения.
    Убирает лишние пробелы, приводит к нижнему регистру,
    и учитывает вариации транслитерации казахских имен.
    
    Args:
        name: Название клуба
        
    Returns:
        Нормализованное название
    """
    normalized = name.strip().lower().replace("  ", " ")
    
    # Словарь замен для вариаций транслитерации
    replacements = {
        "qonaev": "qonayev",
        "satpayeva": "satpayev",
        "sharipova": "sharipov",
        "mangilik el": "mangilik yel",
        "koshkarbayeva": "koshkarbayev",
    }
    
    for old, new in replacements.items():
        if old in normalized:
            normalized = normalized.replace(old, new)
    
    return normalized


def load_clubs_with_web_kassas() -> List[str]:
    """
    Считывает список клубов из файла.
    
    Returns:
        Список названий клубов
    """
    file_path = Path("data/clubs_with_web_kassas.txt")
    with open(file_path, "r", encoding="utf-8") as f:
        clubs = [line.strip() for line in f if line.strip()]
    return clubs


@pytest.mark.parametrize("days,min_success_rate", [
    (30, 60),   # Последние 30 дней, минимум 60% успешных чеков
])
def test_receipts_creation_for_web_kassa_clubs(db, days, min_success_rate):
    """
    Проверяет создание чеков (webkassas) для транзакций в клубах с web-кассами.
    
    Проверяет:
    1. Наличие транзакций с webKassaIds для клубов из списка
    2. Соответствие webKassaIds записям в коллекции webkassas
    3. Статус чеков (должен быть 'success')
    4. Согласованность данных между transactions и webkassas
    
    Args:
        db: Фикстура подключения к MongoDB
        days: Количество дней для проверки транзакций
        min_success_rate: Минимальный процент успешных чеков (по умолчанию 60%)
    """
    print("\n" + "=" * 80)
    print("ПРОВЕРКА СОЗДАНИЯ ЧЕКОВ ДЛЯ КЛУБОВ С WEB-КАССАМИ")
    print("=" * 80)
    
    # Шаг 1: Загружаем список клубов
    club_names = load_clubs_with_web_kassas()
    print(f"\nЗагружено клубов из файла: {len(club_names)}")
    
    # Шаг 2: Получаем все клубы из БД
    clubs_col = get_collection(db, "clubs")
    all_clubs = list(clubs_col.find({}, {"name": 1}))
    
    # Создаем словарь для нормализованного поиска
    normalized_db_clubs = {normalize_club_name(club["name"]): club for club in all_clubs}
    
    # Ищем клубы по нормализованным названиям
    found_clubs = []
    not_found = []
    
    for club_name in club_names:
        normalized = normalize_club_name(club_name)
        if normalized in normalized_db_clubs:
            found_clubs.append(normalized_db_clubs[normalized])
        else:
            not_found.append(club_name)
    
    clubs = found_clubs
    club_ids = [club["_id"] for club in clubs]
    club_name_to_id = {club["name"]: club["_id"] for club in clubs}
    
    print(f"Найдено клубов в БД: {len(clubs)}")
    
    if not_found:
        print(f"Внимание! Не найдено в БД ({len(not_found)} клубов):")
        for club_name in sorted(not_found)[:10]:  # Показываем первые 10
            print(f"  - {club_name}")
    
    assert len(clubs) > 0, "Не найдено ни одного клуба из списка в БД"
    
    # Шаг 3: Получаем транзакции за указанный период для этих клубов
    now = datetime.now()
    days_ago = now - timedelta(days=days)
    
    print(f"\nПериод проверки транзакций (последние {days} дней):")
    print(f"  С: {days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  По: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    transactions_col = get_collection(db, "transactions")
    transactions = list(transactions_col.find({
        "clubId": {"$in": club_ids},
        "status": "success",
        "created_at": {"$gte": days_ago},
        "isDeleted": False
    }).sort("created_at", -1))
    
    print(f"\nНайдено успешных транзакций: {len(transactions)}")
    
    # Шаг 4: Анализируем транзакции
    transactions_with_webkassa = []
    transactions_without_webkassa = []
    
    for trans in transactions:
        webkassa_ids = trans.get("webKassaIds", [])
        if webkassa_ids and len(webkassa_ids) > 0:
            transactions_with_webkassa.append(trans)
        else:
            transactions_without_webkassa.append(trans)
    
    print(f"\nТранзакции с webKassaIds: {len(transactions_with_webkassa)}")
    print(f"Транзакции БЕЗ webKassaIds: {len(transactions_without_webkassa)}")
    
    # Шаг 5: Получаем все webKassaIds для проверки
    all_webkassa_ids = []
    for trans in transactions_with_webkassa:
        webkassa_ids = trans.get("webKassaIds", [])
        all_webkassa_ids.extend(webkassa_ids)
    
    print(f"Всего webKassaIds для проверки: {len(all_webkassa_ids)}")
    
    # Шаг 6: Проверяем существование записей в webkassas
    webkassas_col = get_collection(db, "webkassas")
    found_webkassas = list(webkassas_col.find({"_id": {"$in": all_webkassa_ids}}))
    found_webkassa_ids = {wk["_id"] for wk in found_webkassas}
    
    print(f"Найдено записей в webkassas: {len(found_webkassas)}")
    
    # Проверка: все webKassaIds должны существовать в webkassas
    missing_webkassa_ids = set(all_webkassa_ids) - found_webkassa_ids
    if missing_webkassa_ids:
        print(f"\nОШИБКА: Не найдено {len(missing_webkassa_ids)} записей в webkassas:")
        for wk_id in list(missing_webkassa_ids)[:5]:
            print(f"  - {wk_id}")
    
    # Шаг 7: Проверяем статусы чеков
    webkassa_statuses = {}
    for wk in found_webkassas:
        status = wk.get("status", "unknown")
        webkassa_statuses[status] = webkassa_statuses.get(status, 0) + 1
    
    print(f"\nСтатусы чеков в webkassas:")
    for status, count in webkassa_statuses.items():
        print(f"  {status}: {count}")
    
    failed_webkassas = [wk for wk in found_webkassas if wk.get("status") != "success"]
    if failed_webkassas:
        print(f"\nВнимание! Найдено {len(failed_webkassas)} чеков с ошибками:")
        for wk in failed_webkassas[:5]:
            print(f"  _id: {wk['_id']}, status: {wk.get('status')}, club: {wk.get('club')}")
    
    # Шаг 8: Проверяем согласованность club между transactions и webkassas
    print("\n" + "=" * 80)
    print("ПРОВЕРКА СОГЛАСОВАННОСТИ ДАННЫХ")
    print("=" * 80)
    
    club_mismatches = []
    
    for trans in transactions_with_webkassa[:100]:  # Проверяем первые 100
        trans_club_id = trans.get("clubId")
        webkassa_ids = trans.get("webKassaIds", [])
        
        for wk_id in webkassa_ids:
            wk = next((w for w in found_webkassas if w["_id"] == wk_id), None)
            if wk:
                wk_club_id = wk.get("club")
                if trans_club_id != wk_club_id:
                    club_mismatches.append({
                        "transaction_id": trans["_id"],
                        "webkassa_id": wk_id,
                        "transaction_club": trans_club_id,
                        "webkassa_club": wk_club_id
                    })
    
    if club_mismatches:
        print(f"\nОШИБКА: Несоответствие клубов ({len(club_mismatches)} случаев):")
        for mismatch in club_mismatches[:5]:
            print(f"  Transaction {mismatch['transaction_id']} -> club {mismatch['transaction_club']}")
            print(f"  WebKassa {mismatch['webkassa_id']} -> club {mismatch['webkassa_club']}")
    
    # Шаг 9: Статистика по клубам
    print("\n" + "=" * 80)
    print("СТАТИСТИКА ПО КЛУБАМ")
    print("=" * 80)
    
    club_stats = {}
    for trans in transactions:
        club_id = trans.get("clubId")
        if club_id not in club_stats:
            club_stats[club_id] = {
                "total_transactions": 0,
                "with_webkassa": 0,
                "without_webkassa": 0
            }
        club_stats[club_id]["total_transactions"] += 1
        
        webkassa_ids = trans.get("webKassaIds", [])
        if webkassa_ids and len(webkassa_ids) > 0:
            club_stats[club_id]["with_webkassa"] += 1
        else:
            club_stats[club_id]["without_webkassa"] += 1
    
    # Сортируем по количеству транзакций без чеков
    sorted_clubs = sorted(
        club_stats.items(),
        key=lambda x: x[1]["without_webkassa"],
        reverse=True
    )
    
    print(f"\nТоп-10 клубов с транзакциями БЕЗ чеков:")
    print(f"{'Клуб':<35} {'Всего':<7} {'С чеком':<10} {'БЕЗ чека':<10} {'% БЕЗ':<7}")
    print("=" * 80)
    
    for club_id, stats in sorted_clubs[:10]:
        club_name = next((name for name, cid in club_name_to_id.items() if cid == club_id), "Unknown")
        percent_without = (stats["without_webkassa"] / stats["total_transactions"]) * 100 if stats["total_transactions"] > 0 else 0
        print(f"{club_name:<35} {stats['total_transactions']:<7} {stats['with_webkassa']:<10} "
              f"{stats['without_webkassa']:<10} {percent_without:>5.1f}%")
    
    # Итоговая статистика
    print("\n" + "=" * 80)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    print(f"Всего клубов проверено: {len(clubs)}")
    print(f"Всего транзакций за период: {len(transactions)}")
    print(f"Транзакций с webKassaIds: {len(transactions_with_webkassa)}")
    print(f"Транзакций БЕЗ webKassaIds: {len(transactions_without_webkassa)}")
    print(f"Всего webKassaIds: {len(all_webkassa_ids)}")
    print(f"Найдено записей в webkassas: {len(found_webkassas)}")
    print(f"Чеков со статусом 'success': {webkassa_statuses.get('success', 0)}")
    print(f"Чеков с другими статусами: {len(found_webkassas) - webkassa_statuses.get('success', 0)}")
    
    # Проверки
    print("\n" + "=" * 80)
    print("РЕЗУЛЬТАТЫ ПРОВЕРОК")
    print("=" * 80)
    
    checks_passed = []
    checks_failed = []
    
    # Проверка 1: Все webKassaIds должны существовать
    if len(missing_webkassa_ids) == 0:
        checks_passed.append("Все webKassaIds существуют в webkassas")
    else:
        checks_failed.append(f"Не найдено {len(missing_webkassa_ids)} записей в webkassas")
    
    # Проверка 2: Нет несоответствий клубов
    if len(club_mismatches) == 0:
        checks_passed.append("Клубы согласованы между transactions и webkassas")
    else:
        checks_failed.append(f"Найдено {len(club_mismatches)} несоответствий клубов")
    
    # Проверка 3: Большинство чеков должны быть успешными (если есть чеки)
    if found_webkassas:
        success_rate = (webkassa_statuses.get('success', 0) / len(found_webkassas) * 100)
        if success_rate >= min_success_rate:
            checks_passed.append(f"Успешных чеков: {success_rate:.1f}% (>= {min_success_rate}%)")
        else:
            checks_failed.append(f"Низкая доля успешных чеков: {success_rate:.1f}% (ожидается >= {min_success_rate}%)")
    else:
        success_rate = 0
        checks_failed.append("Нет чеков для проверки")
    
    # Проверка 4: Должны быть транзакции с webKassaIds
    if len(transactions_with_webkassa) > 0:
        checks_passed.append(f"Найдено {len(transactions_with_webkassa)} транзакций с чеками")
    else:
        checks_failed.append("Нет транзакций с webKassaIds за указанный период")
    
    print(f"\nПройдено проверок: {len(checks_passed)}")
    for check in checks_passed:
        print(f"  OK: {check}")
    
    if checks_failed:
        print(f"\nНе пройдено проверок: {len(checks_failed)}")
        for check in checks_failed:
            print(f"  FAIL: {check}")
    
    print("=" * 80)
    
    # Assertion: проверяем критичные условия
    assert len(missing_webkassa_ids) == 0, \
        f"Обнаружено {len(missing_webkassa_ids)} webKassaIds, которые не существуют в webkassas"
    
    assert len(club_mismatches) == 0, \
        f"Обнаружено {len(club_mismatches)} несоответствий клубов между transactions и webkassas"
    
    # Проверяем успешность чеков только если они есть
    if found_webkassas:
        assert success_rate >= min_success_rate, \
            f"Слишком низкая доля успешных чеков: {success_rate:.1f}% (ожидается >= {min_success_rate}%)"
    
    # Проверяем наличие транзакций с чеками
    assert len(transactions_with_webkassa) > 0, \
        f"Не найдено транзакций с webKassaIds за последние {days} дней для клубов из списка"


def test_webkassas_basic_structure(db):
    """
    Быстрая проверка базовой структуры webkassas.
    Проверяет, что коллекция webkassas существует и содержит записи с корректной структурой.
    """
    print("\n" + "=" * 80)
    print("БЫСТРАЯ ПРОВЕРКА СТРУКТУРЫ WEBKASSAS")
    print("=" * 80)
    
    webkassas_col = get_collection(db, "webkassas")
    
    # Получаем последние 10 записей
    recent_webkassas = list(webkassas_col.find().sort("created_at", -1).limit(10))
    
    print(f"\nПолучено записей: {len(recent_webkassas)}")
    
    assert len(recent_webkassas) > 0, "Коллекция webkassas пуста"
    
    # Проверяем структуру первой записи
    first_record = recent_webkassas[0]
    required_fields = ["_id", "user", "club", "status", "body"]
    
    print("\nПроверка обязательных полей:")
    for field in required_fields:
        has_field = field in first_record
        status_mark = "OK" if has_field else "FAIL"
        print(f"  {field}: {status_mark}")
        assert has_field, f"Отсутствует обязательное поле: {field}"
    
    # Статистика по статусам
    statuses = {}
    for wk in recent_webkassas:
        status = wk.get("status", "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    
    print(f"\nСтатусы последних {len(recent_webkassas)} чеков:")
    for status, count in statuses.items():
        print(f"  {status}: {count}")
    
    print("\nСтруктура webkassas корректна")
    print("=" * 80)

