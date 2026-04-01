"""
Запуск тестов из файла списка.

Формат файла списка:
  - Каждая строка — путь к тесту, опционально с флагами через |:
        tests/web/test_foo.py | -v -k smoke
  - Специальные директивы в начале файла (строки с #):
        # PYTEST_ARGS: -v -s
        # ALLURE: on|off
        # OPEN_REPORT: on|off
        # INTERACTIVE: on|off
"""
import subprocess
import sys
import os
import platform
import shutil

# ==============================================================
#  НАСТРОЙКИ — редактируй здесь
# ==============================================================

MODE = "backend"          # "mobile" | "backend" | "web"

FILE = None              # None = дефолтный файл для режима:
                         #   mobile  → tests_to_run_mobile.txt
                         #   backend → tests_to_run_backend.txt
                         #   web     → tests_to_run_web.txt

ALLURE = True            # генерировать Allure-отчёт
OPEN_REPORT = True       # открывать отчёт после прогона

# ==============================================================

DEFAULT_FILES = {
    "mobile":  "tests_to_run_mobile.txt",
    "backend": "tests_to_run_backend.txt",
    "web":     "tests_to_run_web.txt",
}

ALLURE_CATEGORIES_WEB = """[
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
    "name": "Database issues",
    "messageRegex": ".*MongoDB.*|.*database.*",
    "matchedStatuses": ["broken"]
  },
  {
    "name": "Ignored tests",
    "matchedStatuses": ["skipped"]
  }
]
"""

ALLURE_CATEGORIES_MOBILE = """[
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


def run_tests_from_file(file_path, pytest_args=None, generate_allure=True, open_report=True, mode="web"):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_lines = [line.rstrip("\n") for line in f]
    except FileNotFoundError:
        print(f"ERROR: Файл {file_path} не найден")
        return 1

    # --- Разбор директив и тестов из файла ---
    file_pytest_args = None
    file_period_days = None
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
            elif upper.startswith("PERIOD_DAYS:"):
                value = cfg.split(":", 1)[1].strip()
                try:
                    file_period_days = int(value)
                except ValueError:
                    print(f"WARNING: Неверное значение PERIOD_DAYS: {value!r}, игнорируется")
            continue

        if "|" in stripped:
            path_part, args_part = stripped.split("|", 1)
            test_path = path_part.strip()
            line_args = args_part.strip().split() if args_part.strip() else []
        else:
            test_path = stripped
            line_args = []

        tests.append((test_path, line_args))

    # Директивы из файла перекрывают значения по умолчанию / CLI
    if file_generate_allure is not None:
        generate_allure = file_generate_allure
    if file_open_report is not None:
        open_report = file_open_report
    if file_pytest_args is not None:
        pytest_args = file_pytest_args
    if file_period_days is not None and "--period-days" not in (pytest_args or []):
        pytest_args = ["--period-days", str(file_period_days)] + (pytest_args or [])

    if not tests:
        print(f"WARNING: Файл {file_path} пустой или не содержит тестов")
        return 1

    mode_labels = {"mobile": "мобильных", "backend": "backend", "web": "web"}
    mode_label = mode_labels.get(mode, "")
    print(f"Запуск {len(tests)} {mode_label} тест(ов) из {file_path}:")
    for test_path, line_args in tests:
        suffix = f"  |  {' '.join(line_args)}" if line_args else ""
        print(f"  - {test_path}{suffix}")
    print()

    if pytest_args is None:
        pytest_args = ["-v"]

    if interactive and "-s" not in pytest_args:
        pytest_args = pytest_args + ["-s"]

    allure_dir = "allure-results"
    if generate_allure:
        if os.path.exists(allure_dir):
            shutil.rmtree(allure_dir)
        os.makedirs(allure_dir, exist_ok=True)

        env_props_map = {
            "mobile": (
                "Project=Invictus Automated Testing (Mobile)\n"
                "Environment=Stage\n"
                "Test.Framework=Pytest\n"
                "Appium=Mobile\n"
                "Report.Type=Allure\n"
            ),
            "backend": (
                "Project=Invictus Automated Testing (Backend)\n"
                "Environment=Production\n"
                "Test.Framework=Pytest\n"
                "Database=MongoDB\n"
                "Report.Type=Allure\n"
            ),
            "web": (
                "Project=Invictus Automated Testing (Web)\n"
                "Environment=Production\n"
                "Test.Framework=Pytest\n"
                "Browser=Chromium\n"
                "Report.Type=Allure\n"
            ),
        }
        with open(os.path.join(allure_dir, "environment.properties"), "w", encoding="utf-8") as f:
            f.write(env_props_map.get(mode, env_props_map["web"]))

        categories = ALLURE_CATEGORIES_MOBILE if mode == "mobile" else ALLURE_CATEGORIES_WEB
        with open(os.path.join(allure_dir, "categories.json"), "w", encoding="utf-8") as f:
            f.write(categories)

        if "--alluredir" not in " ".join(pytest_args):
            pytest_args = pytest_args + ["--alluredir", allure_dir]

    overall_return_code = 0

    for test_path, line_args in tests:
        cmd = ["pytest"] + pytest_args + line_args + [test_path]
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

        if shutil.which("allure") is None:
            print("\nWARNING: Allure не установлен! (scoop install allure)")
            print(f"Результаты сохранены в: {allure_dir}")
            print(f"Для отчета: allure serve {allure_dir}")
        else:
            print(f"Запуск Allure с результатами из {allure_dir}...")
            try:
                is_windows = platform.system() == "Windows"
                subprocess.run(["allure", "serve", allure_dir], shell=is_windows)
            except KeyboardInterrupt:
                print("\n\nAllure отчет закрыт пользователем")
            except Exception as e:
                print(f"\nERROR: Не удалось запустить Allure: {e}")

    return overall_return_code


if __name__ == "__main__":
    if MODE not in DEFAULT_FILES:
        print(f"ERROR: Неизвестный MODE={MODE!r}. Допустимые: {list(DEFAULT_FILES)}")
        sys.exit(1)

    file_path = FILE or DEFAULT_FILES[MODE]

    sys.exit(run_tests_from_file(
        file_path=file_path,
        generate_allure=ALLURE,
        open_report=OPEN_REPORT,
        mode=MODE,
    ))
