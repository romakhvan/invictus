import pytest_check as check

def log_check(label: str, actual, expected):
    """
    🧩 Универсальная функция для проверки значений и печати результата в консоль.
    Используется для проверки title, text и других полей пушей.
    """
    # Нормализация
    actual_norm = str(actual).strip().lower()
    expected_norm = str(expected).strip().lower()

    # Цвета (ANSI)
    green = "\033[92m"
    red = "\033[91m"
    reset = "\033[0m"

    # Вывод в консоль
    if actual_norm == expected_norm:
        print(f"{green}✅ {label}: '{actual}' — OK{reset}")
    else:
        print(f"{red}❌ {label}: '{actual}' — FAIL (ожидалось: '{expected}'){reset}")

    # Проверка с записью в pytest-отчёт
    check.equal(
        actual_norm,
        expected_norm,
        f"❌ {label} отличается.\nОжидалось: '{expected}'\nПолучено: '{actual}'"
    )
