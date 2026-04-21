"""Текстовые report builders для backend-check сценариев payments."""

from __future__ import annotations

from collections import defaultdict

from src.services.backend_checks.payments_checks_service import (
    BonusDeductionConsistencyCheckResult,
    BonusDeductionLimitsCheckResult,
    ForbiddenBonusSpendCheckResult,
    FreezeDaysDuplicateCheckResult,
    InternalErrorTransactionsCheckResult,
    PromoCodeDiscountCheckResult,
    SubscriptionBonusAccrualCheckResult,
    SubscriptionAccessTypeCheckResult,
    VisitBonusAccrualCheckResult,
    VisitBonusCoverageCheckResult,
)
from src.utils.allure_html import HTML_CSS, html_kv, html_table


def build_freeze_days_duplicate_report(result: FreezeDaysDuplicateCheckResult) -> str:
    """Формирует текстовый отчёт по дублирующим FREEZE_DAYS транзакциям."""
    if not result.violations:
        return (
            "Дублей не найдено. "
            f"Проверено {result.unique_subscriptions_count} уникальных подписок."
        )

    lines = [
        (
            f"Абонементов с дублирующей заморозкой: {len(result.violations)} "
            f"из {result.unique_subscriptions_count}"
        ),
        "",
    ]
    for violation in result.violations:
        lines.append(
            f"userSubscription={violation.user_subscription_id} "
            f"({len(violation.transactions)} транзакции)"
        )
        for transaction in violation.transactions:
            created_at = transaction.get("created_at")
            date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "—"
            lines.append(
                "  - "
                f"{date_str} | {transaction['_id']} | "
                f"userId={transaction.get('userId')} | price={transaction.get('price')} тг"
            )
        lines.append("")

    return "\n".join(lines)


def build_forbidden_bonus_spend_report(
    result: ForbiddenBonusSpendCheckResult,
    *,
    max_rows_per_type: int = 10,
) -> str:
    """Формирует текстовый отчёт по списанию бонусов у запрещённых productType."""
    if not result.violation_groups:
        return "Нарушений не найдено. Все запрещённые типы работают корректно."

    lines = [
        f"Нарушений: {result.violations_count} | Типов: {len(result.violation_groups)}",
        "",
    ]
    for group in result.violation_groups:
        lines.append(f"{group.product_type} ({len(group.transactions)})")
        for transaction in group.transactions[:max_rows_per_type]:
            created_at = transaction.get("created_at")
            date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "—"
            price = transaction.get("price", 0)
            spent = transaction.get("bonusesSpent", 0)
            percentage = round(spent / price * 100, 1) if price else "?"
            lines.append(
                "  - "
                f"{date_str} | {transaction['_id']} | "
                f"цена={price} тг | списано={spent} тг ({percentage}%)"
            )
        if len(group.transactions) > max_rows_per_type:
            lines.append(f"  ... и ещё {len(group.transactions) - max_rows_per_type}")
        lines.append("")

    return "\n".join(lines)


def build_bonus_deduction_consistency_report(
    result: BonusDeductionConsistencyCheckResult,
    *,
    max_rows_per_type: int = 10,
) -> str:
    """Формирует текстовый отчёт по транзакциям без PAY-записи бонусной истории."""
    if not result.violations:
        return (
            f"Все {result.transactions_count} транзакций со списанием бонусов "
            "имеют соответствующую PAY-запись."
        )

    violations_by_type = defaultdict(list)
    for violation in result.violations:
        violations_by_type[violation.product_type].append(violation)

    lines = [
        (
            f"Транзакций без PAY-записи: {len(result.violations)} "
            f"из {result.transactions_count}"
        ),
        "",
    ]
    for product_type, product_violations in sorted(
        violations_by_type.items(),
        key=lambda item: -len(item[1]),
    ):
        lines.append(f"{product_type} ({len(product_violations)})")
        for violation in product_violations[:max_rows_per_type]:
            date_str = (
                violation.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if violation.created_at
                else "—"
            )
            lines.append(
                "  - "
                f"{date_str} | {violation.tx_id} | "
                f"bonusesSpent={violation.bonuses_spent} тг | "
                f"PAY-записей для user={violation.user_pay_count}"
            )
        if len(product_violations) > max_rows_per_type:
            lines.append(f"  ... и ещё {len(product_violations) - max_rows_per_type}")
        lines.append("")

    return "\n".join(lines)


