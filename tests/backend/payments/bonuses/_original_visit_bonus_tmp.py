"""
Проверка бизнес-правил начисления VISIT-бонусов:
1. Каждый VISIT-бонус соответствует реальному посещению клуба
   (accesscontrols.type=enter, без поля err, accessType != staff).
2. Пользователь получает не более одного VISIT-бонуса в день.
"""
import pytest
import allure
from collections import defaultdict
from datetime import datetime, timedelta

from src.utils.repository_helpers import get_collection

SAMPLE_SIZE = 500           # кол-во последних VISIT-бонусов для проверки
FORWARD_SAMPLE_USERS = 200  # кол-во пользователей-абонентов для прямой проверки
TIME_TOLERANCE_SEC = 5      # допустимое окно по времени (±5 секунд)


def _time_bucket(t, sec=TIME_TOLERANCE_SEC):
    """Усекает datetime до начала интервала в sec секунд (floor)."""
    return (int(t.timestamp()) // sec) * sec


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus accrual")
@allure.title("За посещение клуба начисляются бонусы (VISIT)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "visit", "accesscontrols")
def test_visit_bonus_accrual(db, period_days):
    """
    Для выборки последних SAMPLE_SIZE VISIT-бонусов проверяет:
    1. Каждый бонус имеет соответствующий enter в accesscontrols
       (без err, без accessType=staff, ±5 сек).
    2. Ни один пользователь не получил более одного VISIT-бонуса за день.
    """
    bonus_col = get_collection(db, "userbonuseshistories")
    access_col = get_collection(db, "accesscontrols")
    since = datetime.now() - timedelta(days=period_days)

    # 1. Выборка последних VISIT-бонусов за период
    # Исключаем записи с полем description — они добавляются вручную администраторами
    with allure.step(f"Получить последние {SAMPLE_SIZE} VISIT-бонусов за {period_days} дней"):
        visit_bonuses = list(bonus_col.find(
            {"type": "VISIT", "time": {"$gte": since}, "description": {"$exists": False}},
            {"_id": 1, "user": 1, "time": 1, "amount": 1},
        ).sort("time", -1).limit(SAMPLE_SIZE))

    if not visit_bonuses:
        pytest.skip(f"Нет VISIT-бонусов за последние {period_days} дней")

    allure.dynamic.parameter("Проверено бонусов", len(visit_bonuses))

    # 2. Проверка: не более одного VISIT-бонуса на пользователя в день
    with allure.step("Проверить уникальность бонусов (один в день на пользователя)"):
        day_map = defaultdict(list)
        for b in visit_bonuses:
            key = (str(b["user"]), b["time"].date())
            day_map[key].append(b["_id"])

        duplicate_days = {k: ids for k, ids in day_map.items() if len(ids) > 1}

    if duplicate_days:
        lines = [f"Дубли VISIT-бонусов за один день: {len(duplicate_days)} случаев\n"]
        for (user, date), ids in list(duplicate_days.items())[:20]:
            lines.append(f"  user={user}  date={date}  bonus_ids={ids}")
        allure.attach(
            "\n".join(lines),
            name="Дубли VISIT-бонусов",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert len(duplicate_days) == 0, (
        f"Найдено {len(duplicate_days)} случаев, когда пользователь получил "
        f"более одного VISIT-бонуса за день."
    )

    # 3. Bulk-запрос к accesscontrols: только валидные входы
    with allure.step("Загрузить валидные входы в клуб (без err, без staff)"):
        user_ids = list({b["user"] for b in visit_bonuses})
        times = [b["time"] for b in visit_bonuses]
        window_start = min(times) - timedelta(seconds=TIME_TOLERANCE_SEC)
        window_end   = max(times) + timedelta(seconds=TIME_TOLERANCE_SEC)

        entries = list(access_col.find(
            {
                "user": {"$in": user_ids},
                "type": "enter",
                "err": {"$exists": False},          # исключить ошибочные входы
                "accessType": {"$ne": "staff"},      # исключить staff-доступ
                "time": {"$gte": window_start, "$lte": window_end},
            },
            {"user": 1, "time": 1},
        ))

    # 4. Lookup-set (user, time_bucket)
    entry_set = {(str(e["user"]), _time_bucket(e["time"])) for e in entries}

    # 5. Найти бонусы без соответствующего визита
    # Проверяем три смежных бакета, чтобы исключить ложные промахи на границах интервалов
    with allure.step("Сопоставить бонусы с посещениями"):
        violations = []
        for b in visit_bonuses:
            bucket = _time_bucket(b["time"])
            user_key = str(b["user"])
            found = any(
                (user_key, bucket + offset) in entry_set
                for offset in (-TIME_TOLERANCE_SEC, 0, TIME_TOLERANCE_SEC)
            )
            if not found:
                violations.append(b)

    if violations:
        lines = [f"Найдено нарушений: {len(violations)} из {len(visit_bonuses)}\n"]
        for v in violations:
            lines.append(
                f"  bonus_id={v['_id']}  user={v['user']}  "
                f"amount={v.get('amount')}  time={v['time']}"
            )
        allure.attach(
            "\n".join(lines),
            name="VISIT-бонусы без посещения",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert len(violations) == 0, (
        f"Найдено {len(violations)} VISIT-бонусов без соответствующего посещения клуба. "
        f"Первый: bonus_id={violations[0]['_id']}, user={violations[0]['user']}, "
        f"time={violations[0]['time']}"
    )


@pytest.mark.backend
@allure.feature("Payments")
@allure.story("Bonus accrual")
@allure.title("За каждый день посещения клуба абоненту начислен VISIT-бонус")
@allure.severity(allure.severity_level.CRITICAL)
@allure.tag("backend", "payments", "bonuses", "visit", "accesscontrols")
def test_visit_generates_bonus(db, period_days):
    """
    Для пользователей-абонентов (тех, у кого есть VISIT-бонусы за период)
    проверяет, что каждый день с валидным посещением клуба содержит
    хотя бы один VISIT-бонус.
    """
    bonus_col = get_collection(db, "userbonuseshistories")
    access_col = get_collection(db, "accesscontrols")
    since = datetime.now() - timedelta(days=period_days)
    bonus_filter = {"type": "VISIT", "time": {"$gte": since}, "description": {"$exists": False}}

    # 1. Пользователи-абоненты: те, у кого есть VISIT-бонусы в периоде
    with allure.step(f"Найти пользователей-абонентов с VISIT-бонусами за {period_days} дней"):
        bonus_user_ids = bonus_col.distinct("user", bonus_filter)[:FORWARD_SAMPLE_USERS]

    if not bonus_user_ids:
        pytest.skip("Нет пользователей с VISIT-бонусами за период")

    allure.dynamic.parameter("Пользователей-абонентов", len(bonus_user_ids))

    # 2. Дни, когда этим пользователям начислялись VISIT-бонусы
    with allure.step("Загрузить дни с VISIT-бонусами для этих пользователей"):
        bonuses = list(bonus_col.find(
            {**bonus_filter, "user": {"$in": bonus_user_ids}},
            {"user": 1, "time": 1},
        ))
        bonus_days = {(str(b["user"]), b["time"].date()) for b in bonuses}

    # 3. Дни, когда эти пользователи совершали валидные входы
    with allure.step("Загрузить дни с валидными входами (без err, без staff)"):
        entries = list(access_col.find(
            {
                "user": {"$in": bonus_user_ids},
                "type": "enter",
                "err": {"$exists": False},
                "accessType": {"$ne": "staff"},
                "time": {"$gte": since},
            },
            {"user": 1, "time": 1},
        ))
        visit_days = {(str(e["user"]), e["time"].date()) for e in entries}

    # 4. Дни с посещением, но без начисленного бонуса
    with allure.step("Найти дни посещений без VISIT-бонуса"):
        violations = sorted(visit_days - bonus_days)

    if violations:
        # Группируем по пользователю для удобства чтения
        by_user = defaultdict(list)
        for user, date in violations:
            by_user[user].append(date)
        by_user_sorted = sorted(by_user.items(), key=lambda x: -len(x[1]))

        lines = [
            f"Дней посещений без VISIT-бонуса: {len(violations)}",
            f"Затронуто пользователей: {len(by_user)}\n",
        ]
        for user, dates in by_user_sorted[:30]:
            dates_str = ", ".join(str(d) for d in sorted(dates))
            lines.append(f"  user={user}  пропущено дней: {len(dates)}")
            lines.append(f"    {dates_str}")
        allure.attach(
            "\n".join(lines),
            name="Посещения без бонуса",
            attachment_type=allure.attachment_type.TEXT,
        )

    assert len(violations) == 0, (
        f"Найдено {len(violations)} дней с посещением клуба без VISIT-бонуса "
        f"у {len({u for u, _ in violations})} пользователей. "
        f"Первый: user={violations[0][0]}, date={violations[0][1]}"
    )
