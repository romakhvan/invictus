import pytest_check as check
import sys

def safe_print(message: str):
    """Безопасный вывод для Windows консоли"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Кодируем строку в cp1251, заменяя непечатаемые символы
        encoded = message.encode(sys.stdout.encoding or 'cp1251', errors='replace')
        print(encoded.decode(sys.stdout.encoding or 'cp1251'))

def log_check(label: str, actual, expected):
    """
    Универсальная функция для проверки значений и печати результата в консоль.
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
        safe_print(f"{green}[OK] {label}: '{actual}'{reset}")
    else:
        safe_print(f"{red}[FAIL] {label}: '{actual}' (ожидалось: '{expected}'){reset}")

    # Проверка с записью в pytest-отчёт
    check.equal(
        actual_norm,
        expected_norm,
        f"[FAIL] {label} отличается.\nОжидалось: '{expected}'\nПолучено: '{actual}'"
    )