def build_bonus_deduction_limits_report(
    result: BonusDeductionLimitsCheckResult,
    *,
    max_rows_per_interval: int = 15,
) -> str:
    """Builds a text report for bonus deduction limit violations by subscription interval."""
    def interval_label(interval: int | None) -> str:
        return {
            365: "Годовой",
            180: "Полугодовой",
            90: "3-месячный",
            30: "Месячный",
            None: "План не найден",
        }.get(interval, f"Неизвестный ({interval} дн.)")

    stats_lines = []
    for stat in sorted(
        result.interval_stats,
        key=lambda item: (-item.transactions_count, item.interval is None, item.interval or 0),
    ):
        limit = "—"
        if stat.interval == 365:
            limit = "≤20%"
        elif stat.interval == 180:
            limit = "≤10%"
        elif stat.interval == 90:
            limit = "≤7%"
        elif stat.interval == 30:
            limit = "≤5%"
        stats_lines.append(
            f"  {interval_label(stat.interval):<20} {limit:<6} "
            f"транзакций: {stat.transactions_count}, нарушений: {stat.violations_count}"
        )
    if result.skipped_unknown_plan_count:
        stats_lines.append(
            f"  Пропущено (неизвестный план/interval): {result.skipped_unknown_plan_count}"
        )

    if not result.violations:
        return "\n".join(
            [
                (
                    f"Нарушений лимитов не найдено. Проверено {result.transactions_count} "
                    f"транзакций по {result.plans_count} планам."
                ),
                "",
                "Статистика по типам:",
                *stats_lines,
            ]
        )

    violations_by_interval = defaultdict(list)
    for violation in result.violations:
        violations_by_interval[violation.interval].append(violation)

    lines = [
        f"Нарушений лимита списания: {len(result.violations)}",
        f"Проверено транзакций: {result.transactions_count}",
        "",
        "Статистика по типам:",
        *stats_lines,
        "",
    ]
    for interval, items in sorted(
        violations_by_interval.items(),
        key=lambda item: (-len(item[1]), item[0]),
    ):
        lines.append(
            f"{interval_label(interval)} (лимит ≤{items[0].limit_pct}%) — {len(items)} нарушений"
        )
        for violation in items[:max_rows_per_interval]:
            date_str = (
                violation.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if violation.created_at
                else "—"
            )
            lines.append(
                f"  - {date_str} | {violation.tx_id} | {violation.plan_name} | "
                f"цена={violation.full_price} тг | списано={violation.bonuses_spent} тг "
                f"({violation.actual_pct}%)"
            )
        if len(items) > max_rows_per_interval:
            lines.append(f"  ... и ещё {len(items) - max_rows_per_interval}")
        lines.append("")

    return "\n".join(lines)


