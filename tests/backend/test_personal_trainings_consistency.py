"""
Тест на консистентность количества персональных тренировок клиента
в разных коллекциях MongoDB.
"""

import pytest
import pymongo
import allure
import json
from bson import ObjectId
from src.utils.repository_helpers import get_collection
from src.config.db_config import MONGO_URI_PROD, MONGO_URI_STAGE, DB_NAME


def _results_to_html_table(results_list, title=""):
    """Формирует HTML-таблицу из списка results для отображения в Allure (все колонки, включая Created at)."""
    headers = ["№", "USP ID", "User ID", "Init", "Count", "Tickets", "Hist", "Status", "Updated At", "Created At"]
    rows = []
    for r in results_list:
        updated_str = r["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if r["updated_at"] != "N/A" else "N/A"
        created_str = r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] != "N/A" else "N/A"
        rows.append([
            str(r["idx"]), r["usp_id"], r["user_id"],
            str(r["initial_count"]), str(r["count"]), str(r["tickets_count"]), str(r["hist_count"]),
            r["status"], updated_str, created_str
        ])
    th_cells = "".join(f"<th>{h}</th>" for h in headers)
    trs = []
    for row in rows:
        trs.append("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>")
    table_body = "".join(trs)
    html = f'<table border="1" cellpadding="4" cellspacing="0"><thead><tr>{th_cells}</tr></thead><tbody>{table_body}</tbody></table>'
    return html


# ========== КОНФИГУРАЦИЯ ОКРУЖЕНИЯ ==========
# Выберите окружение базы данных: 'prod' или 'stage'
ENVIRONMENT = 'prod'  # 'prod' или 'stage'
# ============================================


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB.
    Окружение определяется переменной ENVIRONMENT.
    """
    mongo_uri = MONGO_URI_PROD if ENVIRONMENT == 'prod' else MONGO_URI_STAGE
    env_name = ENVIRONMENT.upper()
    
    print(f"\nConnecting to MongoDB {env_name}...")
    client = pymongo.MongoClient(mongo_uri)
    db = client[DB_NAME]
    yield db
    print(f"\nClosing Mongo {env_name} connection.")
    client.close()


@allure.feature("Backend Data Consistency")
@allure.story("Personal Trainings")
@allure.title("Проверка консистентности персональных тренировок")
@allure.description("""
Проверяет консистентность количества персональных тренировок
для записей userserviceproducts.

