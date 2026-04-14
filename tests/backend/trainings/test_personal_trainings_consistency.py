"""
Тест на консистентность количества персональных тренировок клиента
в разных коллекциях MongoDB.
"""

import calendar
import pytest
import allure
import json
from datetime import datetime, timedelta
from bson import ObjectId
from src.utils.repository_helpers import get_collection
from src.utils.allure_html import HTML_CSS, html_table


# ========== КОНФИГУРАЦИЯ ТЕСТА ==========
# Режим 1 — конкретная запись по ID:
# SPECIFIC_USP_ID = '6940ec171415e064049b4254'  # например: "663f1a2b4e1d2c0012345678"
SPECIFIC_USP_ID = None  # например: "663f1a2b4e1d2c0012345678"

# Режим 2 — фильтр по дате (используется если SPECIFIC_USP_ID = None):
# Фильтры по updated_at и created_at задаются независимо.
# Если все значения одного фильтра = 0, это поле не фильтруется.
# Можно комбинировать: MONTHS=1, DAYS=15 = "1 месяц и 15 дней назад"

UPDATED_AT_YEARS = 0  # лет назад
UPDATED_AT_MONTHS = 0  # месяцев назад
UPDATED_AT_DAYS = 0  # дней назад

CREATED_AT_YEARS = 0  # лет назад
CREATED_AT_MONTHS = 0  # месяцев назад
CREATED_AT_DAYS = 10  # дней назад
# =========================================

_COL_HEADER = f"{'№':<4} {'USP ID':<26} {'User ID':<26} {'Init':<5} {'Count':<6} {'Tickets':<8} {'Hist':<5} {'Sessions':<9} {'CnlNR':<7} {'Status':<7} {'Updated At':<22} {'Created At':<22}"
_COL_SEP = "=" * 210


def _compute_date_from(years: int, months: int, days: int) -> datetime:
    """Возвращает datetime = сейчас минус (years, months, days)."""
    now = datetime.now()
    target_month = now.month - months
    target_year = now.year - years
    while target_month <= 0:
        target_month += 12
        target_year -= 1
    max_day = calendar.monthrange(target_year, target_month)[1]
    target_day = min(now.day, max_day)
    return datetime(
        target_year, target_month, target_day, now.hour, now.minute, now.second
    ) - timedelta(days=days)


def _fmt_date(dt) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt != "N/A" else "N/A"


def _result_to_line(r: dict) -> str:
    return (
        f"{r['idx']:<4} {r['usp_id']:<26} {r['user_id']:<26} "
        f"{str(r['initial_count']):<5} {str(r['count']):<6} "
        f"{str(r['tickets_count']):<8} {str(r['hist_count']):<5} "
        f"{str(r['sessions_count']):<9} {str(r['cancel_not_restored']):<7} "
        f"{r['status']:<7} {_fmt_date(r['updated_at']):<22} {_fmt_date(r['created_at']):<22}"
    )


def _results_to_text_table(results_list: list) -> str:
    lines = [_COL_HEADER, _COL_SEP] + [_result_to_line(r) for r in results_list]
    return "\n".join(lines)


def _results_to_html_table(results_list: list, title: str = "Результаты") -> str:
    headers = ["№", "USP ID", "User ID", "Init", "Count", "Tickets", "Hist", "Sessions", "CnlNR", "Status", "Updated At", "Created At"]
    rows = [
        [
            str(r["idx"]),
            r["usp_id"],
            r["user_id"],
            str(r["initial_count"]),
            str(r["count"]),
            str(r["tickets_count"]),
            str(r["hist_count"]),
            str(r["sessions_count"]),
            str(r["cancel_not_restored"]),
            r["status"],
            _fmt_date(r["updated_at"]),
            _fmt_date(r["created_at"]),
        ]
        for r in results_list
    ]
    return HTML_CSS + f"<h2>{title}</h2>" + html_table(headers, rows)


def _attach_results(name: str, results_list: list):
    """Прикрепляет TEXT-таблицу и HTML-таблицу к Allure."""
    allure.attach(
        _results_to_text_table(results_list),
        name=name,
        attachment_type=allure.attachment_type.TEXT,
    )
    allure.attach(
        _results_to_html_table(results_list, title=name),
        name=f"{name} — таблица",
        attachment_type=allure.attachment_type.HTML,
    )


