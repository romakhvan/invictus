"""Утилиты для форматирования дат на русском языке."""

from datetime import datetime, timedelta

RUSSIAN_MONTH_NAMES = (
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
)

RUSSIAN_MONTH_NAMES_GENITIVE = (
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
)


def current_week_range_str(now: datetime = None) -> str:
    """Текст диапазона текущей недели, например '27 апреля - 03 мая'."""
    if now is None:
        now = datetime.now()
    monday = now - timedelta(days=now.weekday())
    sunday = monday + timedelta(days=6)
    month_start = RUSSIAN_MONTH_NAMES_GENITIVE[monday.month - 1]
    month_end = RUSSIAN_MONTH_NAMES_GENITIVE[sunday.month - 1]
    return f"{monday.day:02d} {month_start} - {sunday.day:02d} {month_end}"


def current_month_str(now: datetime = None) -> str:
    """Текст текущего месяца и года, например 'апрель 2026'."""
    if now is None:
        now = datetime.now()
    return f"{RUSSIAN_MONTH_NAMES[now.month - 1]} {now.year}"


def current_year_str(now: datetime = None) -> str:
    """Текущий год в виде строки, например '2026'."""
    if now is None:
        now = datetime.now()
    return str(now.year)
