"""
Проверка корректности поля accessType при входе клиента по абонементу.

Бизнес-правило: вход по нерекуррентному абонементу (subscriptions.isRecurrent=false)
должен фиксироваться с accesscontrols.accessType='subscription'.
Подписки (isRecurrent=true) этим тестом не охватываются.
"""
import pytest
import allure
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection
from src.utils.allure_html import HTML_CSS as _HTML_CSS, html_table as _html_table, html_kv as _html_kv

SAMPLE_SIZE = 300  # кол-во абонементов для выборки


def _pct(part, total):
    return f"{part / total * 100:.1f}%" if total else "—"


def _viol_css_val(val, total):
    """Окрашивает значение нарушений: красный если > 0, серый если 0."""
    if total == 0:
        return f'<span class="gray">{val}</span>'
    return f'<span class="red">{val}</span>' if val else f'<span class="green">{val}</span>'


def _sample_entries(entries):
    """Возвращает последние 2 и первые 2 записи в порядке: последний, предпоследний, первый, второй."""
    if len(entries) <= 4:
        return entries
    return [entries[-1], entries[-2], entries[0], entries[1]]


@pytest.mark.backend
@allure.feature("Access Control")
@allure.story("Subscription entry validation")
@allure.title("При входе по абонементу accesscontrols.accessType=subscription")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "accesscontrols", "subscription", "access")
def test_subscription_entry_access_type(db, period_days):
    """
    Для выборки пользователей с активными нерекуррентными абонементами
    проверяет, что все их входы в клуб (type=enter, без err, без staff)
    в период действия абонемента имеют accessType='subscription'.
    """
    subscriptions_col = get_collection(db, "subscriptions")
    usersubs_col = get_collection(db, "usersubscriptions")
    access_col = get_collection(db, "accesscontrols")
    clubs_col = get_collection(db, "clubs")
    now = datetime.now()
    since = now - timedelta(days=period_days)

    # 1. Нерекуррентные планы абонементов (ID + название + интервал)
    with allure.step("Загрузить нерекуррентные планы абонементов"):
        plans = list(subscriptions_col.find(
            {"isRecurrent": {"$ne": True}, "isDeleted": False},
            {"_id": 1, "name": 1, "interval": 1, "clubId": 1},
        ))

    if not plans:
        pytest.skip("Нет нерекуррентных планов абонементов в базе")

    plan_map = {p["_id"]: p for p in plans}
    allure.dynamic.parameter("Нерекуррентных планов", len(plans))

    # 2. Пользовательские абонементы, активные в анализируемом периоде
    with allure.step(f"Найти абонементы, активные в последние {period_days} дней"):
        user_subs = list(usersubs_col.find(
            {
                "subscriptionId": {"$in": list(plan_map.keys())},
                "isDeleted": False,
                "startDate": {"$lte": now},
                "$or": [
                    {"endDate": {"$gte": since}},
                    {"endDate": None},
                ],
            },
            {"user": 1, "startDate": 1, "endDate": 1, "subscriptionId": 1},
        ).limit(SAMPLE_SIZE))

    if not user_subs:
        pytest.skip(f"Нет активных абонементов за последние {period_days} дней")

    allure.dynamic.parameter("Абонементов в выборке", len(user_subs))

    # Индекс: user_id → список (startDate, endDate, subscriptionId)
    user_windows = defaultdict(list)
    for s in user_subs:
        user_windows[s["user"]].append((
            s["startDate"],
            s.get("endDate"),
            s.get("subscriptionId"),
        ))

    user_ids = list(user_windows.keys())
    allure.dynamic.parameter("Пользователей в выборке", len(user_ids))

    # 3. Bulk-запрос входов за период (без ошибочных, без staff)
    with allure.step("Загрузить входы в клуб для пользователей-абонентов (без err, без staff)"):
        entries = list(access_col.find(
            {
                "user": {"$in": user_ids},
                "type": "enter",
                "err": {"$exists": False},
                "accessType": {"$ne": "staff"},
                "time": {"$gte": since, "$lte": now},
            },
            {"_id": 1, "user": 1, "time": 1, "accessType": 1, "club": 1},
        ))

    if not entries:
        pytest.skip("Нет входов в клуб у абонентов за период")

    allure.dynamic.parameter("Входов в выборке", len(entries))

    # 4. Проверка + сбор статистики по клубам и планам
    def find_window(user_id, entry_time, entry_club):
        """
        Возвращает (subscriptionId, club_matched) для первого окна, совпадающего по времени.
        club_matched=True  — план совпадает по клубу (полное совпадение).
        club_matched=False — план без clubId (клуб не указан в плане).
        Возвращает None, если ни одно окно не совпадает по времени или клубу не совпадает.
        """
        no_clubid_match = None
        for start, end, sub_id in user_windows.get(user_id, []):
            if entry_time >= start and (end is None or entry_time <= end):
                plan_club = plan_map.get(sub_id, {}).get("clubId")
                if plan_club == entry_club:
                    return sub_id, True
                if plan_club is None and no_clubid_match is None:
                    no_clubid_match = sub_id  # запоминаем, но продолжаем искать полное совпадение
        if no_clubid_match is not None:
            return no_clubid_match, False
        return None

    with allure.step("Проверить accessType и собрать статистику по клубам и планам"):
        violations = []
        no_clubid_entries = []  # входы с планом без clubId
        outside_window = 0

        # Счётчики: {id: {"total": N, "violations": N}}
        by_club = defaultdict(lambda: {"total": 0, "violations": 0})
        by_plan = defaultdict(lambda: {"total": 0, "violations": 0})

        for e in entries:
            result = find_window(e["user"], e["time"], e.get("club"))
            if result is None:
                outside_window += 1
                continue

            matched_plan_id, club_matched = result

            if not club_matched:
                no_clubid_entries.append({**e, "_plan_id": matched_plan_id})
                continue

            club_id = e.get("club")
            by_club[club_id]["total"] += 1
            by_plan[matched_plan_id]["total"] += 1

            if e.get("accessType") != "subscription":
                violations.append({**e, "_plan_id": matched_plan_id})
                by_club[club_id]["violations"] += 1
                by_plan[matched_plan_id]["violations"] += 1

    total_checked = len(entries)
    total_in_window = total_checked - outside_window

    # 5. Загрузка имён клубов для отчёта (включая клубы из no_clubid_entries)
    club_ids_used = list({
        cid for cid in list(by_club.keys()) + [e.get("club") for e in no_clubid_entries]
        if cid is not None
    })
    club_name_map = {}
    if club_ids_used:
        clubs_data = list(clubs_col.find(
            {"_id": {"$in": club_ids_used}},
            {"_id": 1, "name": 1},
        ))
        club_name_map = {c["_id"]: c.get("name", str(c["_id"])) for c in clubs_data}

    def club_label(club_id):
        name = club_name_map.get(club_id, "неизвестный клуб") if club_id else "неизвестный клуб"
        return f"{name} ({club_id})" if club_id else name

    def plan_label(plan_id):
        p = plan_map.get(plan_id)
        if not p:
            return f"неизвестный план ({plan_id})"
        return f"{p.get('name', '—')} ({plan_id})"

    # 6. Формирование диагностического отчёта
    with allure.step("Сформировать диагностический отчёт"):

        # Предвычисляем ширину колонки названий для выравнивания текстовых таблиц
        club_col_w = max((len(club_label(cid)) for cid in by_club), default=40) + 2
        plan_col_w = max((len(plan_label(pid)) for pid in by_plan), default=45) + 2

        # ── Summary (текст + HTML) ──────────────────────────────────────────
        summary_pairs = [
            ("Total entries checked",      total_checked),
            ("Entries in window",          total_in_window),
            ("Skipped (outside window)",   outside_window),
            ("Plan without clubId",        len(no_clubid_entries)),
            ("Violations",                 len(violations)),
            ("Error rate",                 _pct(len(violations), total_in_window)),
        ]
        summary_text = "\n".join(f"{k + ':':<28} {v}" for k, v in summary_pairs)
        print("\n=== SUMMARY ===\n" + summary_text)
        allure.attach(summary_text, name="Summary", attachment_type=allure.attachment_type.TEXT)
        allure.attach(
            _HTML_CSS + "<h2>Summary</h2>" + _html_kv(summary_pairs),
            name="Summary (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )

        # ── By Club (текст + HTML) ──────────────────────────────────────────
        club_rows_sorted = sorted(by_club.items(), key=lambda x: -x[1]["violations"])

        club_text_lines = [
            f"{'Клуб':<{club_col_w}} {'Входов':>8} {'Нарушений':>10} {'%':>8}",
            "-" * (club_col_w + 30),
        ]
        for cid, stat in club_rows_sorted:
            club_text_lines.append(
                f"{club_label(cid):<{club_col_w}} {stat['total']:>8} "
                f"{stat['violations']:>10} {_pct(stat['violations'], stat['total']):>8}"
            )
        club_text = "\n".join(club_text_lines)
        print("\n=== BY CLUB ===\n" + club_text)
        allure.attach(club_text, name="By Club", attachment_type=allure.attachment_type.TEXT)

        club_html_rows = [
            (club_label(cid), stat["total"],
             _viol_css_val(stat["violations"], stat["total"]),
             _pct(stat["violations"], stat["total"]))
            for cid, stat in club_rows_sorted
        ]
        allure.attach(
            _HTML_CSS + "<h2>By Club</h2>" + _html_table(
                ["Клуб", "Входов", "Нарушений", "%"],
                club_html_rows,
                right_cols=(1, 2, 3),
            ),
            name="By Club (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )

        # ── By Subscription Plan (текст + HTML) ────────────────────────────
        plan_rows_sorted = sorted(by_plan.items(), key=lambda x: -x[1]["violations"])

        plan_text_lines = [
            f"{'План':<{plan_col_w}} {'Входов':>8} {'Нарушений':>10} {'%':>8}",
            "-" * (plan_col_w + 30),
        ]
        for pid, stat in plan_rows_sorted:
            plan_text_lines.append(
                f"{plan_label(pid):<{plan_col_w}} {stat['total']:>8} "
                f"{stat['violations']:>10} {_pct(stat['violations'], stat['total']):>8}"
            )
        plan_text = "\n".join(plan_text_lines)
        print("\n=== BY SUBSCRIPTION PLAN ===\n" + plan_text)
        allure.attach(plan_text, name="By Subscription Plan", attachment_type=allure.attachment_type.TEXT)

        plan_html_rows = [
            (plan_label(pid), stat["total"],
             _viol_css_val(stat["violations"], stat["total"]),
             _pct(stat["violations"], stat["total"]))
            for pid, stat in plan_rows_sorted
        ]
        allure.attach(
            _HTML_CSS + "<h2>By Subscription Plan</h2>" + _html_table(
                ["Абонемент", "Входов", "Нарушений", "%"],
                plan_html_rows,
                right_cols=(1, 2, 3),
            ),
            name="By Subscription Plan (HTML)",
            attachment_type=allure.attachment_type.HTML,
        )

        # ── Нарушения по клубам (текст + HTML) ─────────────────────────────
        if violations:
            by_club_plan = defaultdict(lambda: defaultdict(list))
            for v in violations:
                by_club_plan[v.get("club")][v["_plan_id"]].append(v)

            # --- текст ---
            detail_lines = []
            for club_id, plans_in_club in sorted(
                by_club_plan.items(), key=lambda x: -sum(len(e) for e in x[1].values())
            ):
                club_total = sum(len(e) for e in plans_in_club.values())
                detail_lines += [f"Клуб: {club_label(club_id)}", f"Нарушений: {club_total}"]
                for plan_id, club_entries in sorted(plans_in_club.items(), key=lambda x: -len(x[1])):
                    detail_lines += ["", f"  Абонемент: {plan_label(plan_id)}", f"  Нарушений: {len(club_entries)}"]
                    for v in _sample_entries(club_entries):
                        detail_lines.append(
                            f"    - {v['time'].strftime('%Y-%m-%d %H:%M:%S')} "
                            f"| entry_id={v['_id']} | user={v['user']}"
                        )
                detail_lines += ["", "-" * 50, ""]
            detail_text = "\n".join(detail_lines)
            print("\n=== НАРУШЕНИЯ ПО КЛУБАМ ===\n" + detail_text)
            allure.attach(detail_text, name="Нарушения по клубам", attachment_type=allure.attachment_type.TEXT)

            # --- HTML ---
            html_blocks = [_HTML_CSS, "<h2>Нарушения по клубам</h2>"]
            for club_id, plans_in_club in sorted(
                by_club_plan.items(), key=lambda x: -sum(len(e) for e in x[1].values())
            ):
                club_total = sum(len(e) for e in plans_in_club.values())
                html_blocks.append(
                    f'<div class="club-block">'
                    f'<div class="club-head">'
                    f'Клуб: {club_label(club_id)}'
                    f'<span class="club-sub"> — Нарушений: {club_total}</span>'
                    f'</div>'
                )
                for plan_id, club_entries in sorted(plans_in_club.items(), key=lambda x: -len(x[1])):
                    entry_rows = [
                        (v["time"].strftime("%Y-%m-%d %H:%M:%S"), str(v["_id"]), str(v["user"]))
                        for v in _sample_entries(club_entries)
                    ]
                    html_blocks.append(
                        f'<div class="plan-block">'
                        f'<div class="plan-head">'
                        f'Абонемент: {plan_label(plan_id)} — Нарушений: {len(club_entries)}'
                        f'</div>'
                        + _html_table(
                            ["Время входа", "entry_id", "user_id"],
                            entry_rows,
                            right_cols=(),
                        )
                        + "</div>"
                    )
                html_blocks.append("</div>")

            allure.attach(
                "".join(html_blocks),
                name="Нарушения по клубам (HTML)",
                attachment_type=allure.attachment_type.HTML,
            )

        # ── Абонементы без clubId (текст + HTML) ────────────────────────────────
        if no_clubid_entries:
            def interval_label(interval):
                return {365: "Годовой", 180: "Полугодовой", 90: "3-месячный", 30: "Месячный"}.get(
                    interval, f"{interval} дн." if interval else "—"
                )

            # Группировка: клуб входа → план → записи
            by_club_plan_nc = defaultdict(lambda: defaultdict(list))
            for e in no_clubid_entries:
                by_club_plan_nc[e.get("club")][e["_plan_id"]].append(e)

            # --- текст ---
            nc_lines = []
            for club_id, plans_in_club in sorted(
                by_club_plan_nc.items(), key=lambda x: -sum(len(e) for e in x[1].values())
            ):
                club_total = sum(len(e) for e in plans_in_club.values())
                nc_lines += [f"Клуб: {club_label(club_id)}", f"Входов: {club_total}"]
                for plan_id, club_entries in sorted(plans_in_club.items(), key=lambda x: -len(x[1])):
                    p = plan_map.get(plan_id, {})
                    nc_lines += [
                        "",
                        f"  Абонемент: {plan_label(plan_id)}",
                        f"  Тип: {interval_label(p.get('interval'))}",
                        f"  Входов: {len(club_entries)}",
                    ]
                    for v in _sample_entries(club_entries):
                        nc_lines.append(
                            f"    - {v['time'].strftime('%Y-%m-%d %H:%M:%S')} "
                            f"| entry_id={v['_id']} | user={v['user']}"
                        )
                nc_lines += ["", "-" * 50, ""]
            nc_text = "\n".join(nc_lines)
            print("\n== Абонементы без clubId ===\n" + nc_text)
            allure.attach(nc_text, name="Абонементы без clubId", attachment_type=allure.attachment_type.TEXT)

            # --- HTML ---
            nc_html = [_HTML_CSS, "<h2>Абонементы без clubId</h2>"]
            for club_id, plans_in_club in sorted(
                by_club_plan_nc.items(), key=lambda x: -sum(len(e) for e in x[1].values())
            ):
                club_total = sum(len(e) for e in plans_in_club.values())
                nc_html.append(
                    f'<div class="club-block">'
                    f'<div class="club-head">'
                    f'Клуб: {club_label(club_id)}'
                    f'<span class="club-sub"> — Входов: {club_total}</span>'
                    f'</div>'
                )
                for plan_id, club_entries in sorted(plans_in_club.items(), key=lambda x: -len(x[1])):
                    p = plan_map.get(plan_id, {})
                    entry_rows = [
                        (v["time"].strftime("%Y-%m-%d %H:%M:%S"), str(v["_id"]), str(v["user"]))
                        for v in _sample_entries(club_entries)
                    ]
                    nc_html.append(
                        f'<div class="plan-block">'
                        f'<div class="plan-head">'
                        f'Абонемент: {plan_label(plan_id)}'
                        f' — Тип: {interval_label(p.get("interval"))}'
                        f' — Входов: {len(club_entries)}'
                        f'</div>'
                        + _html_table(
                            ["Время входа", "entry_id", "user_id"],
                            entry_rows,
                            right_cols=(),
                        )
                        + "</div>"
                    )
                nc_html.append("</div>")
            allure.attach(
                "".join(nc_html),
                name="Планы без clubId (HTML)",
                attachment_type=allure.attachment_type.HTML,
            )

    assert len(violations) == 0, (
        f"Найдено {len(violations)} входов по абонементу с accessType != 'subscription' "
        f"({_pct(len(violations), total_in_window)} из {total_in_window} входов в окне). "
        f"Первый: entry_id={violations[0]['_id']}, "
        f"клуб={club_label(violations[0].get('club'))}, "
        f"план={plan_label(violations[0]['_plan_id'])}, "
        f"accessType='{violations[0].get('accessType', '—')}'"
    )
