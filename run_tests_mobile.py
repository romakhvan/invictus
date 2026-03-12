"""
Запуск мобильных (Appium) тестов из файла tests_to_run_mobile.txt.
Использует тот же механизм, что и run_tests.py, с файлом списка для mobile.
"""
import subprocess
import sys
import argparse
import shutil
import os
import platform

# Файл со списком мобильных тестов по умолчанию
DEFAULT_MOBILE_FILE = 'tests_to_run_mobile.txt'


def run_tests_from_file(file_path=DEFAULT_MOBILE_FILE, pytest_args=None, generate_allure=True, open_report=True):
    """
    Запускает pytest тесты, перечисленные в файле.

    Дополнительная конфигурация может задаваться внутри файла списка тестов
    через специальные комментарии (обрабатываются до списка тестов):

    # PYTEST_ARGS: -v -s
        - Явно задаёт аргументы для pytest (например, -s для интерактивного меню).
    # ALLURE: on|off
        - Управляет генерацией Allure-результатов (off отключает).
    # OPEN_REPORT: on|off
        - Управляет автоматическим открытием Allure-отчёта (off отключает).
    # INTERACTIVE: on|off
        - При on добавляет -s к аргументам pytest (для отображения навигационного меню/инпутов).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_lines = [line.rstrip("\n") for line in f]

        # --- Конфигурация из файла ---
        file_pytest_args = None
        file_generate_allure = None
        file_open_report = None
        interactive = None
        tests: list[tuple[str, list[str]]] = []

        for line in raw_lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                cfg = stripped.lstrip("#").strip()
                upper = cfg.upper()
                if upper.startswith("PYTEST_ARGS:"):
                    args_str = cfg.split(":", 1)[1].strip()
                    if args_str:
                        file_pytest_args = args_str.split()
                elif upper.startswith("ALLURE:"):
                    value = cfg.split(":", 1)[1].strip().lower()
                    if value in {"on", "off"}:
                        file_generate_allure = value == "on"
                elif upper.startswith("OPEN_REPORT:"):
                    value = cfg.split(":", 1)[1].strip().lower()
                    if value in {"on", "off"}:
                        file_open_report = value == "on"
                elif upper.startswith("INTERACTIVE:"):
                    value = cfg.split(":", 1)[1].strip().lower()
                    if value in {"on", "off"}:
                        interactive = value == "on"
                continue

            # Обычная строка — это путь к тесту, опционально с флагами:
            # tests\path\test_file.py | -m mobile --mobile-no-reset
            if "|" in stripped:
                path_part, args_part = stripped.split("|", 1)
                test_path = path_part.strip()
                line_args = args_part.strip().split() if args_part.strip() else []
            else:
                test_path = stripped
                line_args = []

            tests.append((test_path, line_args))

        # Применяем конфигурацию из файла поверх значений по умолчанию / CLI
        if file_generate_allure is not None:
            generate_allure = file_generate_allure
        if file_open_report is not None:
            open_report = file_open_report
        if file_pytest_args is not None:
            pytest_args = file_pytest_args

        if not tests:
            print(f"WARNING: Файл {file_path} пустой или не содержит тестов")
            return 1

        print(f"Запуск {len(tests)} мобильных тест(ов) из {file_path}:")
        for test_path, line_args in tests:
            if line_args:
                print(f"  - {test_path}  |  {' '.join(line_args)}")
            else:
                print(f"  - {test_path}")
        print()

        # Базовые аргументы pytest, если не заданы
        if pytest_args is None:
            pytest_args = ['-v']

        # Режим интерактивного меню (для _interactive_debug_menu и т.п.)
        if interactive:
            if '-s' not in pytest_args:
                pytest_args = pytest_args + ['-s']

        allure_dir = 'allure-results'
        if generate_allure:
            if os.path.exists(allure_dir):
                shutil.rmtree(allure_dir)
            os.makedirs(allure_dir, exist_ok=True)

            env_props = """Project=Invictus Automated Testing (Mobile)
Environment=Stage
Test.Framework=Pytest
Appium=Mobile
Report.Type=Allure
"""
            with open(os.path.join(allure_dir, 'environment.properties'), 'w', encoding='utf-8') as f:
                f.write(env_props)

            categories = """[
  {
    "name": "Product defects",
    "messageRegex": ".*FAIL.*",
    "matchedStatuses": ["failed"]
  },
  {
    "name": "Test defects",
    "messageRegex": ".*AssertionError.*",
    "matchedStatuses": ["failed", "broken"]
  },
  {
    "name": "Appium/Device issues",
    "messageRegex": ".*Appium.*|.*session.*|.*device.*",
    "matchedStatuses": ["broken"]
  },
  {
    "name": "Ignored tests",
    "matchedStatuses": ["skipped"]
  }
]
"""
            with open(os.path.join(allure_dir, 'categories.json'), 'w', encoding='utf-8') as f:
                f.write(categories)

            if '--alluredir' not in ' '.join(pytest_args):
                pytest_args = pytest_args + ['--alluredir', allure_dir]

        overall_return_code = 0

        # Запускаем каждый тест/путь отдельно, чтобы можно было задавать флаги построчно
        for test_path, line_args in tests:
            cmd = ['pytest'] + pytest_args + line_args + [test_path]
            print("\n" + "-" * 60)
            print("Команда:", " ".join(cmd))
            print("-" * 60)
            result = subprocess.run(cmd)
            if result.returncode != 0 and overall_return_code == 0:
                overall_return_code = result.returncode

        if generate_allure and open_report:
            print("\n" + "=" * 60)
            print("Генерация и открытие Allure отчета...")
            print("=" * 60)

            if shutil.which('allure') is None:
                print("\nWARNING: Allure не установлен!")
                print("Установите Allure (например: scoop install allure)")
                print(f"Результаты сохранены в: {allure_dir}")
                print(f"Для отчета: allure serve {allure_dir}")
            else:
                print(f"Запуск Allure с результатами из {allure_dir}...")
                try:
                    is_windows = platform.system() == 'Windows'
                    subprocess.run(['allure', 'serve', allure_dir], shell=is_windows)
                except KeyboardInterrupt:
                    print("\n\nAllure отчет закрыт пользователем")
                except Exception as e:
                    print(f"\nERROR: Не удалось запустить Allure: {e}")

        return overall_return_code

    except FileNotFoundError:
        print(f"ERROR: Файл {file_path} не найден")
        return 1
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        return 130


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Запуск мобильных тестов из файла (Allure по умолчанию)')
    parser.add_argument('--file', '-f', default=DEFAULT_MOBILE_FILE, help='Файл со списком тестов')
    parser.add_argument('--args', '-a', nargs='+', default=['-v'], help='Аргументы для pytest')
    parser.add_argument('--no-allure', action='store_true', help='Не генерировать Allure отчет')
    parser.add_argument('--no-open', action='store_true', help='Не открывать Allure отчет')

    args = parser.parse_args()
    sys.exit(run_tests_from_file(args.file, args.args, not args.no_allure, not args.no_open))