def build_subscription_bonus_accrual_report(
    result: SubscriptionBonusAccrualCheckResult,
    *,
    max_rows_per_group: int = 20,
) -> str:
    """Builds a text report for subscription purchase bonus accrual checks."""
    def interval_label(interval: int | None) -> str:
        return {
            365: "Годовой",
            180: "Полугодовой",
            90: "3-месячный",
            30: "Месячный",
            None: "План не найден",
        }.get(interval, f"Неизвестный ({interval} дн.)")

    total_violations = (
        len(result.missing_bonus)
        + len(result.wrong_amount)
        + len(result.unexpected_bonus)
    )
    stats_lines = [f"Всего транзакций: {result.transactions_count}", ""]
    for stat in result.interval_stats:
        stats_lines.append(f"  {interval_label(stat.interval)}: {stat.transactions_count}")
    stats_lines += [
        "",
        f"Пропущено: {result.skipped_count}",
        f"Нарушений - нет бонуса: {len(result.missing_bonus)}",
        f"Нарушений - неверная сумма: {len(result.wrong_amount)}",
        f"Нарушений - бонус не должен быть начислен: {len(result.unexpected_bonus)}",
    ]

    if total_violations == 0:
        return "\n".join(
            [
                "Нарушений начисления SUBSCRIPTION-бонусов не найдено.",
                "",
                *stats_lines,
            ]
        )

    lines = [*stats_lines, ""]

    if result.missing_bonus:
        lines += [
            f"Годовой/Полугодовой без SUBSCRIPTION-бонуса: {len(result.missing_bonus)}",
            "  дата               | tx_id | план | оплачено | цена плана | ожид. бонус",
            "  " + "-" * 95,
        ]
        for violation in result.missing_bonus[:max_rows_per_group]:
            date_str = (
                violation.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if violation.created_at
                else "—"
            )
            lines.append(
                f"  {date_str} | {violation.tx_id} | {violation.plan_name:<11} | "
                f"{violation.paid_price:>9} тг | {violation.full_price:>9} тг | "
                f"{violation.expected_amount:>10} тг"
            )
        if len(result.missing_bonus) > max_rows_per_group:
            lines.append(f"  ... и ещё {len(result.missing_bonus) - max_rows_per_group}")
        lines.append("")

    if result.wrong_amount:
        lines += [
            f"Неверная сумма SUBSCRIPTION-бонуса: {len(result.wrong_amount)}",
            "  дата               | tx_id | план | цена плана | бонусы сп. | база | ожид. бонус | факт. бонус | разница",
            "  " + "-" * 145,
        ]
        for violation in result.wrong_amount[:max_rows_per_group]:
            date_str = (
                violation.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if violation.created_at
                else "—"
            )
            promo_mark = " +promo" if violation.has_promo else ""
            rate_pct = 10 if violation.interval == 365 else 7 if violation.interval == 180 else "?"
            lines.append(
                f"  {date_str} | {violation.tx_id} | {violation.plan_name:<11} | "
                f"{violation.full_price:>9} тг | {violation.bonuses_spent:>9} тг | "
                f"{violation.base_price:>9} тг{promo_mark:<7} | "
                f"{violation.expected_amount:>8} тг ({rate_pct}%) | "
                f"{violation.actual_amount:>10} тг | {violation.diff:>+7}"
            )
        if len(result.wrong_amount) > max_rows_per_group:
            lines.append(f"  ... и ещё {len(result.wrong_amount) - max_rows_per_group}")
        lines.append("")

    if result.unexpected_bonus:
        lines += [
            f"Бонус начислен, хотя не должен: {len(result.unexpected_bonus)}",
            "  дата               | tx_id | план | интервал | оплачено | факт. бонус",
            "  " + "-" * 100,
        ]
        for violation in result.unexpected_bonus[:max_rows_per_group]:
            date_str = (
                violation.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if violation.created_at
                else "—"
            )
            lines.append(
                f"  {date_str} | {violation.tx_id} | {violation.plan_name:<11} | "
                f"{violation.interval:>5} дн. | {violation.paid_price:>9} тг | "
                f"{violation.bonus_amount:>10} тг"
            )
        if len(result.unexpected_bonus) > max_rows_per_group:
            lines.append(f"  ... и ещё {len(result.unexpected_bonus) - max_rows_per_group}")

    return "\n".join(lines)


def build_visit_bonus_accrual_report(result: VisitBonusAccrualCheckResult) -> str:
    """Builds a text report for VISIT bonus accrual consistency checks."""
    lines = [
        f"Проверено VISIT-бонусов: {result.bonus_records_count}",
        f"Найдено валидных входов: {result.access_entries_count}",
        f"Дублей бонусов за день: {len(result.duplicate_days)}",
        f"Бонусов без посещения: {len(result.missing_visit_bonuses)}",
    ]

    if not result.duplicate_days and not result.missing_visit_bonuses:
        return "\n".join(lines)

    if result.duplicate_days:
        lines += ["", f"Дубли VISIT-бонусов за один день: {len(result.duplicate_days)}"]
        for violation in result.duplicate_days[:20]:
            lines.append(
                f"  user={violation.user_id} date={violation.date} bonus_ids={violation.bonus_ids}"
            )

    if result.missing_visit_bonuses:
        lines += ["", f"VISIT-бонусы без посещения: {len(result.missing_visit_bonuses)}"]
        for violation in result.missing_visit_bonuses[:20]:
            lines.append(
                f"  bonus_id={violation.bonus_id} user={violation.user_id} "
                f"amount={violation.amount} time={violation.time}"
            )

    return "\n".join(lines)


