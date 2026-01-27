import subprocess
import sys
import argparse
import shutil
import os
import platform


def run_tests_from_file(file_path='tests_to_run.txt', pytest_args=None, generate_allure=True, open_report=True):
    """Запускает pytest тесты, перечисленные в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tests = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not tests:
            print(f"WARNING: Файл {file_path} пустой или не содержит тестов")
            return 1
        
        print(f"Запуск {len(tests)} тест(ов) из {file_path}:")
        for test in tests:
            print(f"  - {test}")
        print()
        
        # Добавляем allure параметры если нужно
        allure_dir = 'allure-results'
        if generate_allure:
            # Очищаем старые результаты
            if os.path.exists(allure_dir):
                shutil.rmtree(allure_dir)
            os.makedirs(allure_dir, exist_ok=True)
            
            # Создаем environment.properties для Allure отчета
            env_props = """Project=Invictus Automated Testing
Environment=Production
Test.Framework=Pytest
Python.Version=3.13
Database=MongoDB
Report.Type=Allure
"""
            with open(os.path.join(allure_dir, 'environment.properties'), 'w', encoding='utf-8') as f:
                f.write(env_props)
            
            # Создаем categories.json для группировки ошибок
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
            with open(os.path.join(allure_dir, 'categories.json'), 'w', encoding='utf-8') as f:
                f.write(categories)
            
            # Добавляем --alluredir если его еще нет
            if pytest_args is None:
                pytest_args = ['-v']
            
            if '--alluredir' not in ' '.join(pytest_args):
                pytest_args = pytest_args + ['--alluredir', allure_dir]
        
        # Запускаем тесты
        cmd = ['pytest'] + pytest_args + tests
        result = subprocess.run(cmd)
        
        # Генерируем и открываем Allure отчет
        if generate_allure and open_report:
            print("\n" + "="*60)
            print("Генерация и открытие Allure отчета...")
            print("="*60)
            
            # Проверяем наличие allure
            if shutil.which('allure') is None:
                print("\nWARNING: Allure не установлен!")
                print("Установите Allure:")
                print("  - Windows (Scoop): scoop install allure")
                print("  - macOS (Homebrew): brew install allure")
                print("  - Или скачайте с: https://github.com/allure-framework/allure2/releases")
                print(f"\nРезультаты тестов сохранены в: {allure_dir}")
                print(f"Для просмотра отчета выполните: allure serve {allure_dir}")
            else:
                # Открываем отчет
                print(f"Запуск Allure веб-сервера с результатами из {allure_dir}...")
                print("Отчет откроется в браузере автоматически.")
                print("Для остановки сервера нажмите Ctrl+C\n")
                try:
                    # На Windows используем shell=True для корректной работы с npm-командами
                    is_windows = platform.system() == 'Windows'
                    subprocess.run(['allure', 'serve', allure_dir], shell=is_windows)
                except KeyboardInterrupt:
                    print("\n\nAllure отчет закрыт пользователем")
                except FileNotFoundError:
                    print("\nERROR: Команда 'allure' не найдена!")
                    print("Установите Allure или проверьте PATH")
                except Exception as e:
                    print(f"\nERROR: Не удалось запустить Allure: {e}")
        
        return result.returncode
    
    except FileNotFoundError:
        print(f"ERROR: Файл {file_path} не найден")
        return 1
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        return 130


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Запуск тестов из файла с генерацией Allure отчета')
    parser.add_argument('--file', '-f', default='tests_to_run.txt', help='Файл со списком тестов')
    parser.add_argument('--args', '-a', nargs='+', default=['-v'], help='Аргументы для pytest')
    parser.add_argument('--no-allure', action='store_true', help='Не генерировать Allure отчет')
    parser.add_argument('--no-open', action='store_true', help='Не открывать Allure отчет автоматически')
    
    args = parser.parse_args()
    
    generate_allure = not args.no_allure
    open_report = not args.no_open
    
    sys.exit(run_tests_from_file(args.file, args.args, generate_allure, open_report))
