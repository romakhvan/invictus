"""
Мониторинг создания чеков web-kassa по всем клубам.
Анализирует транзакции и показывает статистику по каждому клубу.
"""

import pytest
import pymongo
import allure
from bson import ObjectId
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict
from src.utils.repository_helpers import get_collection
from src.config.db_config import MONGO_URI_PROD, MONGO_URI_STAGE, DB_NAME


# ========== КОНФИГУРАЦИЯ ОКРУЖЕНИЯ ==========
# Выберите окружение базы данных: 'prod' или 'stage'
ENVIRONMENT = 'prod'  # 'prod' или 'stage'
# ============================================


@pytest.fixture(scope="module")
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


@allure.feature('WebKassa Monitoring')
@allure.story('Receipt Creation Status')
@allure.title('Мониторинг создания чеков WebKassa по клубам')
@allure.description('Анализирует транзакции за последние 7 дней и показывает статистику создания чеков по каждому клубу')
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag('backend', 'webkassa', 'monitoring', 'receipts')
@allure.link("https://docs.google.com/spreadsheets/d/1zE_eUYsGQXvJQOM3FnOc83O2mt5pZT8-SvJwQ2YeCnA/edit?gid=0#gid=0")
def test_webkassa_status_by_clubs(db):
    """
    Анализирует создание чеков по всем клубам за последние 7 дней.
    
    Показывает для каждого клуба:
    - Количество транзакций с успешными чеками
    - Количество транзакций с ошибочными чеками
    - Количество транзакций без чеков
    
    Выводит примеры ошибочных и пустых транзакций.
    """
    with allure.step("Инициализация мониторинга WebKassa"):
        now = datetime.now()
        
        allure.attach(
            f"ENVIRONMENT: {ENVIRONMENT.upper()}\n"
            f"Период анализа: последние 7 дней\n"
            f"Дата запуска: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            name="Конфигурация теста",
            attachment_type=allure.attachment_type.TEXT
        )
        print("\n" + "=" * 110)
        print("МОНИТОРИНГ СОЗДАНИЯ ЧЕКОВ WEB-KASSA ПО КЛУБАМ")
        print("=" * 110)
        
        # Период: последние 7 дней
        days_ago = now - timedelta(days=7)
        
        print(f"\nПериод анализа (последние 7 дней):")
        print(f"  С: {days_ago.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  По: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Шаг 1: Получаем список исключенных клубов
        with allure.step("Получение списка исключенных клубов"):
            excluded_club_ids = [
                ObjectId("68b8060be664a702920a547d"), # Invictus GO Bishkek
                ObjectId("6480df84f493f6015319936d"), # Invictus GO Baitursynov (shop)
                ObjectId("681e3cfc635290fa6d953b10"), # Invictus Fitness Akbulak Riviera
                ObjectId("683574f3f6c08fc5af1eba6b"), # Invictus GO OXY
                ObjectId("6735ee6836765d003669dc72"), # Invictus GO Aport East
                ObjectId("61e6940c1c5b19780b303507"), # Invictus GO Aqsay
                ObjectId("662238db99337806676947b3"), # Invictus GO Shalyapin
                ObjectId("621875f8a81b6009230607e0"), # Invictus Fitness Sadu
                ObjectId("668687f7ab149a00a04341be"), # Invictus GO Austria
                ObjectId("681e3cfc635290fa6d953b10"), # Invictus Fitness Akbulak Riviera
                ObjectId("61ea59bf4360983086b47f3d"), # Invictus Fitness Al-Farabi
                ObjectId("656716180916e102c983dfbe"), # Invictus Girls Nursat
                ObjectId("65144d379928de0202b789f9"), # Invictus Fitness Nursat
                ObjectId("6932d95c3f5fce2f4a89ba9e"), # Invictus GO Arena
                ObjectId("687f521e770a1c01340880c5"), # Invictus Fitness Oral
                ObjectId("690deed030c845004162369c"), # Invictus GO Ualikhanov
                ObjectId("6523f8eb606d2f00fb03b5c6"), # Invictus Fitness Atyrau
                ObjectId("68382801f6c08fc5af1eba9a"), # Invictus GO Raiymbek Batyr
                ObjectId("622127a7097e5c3170553862"), # Invictus Fitness Semey
            ]
            
            # Получаем названия исключенных клубов
            clubs_col = get_collection(db, "clubs")
            excluded_clubs = list(clubs_col.find(
                {"_id": {"$in": excluded_club_ids}},
                {"_id": 1, "name": 1}
            ))
            
            if excluded_clubs:
                print(f"\nИсключенные клубы (не должны создавать чеки):")
                for club in excluded_clubs:
                    print(f"  - {club['name']} (ID: {club['_id']})")
                
                excluded_names = "\n".join([f"- {club['name']}" for club in excluded_clubs])
                allure.attach(
                    f"Всего исключенных клубов: {len(excluded_clubs)}\n\n{excluded_names}",
                    name="Исключенные клубы",
                    # Этот параметр определяет, что вложение в Allure будет отображаться как простой текстовый файл.
                    attachment_type=allure.attachment_type.TEXT
                )
        
        # Шаг 2: Получаем все транзакции за период
        with allure.step("Получение транзакций за последние 7 дней"):
            transactions_col = get_collection(db, "transactions")
            transactions = list(transactions_col.find({
                "status": "success",
                "created_at": {"$gte": days_ago},
                "isDeleted": False,
                "source": {"$in": ["mobile", "website"]},
                "clubId": {"$exists": True, "$ne": None, "$nin": excluded_club_ids}
            }, {
                "_id": 1,
                "clubId": 1,
                "webKassaIds": 1,
                "price": 1,
                "created_at": 1,
                "productType": 1
            }).sort("created_at", -1))
            
            print(f"\nВсего транзакций за период: {len(transactions)}")
            
            allure.attach(
                f"Найдено транзакций: {len(transactions)}",
                name="Количество транзакций",
                attachment_type=allure.attachment_type.TEXT
            )
            
            if not transactions:
                print("Нет транзакций для анализа")
                return
        
        # Шаг 3: Получаем информацию о клубах
        with allure.step("Получение информации о клубах"):
            club_ids = list(set([t["clubId"] for t in transactions]))
            clubs = list(clubs_col.find({"_id": {"$in": club_ids}}, {"_id": 1, "name": 1}))
            club_id_to_name = {club["_id"]: club["name"] for club in clubs}
            
            print(f"Уникальных клубов: {len(club_ids)}")
            
            allure.attach(
                f"Уникальных клубов: {len(club_ids)}",
                name="Количество клубов",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Шаг 4: Собираем все webKassaIds для проверки статусов
        with allure.step("Сбор webKassaIds из транзакций"):
            all_webkassa_ids = []
            transaction_to_webkassa = {}  # transaction_id -> [webkassa_ids]
            
            for trans in transactions:
                trans_id = trans["_id"]
                webkassa_ids = trans.get("webKassaIds", [])
                if webkassa_ids:
                    all_webkassa_ids.extend(webkassa_ids)
                    transaction_to_webkassa[trans_id] = webkassa_ids
            
            print(f"Транзакций с webKassaIds: {len(transaction_to_webkassa)}")
            print(f"Всего webKassaIds: {len(all_webkassa_ids)}")
            
            allure.attach(
                f"Транзакций с чеками: {len(transaction_to_webkassa)}\n"
                f"Всего webKassaIds: {len(all_webkassa_ids)}",
                name="WebKassa статистика",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Шаг 5: Получаем статусы всех чеков и тексты ошибок
        with allure.step("Получение статусов чеков и анализ ошибок"):
            webkassas_col = get_collection(db, "webkassas")
            webkassas = list(webkassas_col.find(
                {"_id": {"$in": all_webkassa_ids}},
                {"_id": 1, "status": 1, "body": 1}
            ))
            
            webkassa_statuses = {wk["_id"]: wk.get("status", "unknown") for wk in webkassas}
            webkassa_errors = {}  # wk_id -> error text
            for wk in webkassas:
                if wk.get("status") == "error":
                    body = wk.get("body", [])
                    if body and len(body) > 0 and isinstance(body[0], dict):
                        error_text = body[0].get("Text", "")
                        if error_text:
                            webkassa_errors[wk["_id"]] = error_text
            
            print(f"Найдено чеков в webkassas: {len(webkassas)}")
            
            allure.attach(
                f"Найдено чеков: {len(webkassas)}\n"
                f"Чеков с ошибками: {len(webkassa_errors)}",
                name="Статусы чеков",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Шаг 6: Группируем транзакции по клубам и статусам
        with allure.step("Группировка транзакций по клубам и статусам"):
            club_stats = defaultdict(lambda: {
                "name": "",
                "total": 0,
                "with_success_receipts": 0,
                "with_error_receipts": 0,
                "without_receipts": 0,
                "success_examples": [],
                "error_examples": [],
                "empty_examples": []
            })
            
            for trans in transactions:
                club_id = trans["clubId"]
                trans_id = trans["_id"]
                
                club_stats[club_id]["name"] = club_id_to_name.get(club_id, f"Unknown ({club_id})")
                club_stats[club_id]["total"] += 1
                
                # Проверяем статус чеков для этой транзакции
                webkassa_ids = trans.get("webKassaIds", [])
                
                if not webkassa_ids:
                    # Транзакция без чеков
                    club_stats[club_id]["without_receipts"] += 1
                    if len(club_stats[club_id]["empty_examples"]) < 5:
                        club_stats[club_id]["empty_examples"].append({
                            "transaction_id": trans_id,
                            "price": trans.get("price", 0),
                            "created_at": trans.get("created_at"),
                            "productType": trans.get("productType")
                        })
                else:
                    # Проверяем статусы чеков
                    has_error = False
                    has_success = False
                    
                    for wk_id in webkassa_ids:
                        status = webkassa_statuses.get(wk_id, "not_found")
                        if status == "success":
                            has_success = True
                        else:
                            has_error = True
                    
                    if has_error:
                        club_stats[club_id]["with_error_receipts"] += 1
                        if len(club_stats[club_id]["error_examples"]) < 5:
                            # Собираем тексты ошибок для каждого чека
                            error_texts = []
                            for wk_id in webkassa_ids:
                                if wk_id in webkassa_errors:
                                    error_texts.append(webkassa_errors[wk_id])
                            
                            club_stats[club_id]["error_examples"].append({
                                "transaction_id": trans_id,
                                "webkassa_ids": webkassa_ids,
                                "statuses": [webkassa_statuses.get(wk_id, "not_found") for wk_id in webkassa_ids],
                                "error_texts": error_texts,
                                "price": trans.get("price", 0),
                                "created_at": trans.get("created_at")
                            })
                    elif has_success:
                        club_stats[club_id]["with_success_receipts"] += 1
        
        # Шаг 7: Сортируем клубы по алфавиту
        with allure.step("Сортировка и разделение клубов на группы"):
            sorted_clubs_alphabetically = sorted(
                club_stats.items(),
                key=lambda x: x[1]["name"]
            )
            
            # Также создаем список клубов по количеству проблем (для примеров)
            sorted_clubs_by_problems = sorted(
                club_stats.items(),
                key=lambda x: (x[1]["with_error_receipts"] + x[1]["without_receipts"], x[1]["total"]),
                reverse=True
            )
            
            # Шаг 8: Разделяем клубы на две группы
            clubs_with_problems = []
            clubs_without_problems = []
            
            for club_id, stats in sorted_clubs_alphabetically:
                errors = stats["with_error_receipts"]
                empty = stats["without_receipts"]
                
                if errors > 0 or empty > 0:
                    clubs_with_problems.append((club_id, stats))
                else:
                    clubs_without_problems.append((club_id, stats))
            
            allure.attach(
                f"Клубов с проблемами: {len(clubs_with_problems)}\n"
                f"Клубов без проблем: {len(clubs_without_problems)}",
                name="Разделение клубов",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Таблица 1: Клубы с проблемами
        print("\n" + "=" * 110)
        print(f"ТАБЛИЦА 1: КЛУБЫ С ПРОБЛЕМАМИ ({len(clubs_with_problems)} клубов)")
        print("=" * 110)
        
        if clubs_with_problems:
            print(f"\n{'№':<4} {'Клуб':<40} {'Всего':<8} {'Успешн.':<10} {'Ошибки':<10} {'Без чека':<10} {'% Проблем':<10}")
            print("=" * 110)
            
            total_problems_trans = 0
            total_problems_success = 0
            total_problems_errors = 0
            total_problems_empty = 0
            
            for idx, (club_id, stats) in enumerate(clubs_with_problems, start=1):
                total = stats["total"]
                success = stats["with_success_receipts"]
                errors = stats["with_error_receipts"]
                empty = stats["without_receipts"]
                
                total_problems_trans += total
                total_problems_success += success
                total_problems_errors += errors
                total_problems_empty += empty
                
                problem_percent = ((errors + empty) / total * 100) if total > 0 else 0
                
                club_name = stats["name"][:38]
                print(f"{idx:<4} {club_name:<40} {total:<8} {success:<10} {errors:<10} {empty:<10} {problem_percent:>8.1f}%")
            
            print("=" * 110)
            print(f"{'':>4} {'ИТОГО':<40} {total_problems_trans:<8} {total_problems_success:<10} {total_problems_errors:<10} {total_problems_empty:<10}")
            print("=" * 110)
        else:
            print("\nВсе клубы работают без проблем!")
        
        # Подсчет данных по клубам без проблем (без вывода таблицы)
        total_perfect_trans = 0
        total_perfect_success = 0
        
        for club_id, stats in clubs_without_problems:
            total_perfect_trans += stats["total"]
            total_perfect_success += stats["with_success_receipts"]
        
        # Общая статистика по всем клубам
        with allure.step("Подсчет общей статистики"):
            total_transactions = total_problems_trans + total_perfect_trans
            total_success = total_problems_success + total_perfect_success
            total_errors = total_problems_errors
            total_empty = total_problems_empty
            
            print("\n" + "=" * 110)
            print("ОБЩАЯ СТАТИСТИКА ПО ВСЕМ КЛУБАМ")
            print("=" * 110)
            print(f"Всего клубов: {len(sorted_clubs_alphabetically)}")
            print(f"  - С проблемами: {len(clubs_with_problems)}")
            print(f"  - Без проблем: {len(clubs_without_problems)}")
            print(f"\nВсего транзакций: {total_transactions}")
            print(f"  - С успешными чеками: {total_success}")
            print(f"  - С ошибочными чеками: {total_errors}")
            print(f"  - Без чеков: {total_empty}")
            print("=" * 110)
            
            # Прикрепляем общую статистику в Allure
            success_rate = (total_success / total_transactions * 100) if total_transactions > 0 else 0
            error_rate = (total_errors / total_transactions * 100) if total_transactions > 0 else 0
            empty_rate = (total_empty / total_transactions * 100) if total_transactions > 0 else 0
            
            allure.attach(
                f"Всего клубов: {len(sorted_clubs_alphabetically)}\n"
                f"  - С проблемами: {len(clubs_with_problems)}\n"
                f"  - Без проблем: {len(clubs_without_problems)}\n\n"
                f"Всего транзакций: {total_transactions}\n"
                f"  - С успешными чеками: {total_success} ({success_rate:.1f}%)\n"
                f"  - С ошибочными чеками: {total_errors} ({error_rate:.1f}%)\n"
                f"  - Без чеков: {total_empty} ({empty_rate:.1f}%)",
                name="Общая статистика",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Шаг 9: Примеры ошибочных транзакций
        print("\n" + "=" * 110)
        print("ПРИМЕРЫ ТРАНЗАКЦИЙ С ОШИБОЧНЫМИ ЧЕКАМИ (до 5 на клуб)")
        print("=" * 110)
        
        error_count = 0
        error_examples_text = []
        
        for club_id, stats in sorted_clubs_by_problems:
            if stats["error_examples"]:
                club_info = f"\nКлуб: {stats['name']}\nВсего ошибочных: {stats['with_error_receipts']}\n"
                print(club_info)
                error_examples_text.append(club_info)
                
                for example in stats["error_examples"]:
                    error_count += 1
                    example_text = [
                        f"  - Transaction: {example['transaction_id']}",
                        f"    WebKassa IDs: {example['webkassa_ids']}",
                        f"    Статусы: {example['statuses']}"
                    ]
                    
                    if example.get('error_texts'):
                        example_text.append("    Тексты ошибок:")
                        for error_text in example['error_texts']:
                            example_text.append(f"      • {error_text}")
                    
                    example_text.append(f"    Сумма: {example['price']} тг")
                    example_text.append(f"    Дата: {example['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    example_output = "\n".join(example_text)
                    print(example_output)
                    error_examples_text.append(example_output)
                    
                if error_count >= 25:  # Не больше 25 примеров всего
                    break
        
        if error_count == 0:
            print("\nНет транзакций с ошибочными чеками")
            error_examples_text.append("Нет транзакций с ошибочными чеками")
        
        # Прикрепляем примеры ошибочных транзакций к отчету
        if error_examples_text:
            allure.attach(
                "\n".join(error_examples_text),
                name="Примеры ошибочных транзакций",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Шаг 10: Примеры транзакций без чеков
        print("\n" + "=" * 110)
        print("ПРИМЕРЫ ТРАНЗАКЦИЙ БЕЗ ЧЕКОВ (до 5 на клуб)")
        print("=" * 110)
        
        empty_count = 0
        empty_examples_text = []
        
        for club_id, stats in sorted_clubs_by_problems:
            if stats["empty_examples"]:
                club_info = f"\nКлуб: {stats['name']}\nВсего без чеков: {stats['without_receipts']}\n"
                print(club_info)
                empty_examples_text.append(club_info)
                
                for example in stats["empty_examples"]:
                    empty_count += 1
                    example_text = [
                        f"  - Transaction: {example['transaction_id']}",
                        f"    Сумма: {example['price']} тг",
                        f"    Тип продукта: {example.get('productType', 'N/A')}",
                        f"    Дата: {example['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"
                    ]
                    
                    example_output = "\n".join(example_text)
                    print(example_output)
                    empty_examples_text.append(example_output)
                    
                if empty_count >= 25:  # Не больше 25 примеров всего
                    break
        
        if empty_count == 0:
            print("\nВсе транзакции имеют чеки")
            empty_examples_text.append("Все транзакции имеют чеки")
        
        # Прикрепляем примеры транзакций без чеков к отчету
        if empty_examples_text:
            allure.attach(
                "\n".join(empty_examples_text),
                name="Примеры транзакций без чеков",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Итоговая проверка
        with allure.step("Итоговая оценка и валидация"):
            print("\n" + "=" * 110)
            print("ИТОГОВАЯ ОЦЕНКА")
            print("=" * 110)
            
            warnings = []
            
            if total_transactions > 0:
                success_rate = (total_success / total_transactions * 100)
                error_rate = (total_errors / total_transactions * 100)
                empty_rate = (total_empty / total_transactions * 100)
                
                print(f"\nУспешных транзакций с чеками: {total_success} ({success_rate:.1f}%)")
                print(f"Транзакций с ошибочными чеками: {total_errors} ({error_rate:.1f}%)")
                print(f"Транзакций без чеков: {total_empty} ({empty_rate:.1f}%)")
                
                # Проверки (мягкие, не фейлят тест)
                if error_rate > 15:
                    warning = f"⚠️ Внимание: высокий процент ошибочных чеков ({error_rate:.1f}%)"
                    print(f"\n{warning}")
                    warnings.append(warning)
                
                if empty_rate > 90:
                    warning = f"⚠️ Внимание: большинство транзакций без чеков ({empty_rate:.1f}%)"
                    print(f"\n{warning}")
                    warnings.append(warning)
                
                if success_rate > 20:
                    print(f"\nХороший показатель успешных чеков: {success_rate:.1f}%")
            
            print("\n" + "=" * 110)
            
            # Прикрепляем предупреждения если есть
            if warnings:
                allure.attach(
                    "\n".join(warnings),
                    name="⚠️ Предупреждения",
                    attachment_type=allure.attachment_type.TEXT
                )