def build_visit_bonus_coverage_report(
    result: VisitBonusCoverageCheckResult,
    *,
    max_users: int = 30,
) -> str:
    """Builds a text report for visit days missing VISIT bonuses."""
    if not result.violations:
        return "\n".join(
            [
                f"Пользователей в выборке: {result.sample_users_count}",
                f"Дней с VISIT-бонусами: {result.bonus_days_count}",
                f"Дней с посещениями: {result.visit_days_count}",
                "Нарушений не найдено.",
            ]
        )

    by_user: dict[str, list[Any]] = defaultdict(list)
    for violation in result.violations:
        by_user[violation.user_id].append(violation.date)

    lines = [
        f"Дней посещений без VISIT-бонуса: {len(result.violations)}",
        f"Затронуто пользователей: {len(by_user)}",
        "",
    ]
    for user_id, dates in sorted(by_user.items(), key=lambda item: -len(item[1]))[:max_users]:
        dates_str = ", ".join(str(date) for date in sorted(dates))
        lines.append(f"  user={user_id} пропущено дней: {len(dates)}")
        lines.append(f"    {dates_str}")

    return "\n".join(lines)


def build_promo_code_discount_report(
    result: PromoCodeDiscountCheckResult,
    *,
    max_rows_per_kind: int = 10,
) -> str:
    """Формирует текстовый отчёт по нарушениям применения промокодов."""
    if not result.violations:
        return f"Все {result.transactions_count} транзакций прошли проверку промокода."

    violations_by_kind: dict[str, list] = {}
    for violation in result.violations:
        violations_by_kind.setdefault(violation.kind, []).append(violation)

    lines = [
        f"Нарушений промокодов: {len(result.violations)} из {result.transactions_count} транзакций",
        "",
    ]
    for kind in ("A", "B", "C", "D"):
        kind_violations = violations_by_kind.get(kind, [])
        if not kind_violations:
            continue
        lines.append(f"[{kind}] {kind_violations[0].label} ({len(kind_violations)})")
        for violation in kind_violations[:max_rows_per_kind]:
            date_str = violation.date.strftime("%Y-%m-%d %H:%M:%S") if violation.date else "—"
            lines.append(f"  - {date_str} | {violation.tx_id} | {violation.detail}")
        if len(kind_violations) > max_rows_per_kind:
            lines.append(f"  ... и ещё {len(kind_violations) - max_rows_per_kind}")
        lines.append("")

    return "\n".join(lines)


def build_internal_error_report(
    result: InternalErrorTransactionsCheckResult,
    *,
    max_rows_per_club: int = 10,
) -> str:
    """Формирует текстовый отчёт по internalError транзакциям."""
    if not result.club_groups:
        return "Транзакций со статусом internalError не найдено. Всё в порядке."

    lines = [
        f"Всего транзакций с internalError: {result.error_transactions_count}",
        f"Затронуто клубов: {result.affected_clubs_count}",
        "",
    ]
    for club_group in result.club_groups:
        lines.append(f"{club_group.club_name} ({len(club_group.transactions)})")
        for transaction in club_group.transactions[:max_rows_per_club]:
            created_at = transaction.get("created_at")
            date_str = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else "—"
            price = transaction.get("price", 0)
            price_fmt = f"{int(price):,}".replace(",", " ") + " тг"
            product_type = transaction.get("productType") or "—"
            source = transaction.get("source") or "—"
            reason = transaction.get("reason") or "—"
            lines.append(
                f"  - {date_str} | {transaction['_id']} | {price_fmt} | {product_type} | {source} | {reason}"
            )
        if len(club_group.transactions) > max_rows_per_club:
            lines.append(f"  ... и ещё {len(club_group.transactions) - max_rows_per_club}")
        lines.append("")

    return "\n".join(lines)


def build_internal_error_product_breakdown(result: InternalErrorTransactionsCheckResult) -> str:
    """Формирует краткую разбивку internalError транзакций по productType."""
    if not result.product_type_counts:
        return "Нет данных по productType."
    return "\n".join(
        f"{product_type}: {count}"
        for product_type, count in result.product_type_counts.items()
    )


def _pct(part: int, total: int) -> str:
    return f"{part / total * 100:.1f}%" if total else "—"


def _viol_css_val(value: int, total: int) -> str:
    if total == 0:
        return f'<span class="gray">{value}</span>'
    return f'<span class="red">{value}</span>' if value else f'<span class="green">{value}</span>'


