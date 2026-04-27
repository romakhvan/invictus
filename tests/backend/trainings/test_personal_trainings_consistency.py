"""
Тест на консистентность количества персональных тренировок клиента
в разных коллекциях MongoDB.
"""

import pytest
import allure

from src.services.backend_checks.trainings_checks_service import (
    RelativeDateOffset,
    build_personal_trainings_period_label,
    run_personal_trainings_consistency_check,
)
from src.services.reporting.trainings_text_reports import (
    build_personal_trainings_grouped_html_report,
    build_personal_trainings_summary,
    build_personal_trainings_text_table,
)


# ========== КОНФИГУРАЦИЯ ТЕСТА ==========
# Режим 1 — конкретная запись по ID:
# SPECIFIC_USP_ID = '6940ec171415e064049b4254'
SPECIFIC_USP_ID = None

# Режим 2 — фильтр по дате (используется если SPECIFIC_USP_ID = None):
UPDATED_AT_OFFSET = RelativeDateOffset(years=0, months=1, days=0)
CREATED_AT_OFFSET = RelativeDateOffset(years=0, months=1, days=0)
# =========================================


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
    with allure.step("Получение и анализ записей userserviceproducts"):
        result = run_personal_trainings_consistency_check(
            db,
            specific_usp_id=SPECIFIC_USP_ID,
            updated_offset=UPDATED_AT_OFFSET,
            created_offset=CREATED_AT_OFFSET,
        )

    if not result.records:
        pytest.skip("Нет активных записей по заданным фильтрам — нечего проверять")

    period_label = build_personal_trainings_period_label(
        SPECIFIC_USP_ID,
        UPDATED_AT_OFFSET,
        CREATED_AT_OFFSET,
    )
    summary = build_personal_trainings_summary(
        result,
        backend_env=backend_env,
        period_label=period_label,
    )

    allure.attach(
        f"Количество записей: {len(result.records)}",
        name="Записи для проверки",
        attachment_type=allure.attachment_type.TEXT,
    )
    allure.attach(
        summary,
        name="Общая статистика",
        attachment_type=allure.attachment_type.TEXT,
    )

    if result.failed_count > 0:
        if result.regular_failed_records:
            regular_failed_count = len(result.regular_failed_records)
            failed_text = build_personal_trainings_text_table(result.regular_failed_records)
            failed_html = build_personal_trainings_grouped_html_report(
                result.regular_failed_records,
                title=f"Расхождения ({regular_failed_count})",
                result=result,
            )
            allure.attach(
                failed_text,
                name=f"Расхождения ({regular_failed_count})",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                failed_html,
                name=f"Расхождения ({regular_failed_count}) — таблица",
                attachment_type=allure.attachment_type.HTML,
            )
        if result.manual_update_failed_records:
            manual_failed_count = len(result.manual_update_failed_records)
            manual_failed_text = build_personal_trainings_text_table(result.manual_update_failed_records)
            manual_failed_html = build_personal_trainings_grouped_html_report(
                result.manual_update_failed_records,
                title=f"Расхождения после ручного изменения count ({manual_failed_count})",
                result=result,
            )
            allure.attach(
                manual_failed_text,
                name=f"Расхождения после ручного изменения count ({manual_failed_count})",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                manual_failed_html,
                name=f"Расхождения после ручного изменения count ({manual_failed_count}) — таблица",
                attachment_type=allure.attachment_type.HTML,
            )
    else:
        allure.attach(
            "Все данные консистентны! Расхождений не обнаружено.",
            name="Результат проверки",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert result.failed_count == 0, (
        f"Обнаружено {result.failed_count} записей с расхождениями данных между таблицами"
    )
