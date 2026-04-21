import allure
import pytest

from src.validators.push_notifications.guest_visit_discount_push_validator import (
    GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION,
    GUEST_VISIT_DISCOUNT_PUSH_TEXT,
    GUEST_VISIT_DISCOUNT_PUSH_TITLE,
    check_guest_visit_discount_push,
    get_guest_visit_discount_push_doc_stats,
    get_guest_visit_discount_push_docs,
)


def _build_language_stats_text(language_stats) -> str:
    if not language_stats:
        return "-"

    return ", ".join(
        f"{language}={stats['docs']}"
        for language, stats in sorted(language_stats.items())
    )


def _build_summary_text(
    period_days,
    docs_count,
    matching_docs_count,
    matching_language_stats,
    created_at,
    recipients_count,
    actual_title,
    actual_text,
) -> str:
    return "\n".join(
        [
            f"Period: last {period_days} days",
            f"Matching docs in period: {matching_docs_count}",
            f"Matching docs by language: {_build_language_stats_text(matching_language_stats)}",
            f"Notification docs checked in validation: {docs_count}",
            f"Push sent at: {created_at or '-'}",
            f"Push description: {GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION} [any language]",
            f"Expected title: {' | '.join(GUEST_VISIT_DISCOUNT_PUSH_TITLE)}",
            f"Actual title: {actual_title or '-'}",
            f"Expected text: {' | '.join(GUEST_VISIT_DISCOUNT_PUSH_TEXT)}",
            f"Actual text: {actual_text or '-'}",
            f"Recipients in push: {recipients_count}",
            "Expected rule: each notification recipient had accesscontrols.type=enter with accessType=visits about 30 minutes earlier.",
        ]
    )


@allure.feature("Push Notifications")
@allure.story("Guest Visit Discount Push")
@allure.title('Проверка пуша "Скидка в день гостевого визита"')
@allure.description(
    "Проверяет push по description 'скидка в день гостевого визита' для всех языковых вариантов и получателей, "
    "которые зашли в клуб по гостевому визиту примерно за 30 минут до отправки. "
    "Тест делает skip, если за период period_days не найдено ни одного такого notification. "
    "Тест падает, если у найденного notification отличается description, title или text, "
    "либо если для любого user из toUsers не найден успешный вход в accesscontrols "
    "с type=enter, accessType=visits, без err и со временем 30 минут ± 60 секунд "
    "до created_at notification."
)
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "notifications", "guest-visit", "discount", "mongodb")
def test_guest_visit_discount_push(db, period_days):
    with allure.step("Определить push за период и приложить summary"):
        docs = get_guest_visit_discount_push_docs(db=db, days=period_days)
        doc_stats = get_guest_visit_discount_push_doc_stats(db=db, days=period_days)
        if not docs:
            pytest.skip(
                f"За последние {period_days} дней push "
                f"'{GUEST_VISIT_DISCOUNT_PUSH_DESCRIPTION}' не найден"
            )
        latest_doc = docs[0]
        recipients_count = sum(len(doc.get("toUsers") or []) for doc in docs)
        created_at = latest_doc.get("created_at")
        actual_title = latest_doc.get("title")
        actual_text = latest_doc.get("text")
        allure.dynamic.parameter("Push sent at", str(created_at) if created_at else "-")
        allure.dynamic.parameter("Matching docs in period", doc_stats["docs"])
        allure.dynamic.parameter("Notification docs checked", len(docs))
        allure.dynamic.parameter("Push recipients", recipients_count)
        allure.attach(
            _build_summary_text(
                period_days,
                len(docs),
                doc_stats["docs"],
                doc_stats["languages"],
                created_at,
                recipients_count,
                actual_title,
                actual_text,
            ),
            name="Summary",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Проверить содержимое push и соответствие получателей гостевому визиту"):
        result = check_guest_visit_discount_push(db, days=period_days)
        assert result, "Push 'Скидка в день гостевого визита' не прошёл проверку"
