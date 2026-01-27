"""
Базовая логика для валидации пуш-уведомлений.

Содержит:
- PushValidationConfig: конфигурация для параметризации валидатора
- validate_push: универсальная функция валидации
- compare_push_recipients: функция сравнения списков получателей
"""
from dataclasses import dataclass
from typing import Callable, Optional
import pytest_check as check
import json
try:
    import allure
    ALLURE_AVAILABLE = True
except ImportError:
    ALLURE_AVAILABLE = False
from src.utils.check_helpers import log_check


@dataclass
class PushValidationConfig:
    """
    Конфигурация для проверки конкретного типа пуш-уведомления.
    
    Используется для параметризации универсальной функции validate_push,
    чтобы избежать дублирования кода между разными типами пушей.
    """
    name: str
    expected_title: str
    expected_text: str
    fetch_function: Callable
    get_recipients_function: Callable
    fetch_kwargs: Optional[dict] = None
    description: str = ""
    
    def __post_init__(self):
        """Инициализация значений по умолчанию"""
        if self.fetch_kwargs is None:
            self.fetch_kwargs = {}


def compare_push_recipients(push_user_ids: list, expected_users: list, entity_name: str = "пользователей") -> bool:
    """
    Универсальная функция сравнения списков получателей пуш-уведомлений.
    
    Сравнивает фактических получателей пуша (из коллекции notifications)
    с ожидаемыми получателями (из БД по бизнес-логике).
    
    Args:
        push_user_ids: список ID пользователей, которые получили пуш (string)
        expected_users: список пользователей из БД (dict с полем _id)
        entity_name: название сущности для отображения в логах
    
    Returns:
        True если списки совпадают, иначе регистрирует ошибки через pytest-check
    """
    print(f"\n{'='*50}")
    print(f"[CHECK] Сравнение составов списков {entity_name}")
    print(f"{'='*50}")
    
    total_push = len(push_user_ids)
    total_db = len(expected_users)
    
    print(f"[PUSH] {entity_name.capitalize()} в пуше: {total_push}")
    print(f"[DB] {entity_name.capitalize()} ожидается (по БД): {total_db}")
    
    # Проверка, что есть хоть кто-то в БД
    check.is_true(
        total_db > 0,
        f"[WARNING] Не найдено {entity_name} по критериям в БД."
    )
    
    # Проверка количества
    check.equal(
        total_db,
        total_push,
        f"[FAIL] Количество {entity_name} в пуше ({total_push}) "
        f"не совпадает с ожидаемым ({total_db})."
    )
    
    # Сравнение составов
    push_set = set(push_user_ids)
    db_set = {str(u["_id"]) for u in expected_users}
    
    missing_in_push = db_set - push_set  # должны были получить, но не получили
    extra_in_push = push_set - db_set    # получили, но не должны были
    matched = db_set & push_set          # совпавшие (правильные)
    
    print(f"\n[OK] Совпавших {entity_name}: {len(matched)}")
    print(f"[WARNING] Не получили пуш (missing): {len(missing_in_push)}")
    print(f"[WARNING] Получили лишние (extra): {len(extra_in_push)}")
    
    # Детализация расхождений
    if not missing_in_push and not extra_in_push:
        print(f"[PASS] Списки {entity_name} полностью совпадают.")
    else:
        if missing_in_push:
            missing_list = list(missing_in_push)
            print(f"\n[WARNING] {len(missing_in_push)} {entity_name} не получили пуш, хотя должны были:")
            print(missing_list[:10])
            
            # Прикрепляем к Allure отчету
            if ALLURE_AVAILABLE:
                allure.attach(
                    json.dumps(missing_list, indent=2, ensure_ascii=False),
                    name=f"Missing IDs ({len(missing_list)} пользователей)",
                    attachment_type=allure.attachment_type.JSON
                )
        
        if extra_in_push:
            extra_list = list(extra_in_push)
            print(f"\n[WARNING] {len(extra_in_push)} {entity_name} получили пуш, хотя не должны были:")
            print(extra_list[:10])
            
            # Прикрепляем к Allure отчету
            if ALLURE_AVAILABLE:
                allure.attach(
                    json.dumps(extra_list, indent=2, ensure_ascii=False),
                    name=f"Extra IDs ({len(extra_list)} пользователей)",
                    attachment_type=allure.attachment_type.JSON
                )
        
        # Прикрепляем общую статистику
        if ALLURE_AVAILABLE:
            stats = {
                "total_in_push": total_push,
                "total_expected": total_db,
                "matched": len(matched),
                "missing": len(missing_in_push),
                "extra": len(extra_in_push)
            }
            allure.attach(
                json.dumps(stats, indent=2, ensure_ascii=False),
                name="Statistics",
                attachment_type=allure.attachment_type.JSON
            )
        
        check.is_true(
            not missing_in_push and not extra_in_push,
            f"[FAIL] Несовпадения в списках {entity_name}: "
            f"{len(missing_in_push)} отсутствуют, {len(extra_in_push)} лишних."
        )
    
    return not missing_in_push and not extra_in_push


def validate_push(db, config: PushValidationConfig, days=7, limit=1):
    """
    Универсальная функция валидации пуш-уведомлений.
    
    Использует конфигурацию (PushValidationConfig) для проверки:
    1. Содержимого пуша (title, text)
    2. Соответствия списка получателей бизнес-логике
    
    Args:
        db: подключение к MongoDB
        config: конфигурация валидации (PushValidationConfig)
        days: количество дней назад для поиска уведомлений
        limit: количество уведомлений для проверки
    
    Returns:
        True если все проверки прошли успешно
    """
    print(f"\n{'='*60}")
    print(f"=== CHECK: {config.name} ===")
    print(f"{'='*60}")
    
    # ---------- 1️⃣ Получаем уведомление из БД ----------
    fetch_result = config.fetch_function(
        db=db,
        days=days,
        limit=limit,
        **config.fetch_kwargs
    )
    
    # Распаковываем результат (user_ids, created_at, title, text)
    user_ids, created_at, title, text = fetch_result
    
    if not created_at:
        print("[WARNING] Уведомление не найдено.")
        check.is_true(False, f"Уведомление '{config.name}' не найдено в БД.")
        return False
    
    print(f"[INFO] Дата отправки пуша: {created_at}")
    print(f"[INFO] Получателей в пуше: {len(user_ids)}")
    
    # ---------- STEP 1: Проверка содержимого ----------
    print(f"\n{'='*50}")
    print("[STEP 1] Проверка содержимого пуша")
    print(f"{'='*50}")
    
    log_check("title", title, config.expected_title)
    log_check("text", text, config.expected_text)
    
    # ---------- STEP 2: Получение ожидаемых получателей ----------
    print(f"\n{'='*50}")
    print("[STEP 2] Проверка соответствия получателей")
    print(f"{'='*50}")
    
    expected_users = config.get_recipients_function(db, created_at)
    
    if not expected_users:
        print(f"[WARNING] Не найдено пользователей, соответствующих критериям для '{config.name}'")
        check.is_true(False, f"Не найдено ожидаемых получателей для '{config.name}'")
        return False
    
    # ---------- STEP 3: Сравнение списков ----------
    compare_push_recipients(user_ids, expected_users, entity_name="пользователей")
    
    return True