Сравнивает:
1. count в userserviceproducts
2. количество активных неиспользованных билетов в trainingtickets
3. currentCount в последней записи userserviceproductshistories
""")
@allure.severity(allure.severity_level.CRITICAL)
@allure.link("https://invictus.entryx.io/user-service-products/")
@allure.link("https://invictus.entryx.io/users")

def test_personal_trainings_count_consistency_last_20(db):
    """
    Проверяет консистентность количества персональных тренировок
    для всех записей userserviceproducts за последние 2 дня.
    
    Сравнивает:
    1. count в userserviceproducts
    2. количество активных неиспользованных билетов в trainingtickets
    3. currentCount в последней записи userserviceproductshistories
    """
    # ========== КОНФИГУРАЦИЯ ТЕСТА ==========
    # Окружение БД настраивается в начале файла (переменная ENVIRONMENT)
    # 
    # Выберите режим проверки:
    # 1. Конкретная запись по ID: укажите SPECIFIC_USP_ID
    # 2. Фильтр по дате: установите SPECIFIC_USP_ID = None и настройте DAYS_AGO
    
    SPECIFIC_USP_ID = None  # Установите None для проверки по дате
    DAYS_AGO = 7  # Количество дней для фильтра по updated_at
    # ========================================
    
    print("\n" + "=" * 80)
    print("ПРОВЕРКА КОНСИСТЕНТНОСТИ ПЕРСОНАЛЬНЫХ ТРЕНИРОВОК")
    print(f"Окружение: {ENVIRONMENT.upper()}")
    print("=" * 80)
    
    with allure.step(f"Подключение к коллекции userserviceproducts ({ENVIRONMENT.upper()})"):
        usp_col = get_collection(db, "userserviceproducts")
    
    from datetime import datetime, timedelta

    with allure.step("Получение записей userserviceproducts для проверки"):
        if SPECIFIC_USP_ID:
            # Режим 1: Проверка конкретной записи по ID
            print(f"Режим: Проверка конкретной записи")
            print(f"ID записи: {SPECIFIC_USP_ID}")
            
            usp_record = usp_col.find_one({
                "_id": ObjectId(SPECIFIC_USP_ID),
                "isDeleted": False
            })
            
            latest_usps = [usp_record] if usp_record else []
        else:
            # Режим 2: Фильтр по дате
            now = datetime.now()
            days_ago = now - timedelta(days=DAYS_AGO)
            
            print(f"Режим: Проверка записей за период")
            print(f"\nПериод проверки:")
            print(f"  С: {days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  По: {now.strftime('%Y-%m-%d %H:%M:%S')}")
            
            latest_usps = list(
                usp_col.find({
                    "isDeleted": False,
                    "isActive": True,
                    "updated_at": {"$gte": days_ago}
                }).sort("updated_at", -1)
            )
        
        print(f"\nПолучено записей userserviceproducts: {len(latest_usps)}")
        allure.attach(f"Количество записей: {len(latest_usps)}", name="Записи для проверки", attachment_type=allure.attachment_type.TEXT)
    
    if not latest_usps:
        print("Нет записей для проверки")
        return
    
    # Шаг 2: BATCH получение данных (оптимизация)
    with allure.step("Получение связанных данных из БД (batch запросы)"):
        tt_col = get_collection(db, "trainingtickets")
        hist_col = get_collection(db, "userserviceproductshistories")
        
        # Собираем все ID для batch-запроса
        usp_ids = [usp['_id'] for usp in latest_usps]
        
        print("\nПолучение данных из trainingtickets (batch)...")
        # Получаем количество билетов для всех userServiceProduct за один запрос
        tickets_pipeline = [
            {
                "$match": {
                    "userServiceProduct": {"$in": usp_ids},
                    "isUsed": False,
                    "status": "active",
                    "isDeleted": False
                }
            },
            {
                "$group": {
                    "_id": "$userServiceProduct",
                    "count": {"$sum": 1}
                }
            }
        ]
        tickets_counts = {doc['_id']: doc['count'] for doc in tt_col.aggregate(tickets_pipeline)}
        
        print("Получение данных из userserviceproductshistories (batch)...")
        # Получаем последние записи истории для всех userServiceProduct
        history_pipeline = [
            {
                "$match": {
                    "userServiceProduct": {"$in": usp_ids}
                }
            },
            {
                "$sort": {"created_at": -1}
            },
            {
                "$group": {
                    "_id": "$userServiceProduct",
                    "lastRecord": {"$first": "$$ROOT"}
                }
            }
        ]
        history_counts = {
            doc['_id']: doc['lastRecord'].get('currentCount', 'N/A') 
            for doc in hist_col.aggregate(history_pipeline)
        }
        
        print("Анализ данных...")
    # Шаг 3: Анализируем результаты
    with allure.step("Анализ консистентности данных"):
        results = []
        
        for idx, usp in enumerate(latest_usps, start=1):
            usp_id = usp['_id']
            user_id = usp['user']
            initial_count = usp.get('initialCount', 'N/A')
            count = usp.get('count', 'N/A')
            updated_at = usp.get('updated_at', 'N/A')
            created_at = usp.get('created_at', 'N/A')
            
            tickets_count = tickets_counts.get(usp_id, 0)
            hist_count = history_counts.get(usp_id, 'N/A')
            
            # Проверяем консистентность
            status = "OK"
            if count != 'N/A' and tickets_count != count:
                status = "FAIL"
            if count != 'N/A' and hist_count != 'N/A' and hist_count != count:
                status = "FAIL"
            if tickets_count != 'N/A' and hist_count != 'N/A' and tickets_count != hist_count:
                status = "FAIL"
            
            results.append({
                'idx': idx,
                'usp_id': str(usp_id),
                'user_id': str(user_id),
                'initial_count': initial_count,
                'count': count,
                'tickets_count': tickets_count,
                'hist_count': hist_count,
                'status': status,
                'updated_at': updated_at,
                'created_at': created_at
            })
    
    # Статистика общая
    failed_count = sum(1 for r in results if r['status'] == 'FAIL')
    ok_count = sum(1 for r in results if r['status'] == 'OK')
    
    print(f"\nОбщая статистика:")
    print(f"  Всего проверено записей: {len(results)}")
    print(f"  OK:   {ok_count}")
    print(f"  FAIL: {failed_count}")
    
    # Allure: Прикрепляем общую статистику
    stats_text = f"""
