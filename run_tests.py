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
import time
from datetime import datetime
import urllib.request
import urllib.error
from src.utils.allure_report_patcher import patch_allure_report

# ==============================================================
#  НАСТРОЙКИ — редактируй здесь
# ==============================================================

MODE = "mobile"             # "mobile" | "backend" | "monitoring" | "web"

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
    "monitoring": "tests_to_run_backend_monitoring.txt",
    "web":     "tests_to_run_web.txt",
}

TEMP_ARTIFACTS_DIR = "tmp"

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


def check_mobile_prerequisites() -> bool:
    """
    Проверяет подключение устройства через ADB и доступность Appium-сервера.
    Если Appium не запущен — пытается запустить его автоматически.
    Возвращает True, если всё готово к запуску тестов.
    """
    from dotenv import load_dotenv
    load_dotenv()
    appium_url = os.getenv("APPIUM_SERVER_URL", "http://localhost:4723")

    print("=" * 60)
    print("Предварительная проверка мобильного окружения")
    print("=" * 60)

    # --- 1. Проверка ADB ---
    print("\n[1/2] Проверка подключённых устройств (adb devices)...")

    if shutil.which("adb") is None:
        print("ERROR: adb не найден. Убедитесь, что Android SDK Platform Tools установлены и добавлены в PATH.")
        return False

    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = [line.strip() for line in result.stdout.strip().splitlines()]
        # Первая строка — "List of devices attached", остальные — устройства
        device_lines = [line for line in lines[1:] if line and not line.startswith("*")]

        if not device_lines:
            print("ERROR: Нет подключённых устройств. Подключите устройство или запустите эмулятор.")
            return False

        unauthorized = [line for line in device_lines if "unauthorized" in line]
        offline = [line for line in device_lines if "offline" in line]
        ready = [line for line in device_lines if "\tdevice" in line or " device" in line]

        print(f"  Обнаружено устройств: {len(device_lines)}")
        for dev in device_lines:
            print(f"    {dev}")

        if unauthorized:
            print("WARNING: Неавторизованные устройства — разрешите USB-отладку на экране устройства.")
        if offline:
            print("WARNING: Offline-устройства — проверьте USB-кабель или перезапустите adb.")
        if not ready:
            print("ERROR: Нет готовых устройств (все offline или unauthorized).")
            return False

        print(f"  Готово к работе: {len(ready)} устройство(а)")

    except subprocess.TimeoutExpired:
        print("ERROR: adb devices завис (timeout 10s). Попробуйте перезапустить adb: adb kill-server && adb start-server")
        return False
    except Exception as e:
        print(f"ERROR: Не удалось выполнить adb devices: {e}")
        return False

    # --- 2. Проверка Appium ---
    print(f"\n[2/2] Проверка Appium-сервера ({appium_url})...")

    def appium_is_running() -> bool:
        try:
            req = urllib.request.urlopen(f"{appium_url}/status", timeout=5)
            return req.status == 200
        except Exception:
            return False

    if appium_is_running():
        print(f"  Appium уже запущен: {appium_url}")
    else:
        print("  Appium не запущен. Запускаю...")

        if shutil.which("appium") is None:
            print("ERROR: appium не найден. Установите: npm install -g appium")
            return False

        try:
            is_windows = platform.system() == "Windows"
            subprocess.Popen(
                ["appium"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=is_windows,
            )
        except Exception as e:
            print(f"ERROR: Не удалось запустить Appium: {e}")
            return False

        print("  Ожидание запуска Appium", end="", flush=True)
        for _ in range(15):
            time.sleep(1)
            print(".", end="", flush=True)
            if appium_is_running():
                break
        print()

        if not appium_is_running():
            print("ERROR: Appium не запустился за 15 секунд. Проверьте порт и вывод в терминале.")
            return False

        print(f"  Appium запущен: {appium_url}")

    print("\n  Окружение готово. Запуск тестов...\n")
    return True


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
    file_single_test = None
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
            elif upper.startswith("SINGLE_TEST:"):
                value = cfg.split(":", 1)[1].strip()
                if value and value.lower() != "none":
                    file_single_test = value
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

    if file_single_test is not None:
        normalized = file_single_test.replace("\\", "/").lower()
        tests = [(p, a) for p, a in tests if p.replace("\\", "/").lower() == normalized]
        if not tests:
            print(f"ERROR: SINGLE_TEST={file_single_test!r} не найден в списке тестов")
            return 1
        print(f"SINGLE_TEST: запускается только {file_single_test}")

    mode_labels = {
        "mobile": "мобильных",
        "backend": "backend",
        "monitoring": "backend monitoring",
        "web": "web",
    }
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
            try:
                shutil.rmtree(allure_dir)
            except PermissionError:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                allure_dir = os.path.join(
                    TEMP_ARTIFACTS_DIR,
                    f"allure-results_{timestamp}",
                )
                print(
                    f"WARNING: Не удалось очистить занятый каталог allure-results. "
                    f"Результаты будут записаны в {allure_dir}"
                )
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
            "monitoring": (
                "Project=Invictus Automated Testing (Backend Monitoring)\n"
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
        # Use the active Python environment and place the test path first so
        # backend-specific pytest options from nested conftest files are loaded.
        cmd = [sys.executable, "-m", "pytest", test_path] + pytest_args + line_args
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
                report_dir = "allure-report"
                if os.path.exists(report_dir):
                    shutil.rmtree(report_dir)

                generate_cmd = ["allure", "generate", "-o", report_dir, allure_dir]
                print("Команда:", " ".join(generate_cmd))
                generate_result = subprocess.run(generate_cmd, shell=is_windows)
                if generate_result.returncode != 0:
                    raise RuntimeError(f"allure generate завершился с кодом {generate_result.returncode}")

                patched = patch_allure_report(report_dir)
                if patched:
                    print(f"Применён локальный патч iframe-resize для {report_dir}")
                else:
                    print(f"WARNING: Не удалось пропатчить {report_dir} (index.html не найден)")

                open_cmd = ["allure", "open", report_dir]
                print("Команда:", " ".join(open_cmd))
                subprocess.run(open_cmd, shell=is_windows)
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

    if MODE == "mobile" and not check_mobile_prerequisites():
        sys.exit(1)

    sys.exit(run_tests_from_file(
        file_path=file_path,
        generate_allure=ALLURE,
        open_report=OPEN_REPORT,
        mode=MODE,
    ))