def _serialize_results(results_list: list) -> list:
    """Конвертирует datetime-поля в строки для JSON-сериализации."""
    out = []
    for r in results_list:
        r_copy = r.copy()
        r_copy["updated_at"] = _fmt_date(r_copy["updated_at"])
        r_copy["created_at"] = _fmt_date(r_copy["created_at"])
        out.append(r_copy)
    return out


@allure.feature("Backend Data Consistency")
@allure.story("Personal Trainings")
@allure.title("Проверка консистентности персональных тренировок")
@allure.description(
    """
Проверяет консистентность количества персональных тренировок
для записей userserviceproducts.

Сравнивает:
1. count в userserviceproducts
2. количество активных неиспользованных билетов в trainingtickets
3. currentCount в последней записи userserviceproductshistories
"""
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.link("https://invictus.entryx.io/user-service-products/")
@allure.link("https://invictus.entryx.io/users")
def test_personal_trainings_count_consistency(db, backend_env):
    # --- Шаг 1: получение USP-записей ---
    with allure.step("Получение записей userserviceproducts"):
        usp_col = get_collection(db, "userserviceproducts")

        if SPECIFIC_USP_ID:
            record = usp_col.find_one(
                {
                    "_id": ObjectId(SPECIFIC_USP_ID),
                    "isDeleted": False,
                    "type": "SPECIALIST",
                }
            )
            latest_usps = [record] if record else []
        else:
            query: dict = {"isDeleted": False, "isActive": True, "type": "SPECIALIST"}
            use_updated = UPDATED_AT_YEARS or UPDATED_AT_MONTHS or UPDATED_AT_DAYS
            use_created = CREATED_AT_YEARS or CREATED_AT_MONTHS or CREATED_AT_DAYS

            if use_updated:
                updated_from = _compute_date_from(
                    UPDATED_AT_YEARS, UPDATED_AT_MONTHS, UPDATED_AT_DAYS
                )
                query["updated_at"] = {"$gte": updated_from}
            if use_created:
                created_from = _compute_date_from(
                    CREATED_AT_YEARS, CREATED_AT_MONTHS, CREATED_AT_DAYS
                )
                query["created_at"] = {"$gte": created_from}

            sort_field = (
                "updated_at" if use_updated else "created_at" if use_created else "_id"
            )
            latest_usps = list(usp_col.find(query).sort(sort_field, -1))

        allure.attach(
            f"Количество записей: {len(latest_usps)}",
            name="Записи для проверки",
            attachment_type=allure.attachment_type.TEXT,
        )

    if not latest_usps:
        pytest.skip("Нет активных записей по заданным фильтрам — нечего проверять")

    # --- Шаг 2: batch-запросы к связанным коллекциям ---
    with allure.step("Получение связанных данных из БД (batch запросы)"):
        usp_ids = [usp["_id"] for usp in latest_usps]
        tt_col = get_collection(db, "trainingtickets")
        hist_col = get_collection(db, "userserviceproductshistories")

        tickets_counts = {
            doc["_id"]: doc["count"]
            for doc in tt_col.aggregate(
                [
                    {
                        "$match": {
                            "userServiceProduct": {"$in": usp_ids},
                            "isUsed": False,
                            "status": "active",
                            "isDeleted": False,
                        }
                    },
                    {"$group": {"_id": "$userServiceProduct", "count": {"$sum": 1}}},
                ]
            )
        }

        history_counts = {
            doc["_id"]: doc["lastRecord"].get("currentCount", "N/A")
            for doc in hist_col.aggregate(
                [
                    {"$match": {"userServiceProduct": {"$in": usp_ids}}},
                    {"$sort": {"created_at": -1}},
                    {
                        "$group": {
                            "_id": "$userServiceProduct",
                            "lastRecord": {"$first": "$$ROOT"},
                        }
                    },
                ]
            )
        }

        sessions_col = get_collection(db, "trainingsessions")
        sessions_counts = {
            doc["_id"]: doc["count"]
            for doc in sessions_col.aggregate(
                [
                    {"$match": {"participantsList.userServiceProduct": {"$in": usp_ids}}},
                    {"$unwind": "$participantsList"},
                    {"$match": {"participantsList.userServiceProduct": {"$in": usp_ids}}},
                    {"$group": {"_id": "$participantsList.userServiceProduct", "count": {"$sum": 1}}},
                ]
            )
        }

        # Отмены без восстановления: count упал, но сессия не создана — это не баг
        cancel_not_restored_counts = {
            doc["_id"]: doc["count"]
            for doc in hist_col.aggregate(
                [
                    {
                        "$match": {
                            "userServiceProduct": {"$in": usp_ids},
                            "type": "CANCEL_BOOKING",
                            "isRestored": False,
                        }
                    },
                    {"$group": {"_id": "$userServiceProduct", "count": {"$sum": 1}}},
                ]
            )
        }

    # --- Шаг 3: анализ консистентности ---
    with allure.step("Анализ консистентности данных"):
        results = []
        for idx, usp in enumerate(latest_usps, start=1):
            usp_id = usp["_id"]
            initial_count = usp.get("initialCount", "N/A")
            count = usp.get("count", "N/A")
            tickets_count = tickets_counts.get(usp_id, 0)
            hist_count = history_counts.get(usp_id, "N/A")
            sessions_count = sessions_counts.get(usp_id, 0)
            cancel_not_restored = cancel_not_restored_counts.get(usp_id, 0)

            status = "OK"
            if count != "N/A" and tickets_count != count:
                status = "FAIL"
            if count != "N/A" and hist_count != "N/A" and hist_count != count:
                status = "FAIL"
            if hist_count != "N/A" and tickets_count != hist_count:
                status = "FAIL"
            # Использованные = проведённые сессии + отменённые без восстановления
            if initial_count != "N/A" and count != "N/A" and (sessions_count + cancel_not_restored) != (initial_count - count):
                status = "FAIL"

            results.append(
                {
                    "idx": idx,
                    "usp_id": str(usp_id),
                    "user_id": str(usp["user"]),
                    "initial_count": initial_count,
                    "count": count,
                    "tickets_count": tickets_count,
                    "hist_count": hist_count,
                    "sessions_count": sessions_count,
                    "cancel_not_restored": cancel_not_restored,
                    "status": status,
                    "updated_at": usp.get("updated_at", "N/A"),
                    "created_at": usp.get("created_at", "N/A"),
                }
            )

    failed_count = sum(1 for r in results if r["status"] == "FAIL")
    ok_count = sum(1 for r in results if r["status"] == "OK")
    failed_records = [r for r in results if r["status"] == "FAIL"]

    # --- Allure: статистика ---
    if SPECIFIC_USP_ID:
        period_label = f"Конкретная запись: {SPECIFIC_USP_ID}"
    else:
        parts = []
        if UPDATED_AT_YEARS or UPDATED_AT_MONTHS or UPDATED_AT_DAYS:
            parts.append(
                f"updated_at: {UPDATED_AT_YEARS}г {UPDATED_AT_MONTHS}м {UPDATED_AT_DAYS}д назад"
            )
        if CREATED_AT_YEARS or CREATED_AT_MONTHS or CREATED_AT_DAYS:
            parts.append(
                f"created_at: {CREATED_AT_YEARS}г {CREATED_AT_MONTHS}м {CREATED_AT_DAYS}д назад"
            )
        period_label = ", ".join(parts) if parts else "без фильтра по дате"

    allure.attach(
        f"Окружение: {backend_env.upper()}\nПериод: {period_label}\nВсего: {len(results)}  OK: {ok_count}  FAIL: {failed_count}",
        name="Общая статистика",
        attachment_type=allure.attachment_type.TEXT,
    )

    # --- Allure: вложения с расхождениями ---
    if failed_count > 0:
        tt_ids = {
            r["idx"]
            for r in failed_records
            if r["count"] != "N/A" and r["tickets_count"] != r["count"]
        }
        sessions_ids = {
            r["idx"]
            for r in failed_records
            if r["initial_count"] != "N/A" and r["count"] != "N/A"
            and (r["sessions_count"] + r["cancel_not_restored"]) != (r["initial_count"] - r["count"])
        }
        detail_ids = tt_ids | sessions_ids
        detail_mismatch = [r for r in failed_records if r["idx"] in detail_ids]
        if detail_mismatch:
            _attach_results(
                f"Расхождения USP ↔ TrainingTickets / TrainingSessions ({len(detail_mismatch)})",
                detail_mismatch,
            )
    else:
        allure.attach(
            "Все данные консистентны! Расхождений не обнаружено.",
            name="Результат проверки",
            attachment_type=allure.attachment_type.TEXT,
        )

    # --- Allure: полный список ---
    allure.attach(
        json.dumps(_serialize_results(results), indent=2, ensure_ascii=False),
        name=f"Все проверенные записи ({len(results)}) — JSON",
        attachment_type=allure.attachment_type.JSON,
    )
    _attach_results(f"Все проверенные записи ({len(results)})", results)

    assert (
        failed_count == 0
    ), f"Обнаружено {failed_count} записей с расхождениями данных между таблицами"