Окружение: {ENVIRONMENT.upper()}
Период проверки: {DAYS_AGO if not SPECIFIC_USP_ID else 'Конкретная запись'}
Всего проверено записей: {len(results)}
OK: {ok_count}
FAIL: {failed_count}
"""
    allure.attach(stats_text.strip(), name="Общая статистика", attachment_type=allure.attachment_type.TEXT)
    
    # Выводим все записи с расхождениями
    if failed_count > 0:
        failed_records = [r for r in results if r['status'] == 'FAIL']
        displayed_records = failed_records
        
        print("\n" + "=" * 190)
        print(f"ЗАПИСИ С РАСХОЖДЕНИЯМИ (всего {failed_count}):")
        print("=" * 190)
        print(f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} {'Tickets':<8} {'Hist':<5} {'Status':<7} {'Updated At':<22} {'Created At':<22}")
        print("=" * 190)
        
        # Формируем таблицу для Allure
        table_lines = [
            f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} {'Tickets':<8} {'Hist':<5} {'Status':<7} {'Updated At':<22} {'Created At':<22}",
            "=" * 190
        ]
        
        for r in displayed_records:
            updated_str = r['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if r['updated_at'] != 'N/A' else 'N/A'
            created_str = r['created_at'].strftime('%Y-%m-%d %H:%M:%S') if r['created_at'] != 'N/A' else 'N/A'
            
            line = (f"{r['idx']:<4} {r['usp_id']:<26} {r['user_id']:<26} "
                   f"{str(r['initial_count']):<5} {str(r['count']):<6} "
                   f"{str(r['tickets_count']):<8} {str(r['hist_count']):<5} "
                   f"{r['status']:<7} {updated_str:<22} {created_str:<22}")
            
            print(line)
            table_lines.append(line)
        
        print("=" * 190)
        
        # Allure: Прикрепляем таблицу расхождений (TEXT + HTML для корректного отображения колонки Created at)
        table_text = "\n".join(table_lines)
        allure.attach(table_text, name=f"Записи с расхождениями ({failed_count})", attachment_type=allure.attachment_type.TEXT)
        allure.attach(_results_to_html_table(failed_records), name=f"Записи с расхождениями ({failed_count}) — таблица", attachment_type=allure.attachment_type.HTML)
        
        # Отдельная таблица для расхождений между USP и TrainingTickets
        usp_tt_mismatch = [
            r for r in failed_records 
            if r['count'] != 'N/A' and r['tickets_count'] != r['count']
        ]
        
        if usp_tt_mismatch:
            usp_tt_count = len(usp_tt_mismatch)
            print("\n" + "=" * 190)
            print(f"РАСХОЖДЕНИЯ МЕЖДУ USERSERVICEPRODUCTS И TRAININGTICKETS (всего {usp_tt_count}):")
            print("=" * 190)
            print(f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} {'Tickets':<8} {'Hist':<5} {'Status':<7} {'Updated At':<22} {'Created At':<22}")
            print("=" * 190)
            
            # Формируем таблицу для Allure
            usp_tt_table_lines = [
                f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} {'Tickets':<8} {'Hist':<5} {'Status':<7} {'Updated At':<22} {'Created At':<22}",
                "=" * 190
            ]
            
            for r in usp_tt_mismatch:
                updated_str = r['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if r['updated_at'] != 'N/A' else 'N/A'
                created_str = r['created_at'].strftime('%Y-%m-%d %H:%M:%S') if r['created_at'] != 'N/A' else 'N/A'
                
                line = (f"{r['idx']:<4} {r['usp_id']:<26} {r['user_id']:<26} "
                       f"{str(r['initial_count']):<5} {str(r['count']):<6} "
                       f"{str(r['tickets_count']):<8} {str(r['hist_count']):<5} "
                       f"{r['status']:<7} {updated_str:<22} {created_str:<22}")
                
                print(line)
                usp_tt_table_lines.append(line)
            
            print("=" * 190)
            
            # Allure: Прикрепляем таблицу расхождений USP vs TT (TEXT + HTML для колонки Created at)
            usp_tt_table_text = "\n".join(usp_tt_table_lines)
            allure.attach(usp_tt_table_text, name=f"Расхождения USP ↔ TrainingTickets ({usp_tt_count})", attachment_type=allure.attachment_type.TEXT)
            allure.attach(_results_to_html_table(usp_tt_mismatch), name=f"Расхождения USP ↔ TrainingTickets ({usp_tt_count}) — таблица", attachment_type=allure.attachment_type.HTML)
    else:
        print("\nВсе данные консистентны! Расхождений не обнаружено.")
        allure.attach("Все данные консистентны! Расхождений не обнаружено.", name="Результат проверки", attachment_type=allure.attachment_type.TEXT)
    
    print("=" * 190)
    
    # Allure: Прикрепляем полный список всех проверенных записей
    all_results_json = []
    for r in results:
        r_copy = r.copy()
        if r_copy['updated_at'] != 'N/A':
            r_copy['updated_at'] = r_copy['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        if r_copy['created_at'] != 'N/A':
            r_copy['created_at'] = r_copy['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        all_results_json.append(r_copy)
    
    allure.attach(
        json.dumps(all_results_json, indent=2, ensure_ascii=False),
        name=f"Все проверенные записи ({len(results)}) - JSON",
        attachment_type=allure.attachment_type.JSON
    )
    # HTML-таблица для Allure: все колонки отображаются, включая Created at
    allure.attach(_results_to_html_table(results), name=f"Все проверенные записи ({len(results)}) — таблица", attachment_type=allure.attachment_type.HTML)
    
    # Проверка: не должно быть расхождений
    assert failed_count == 0, f"Обнаружено {failed_count} записей с расхождениями данных между таблицами"