def _sample_entries(entries: list) -> list:
    if len(entries) <= 4:
        return entries
    return [entries[-1], entries[-2], entries[0], entries[1]]


def _interval_label(interval: int | None) -> str:
    return {
        365: "Годовой",
        180: "Полугодовой",
        90: "3-месячный",
        30: "Месячный",
    }.get(interval, f"{interval} дн." if interval else "—")


def build_subscription_access_type_reports(result: SubscriptionAccessTypeCheckResult) -> dict[str, str]:
    """Формирует набор текстовых и HTML-отчётов для accessType-проверки."""
    def club_label(club_id) -> str:
        name = result.club_name_map.get(club_id, "неизвестный клуб") if club_id else "неизвестный клуб"
        return f"{name} ({club_id})" if club_id else name

    def plan_label(plan_id) -> str:
        plan = result.plan_map.get(plan_id)
        if not plan:
            return f"неизвестный план ({plan_id})"
        return f"{plan.get('name', '—')} ({plan_id})"

    summary_pairs = [
        ("Total entries checked", result.entries_count),
        ("Entries in window", result.entries_in_window_count),
        ("Skipped (outside window)", result.outside_window_count),
        ("Plan without clubId", len(result.no_clubid_entries)),
        ("Violations", len(result.violations)),
        ("Error rate", _pct(len(result.violations), result.entries_in_window_count)),
    ]
    summary_text = "\n".join(f"{key + ':':<28} {value}" for key, value in summary_pairs)
    summary_html = HTML_CSS + "<h2>Summary</h2>" + html_kv(summary_pairs)

    club_rows_sorted = sorted(result.by_club.items(), key=lambda item: -item[1]["violations"])
    club_text_lines = [
        f"{'Клуб':<60} {'Входов':>8} {'Нарушений':>10} {'%':>8}",
        "-" * 90,
    ]
    for club_id, stat in club_rows_sorted:
        club_text_lines.append(
            f"{club_label(club_id):<60} {stat['total']:>8} "
            f"{stat['violations']:>10} {_pct(stat['violations'], stat['total']):>8}"
        )
    by_club_text = "\n".join(club_text_lines)
    by_club_html_rows = [
        (
            club_label(club_id),
            stat["total"],
            _viol_css_val(stat["violations"], stat["total"]),
            _pct(stat["violations"], stat["total"]),
        )
        for club_id, stat in club_rows_sorted
    ]
    by_club_html = HTML_CSS + "<h2>By Club</h2>" + html_table(
        ["Клуб", "Входов", "Нарушений", "%"],
        by_club_html_rows,
        right_cols=(1, 2, 3),
    )

    plan_rows_sorted = sorted(result.by_plan.items(), key=lambda item: -item[1]["violations"])
    plan_text_lines = [
        f"{'План':<80} {'Входов':>8} {'Нарушений':>10} {'%':>8}",
        "-" * 110,
    ]
    for plan_id, stat in plan_rows_sorted:
        plan_text_lines.append(
            f"{plan_label(plan_id):<80} {stat['total']:>8} "
            f"{stat['violations']:>10} {_pct(stat['violations'], stat['total']):>8}"
        )
    by_plan_text = "\n".join(plan_text_lines)
    by_plan_html_rows = [
        (
            plan_label(plan_id),
            stat["total"],
            _viol_css_val(stat["violations"], stat["total"]),
            _pct(stat["violations"], stat["total"]),
        )
        for plan_id, stat in plan_rows_sorted
    ]
    by_plan_html = HTML_CSS + "<h2>By Subscription Plan</h2>" + html_table(
        ["Абонемент", "Входов", "Нарушений", "%"],
        by_plan_html_rows,
        right_cols=(1, 2, 3),
    )

    violations_text = ""
    violations_html = ""
    if result.violations:
        by_club_plan: dict = {}
        for violation in result.violations:
            by_club_plan.setdefault(violation.club_id, {}).setdefault(violation.plan_id, []).append(violation)

        detail_lines = []
        html_blocks = [HTML_CSS, "<h2>Нарушения по клубам</h2>"]
        for club_id, plans_in_club in sorted(
            by_club_plan.items(),
            key=lambda item: -sum(len(entries) for entries in item[1].values()),
        ):
            club_total = sum(len(entries) for entries in plans_in_club.values())
            detail_lines += [f"Клуб: {club_label(club_id)}", f"Нарушений: {club_total}"]
            html_blocks.append(
                f'<div class="club-block"><div class="club-head">'
                f'Клуб: {club_label(club_id)}'
                f'<span class="club-sub"> — Нарушений: {club_total}</span></div>'
            )
            for plan_id, club_entries in sorted(plans_in_club.items(), key=lambda item: -len(item[1])):
                detail_lines += ["", f"  Абонемент: {plan_label(plan_id)}", f"  Нарушений: {len(club_entries)}"]
                for entry in _sample_entries(club_entries):
                    detail_lines.append(
                        f"    - {entry.time.strftime('%Y-%m-%d %H:%M:%S')} | entry_id={entry.entry_id} | user={entry.user_id}"
                    )
                entry_rows = [
                    (entry.time.strftime("%Y-%m-%d %H:%M:%S"), entry.entry_id, entry.user_id)
                    for entry in _sample_entries(club_entries)
                ]
                html_blocks.append(
                    f'<div class="plan-block"><div class="plan-head">'
                    f'Абонемент: {plan_label(plan_id)} — Нарушений: {len(club_entries)}</div>'
                    + html_table(["Время входа", "entry_id", "user_id"], entry_rows)
                    + "</div>"
                )
            detail_lines += ["", "-" * 50, ""]
            html_blocks.append("</div>")

        violations_text = "\n".join(detail_lines)
        violations_html = "".join(html_blocks)

    no_clubid_text = ""
    no_clubid_html = ""
    if result.no_clubid_entries:
        by_club_plan_nc: dict = {}
        for entry in result.no_clubid_entries:
            by_club_plan_nc.setdefault(entry.club_id, {}).setdefault(entry.plan_id, []).append(entry)

        nc_lines = []
        nc_html = [HTML_CSS, "<h2>Абонементы без clubId</h2>"]
        for club_id, plans_in_club in sorted(
            by_club_plan_nc.items(),
            key=lambda item: -sum(len(entries) for entries in item[1].values()),
        ):
            club_total = sum(len(entries) for entries in plans_in_club.values())
            nc_lines += [f"Клуб: {club_label(club_id)}", f"Входов: {club_total}"]
            nc_html.append(
                f'<div class="club-block"><div class="club-head">'
                f'Клуб: {club_label(club_id)}'
                f'<span class="club-sub"> — Входов: {club_total}</span></div>'
            )
            for plan_id, club_entries in sorted(plans_in_club.items(), key=lambda item: -len(item[1])):
                plan = result.plan_map.get(plan_id, {})
                nc_lines += [
                    "",
                    f"  Абонемент: {plan_label(plan_id)}",
                    f"  Тип: {_interval_label(plan.get('interval'))}",
                    f"  Входов: {len(club_entries)}",
                ]
                for entry in _sample_entries(club_entries):
                    nc_lines.append(
                        f"    - {entry.time.strftime('%Y-%m-%d %H:%M:%S')} | entry_id={entry.entry_id} | user={entry.user_id}"
                    )
                entry_rows = [
                    (entry.time.strftime("%Y-%m-%d %H:%M:%S"), entry.entry_id, entry.user_id)
                    for entry in _sample_entries(club_entries)
                ]
                nc_html.append(
                    f'<div class="plan-block"><div class="plan-head">'
                    f'Абонемент: {plan_label(plan_id)}'
                    f' — Тип: {_interval_label(plan.get("interval"))}'
                    f' — Входов: {len(club_entries)}</div>'
                    + html_table(["Время входа", "entry_id", "user_id"], entry_rows)
                    + "</div>"
                )
            nc_lines += ["", "-" * 50, ""]
            nc_html.append("</div>")

        no_clubid_text = "\n".join(nc_lines)
        no_clubid_html = "".join(nc_html)

    return {
        "summary_text": summary_text,
        "summary_html": summary_html,
        "by_club_text": by_club_text,
        "by_club_html": by_club_html,
        "by_plan_text": by_plan_text,
        "by_plan_html": by_plan_html,
        "violations_text": violations_text,
        "violations_html": violations_html,
        "no_clubid_text": no_clubid_text,
        "no_clubid_html": no_clubid_html,
    }
