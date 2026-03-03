"""
Скрипт для визуализации графика ошибок транзакций по датам.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

# Устанавливаем UTF-8 для корректного отображения эмодзи в Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Загружаем переменные окружения из .env файла
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

import psycopg2
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os
from urllib.parse import quote_plus


def get_postgres_connection():
    """Создает подключение к PostgreSQL с проверкой учетных данных."""
    host = os.getenv("POSTGRES_HOST", "10.2.3.22")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DATABASE", "master")
    
    # Выводим диагностическую информацию
    print("\n🔍 Диагностика переменных окружения:")
    print(f"  POSTGRES_HOST: {host}")
    print(f"  POSTGRES_PORT: {port}")
    print(f"  POSTGRES_DATABASE: {database}")
    print(f"  POSTGRES_USER: {user if user else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"  POSTGRES_PASSWORD: {'установлен (' + password[:3] + '...)' if password else '❌ НЕ УСТАНОВЛЕН'}")
    
    # Проверяем наличие обязательных параметров
    if not user or not password:
        print("\n❌ ОШИБКА: Не установлены переменные окружения PostgreSQL")
        print("\nПроверьте файл .env и убедитесь, что в нем есть:")
        print("  POSTGRES_USER=ваш_логин")
        print("  POSTGRES_PASSWORD=ваш_пароль")
        print("\n⚠️  ВАЖНО: Строки НЕ должны начинаться с символа '#'")
        raise ValueError("PostgreSQL credentials not found")
    
    # Проверяем, что переменные не начинаются с '#' (закомментированы)
    if user.startswith('#') or password.startswith('#') or host.startswith('#'):
        print("\n❌ ОШИБКА: Переменные окружения начинаются с '#' (закомментированы)!")
        print("\nЭто означает, что в файле .env строки с переменными закомментированы.")
        print("\n❌ Неправильно:")
        print("  #POSTGRES_USER=myuser")
        print("  #POSTGRES_PASSWORD=mypass")
        print("\n✅ Правильно:")
        print("  POSTGRES_USER=myuser")
        print("  POSTGRES_PASSWORD=mypass")
        raise ValueError("Invalid credentials format - variables start with '#'")
    
    try:
        # Экранируем специальные символы в логине и пароле для URL
        encoded_user = quote_plus(user)
        encoded_password = quote_plus(password)
        conn_string = f"postgresql://{encoded_user}:{encoded_password}@{host}:{port}/{database}"
        return psycopg2.connect(conn_string)
    except Exception as e:
        print(f"\n❌ Ошибка подключения к PostgreSQL: {e}")
        print(f"\nПопытка подключения к: {host}:{port}/{database}")
        print(f"С пользователем: {user}")
        raise


def fetch_error_data():
    """Получает данные об ошибках из PostgreSQL."""
    query = """
    SELECT 
        DATE(created_at) as error_date,
        COUNT(*) as error_count,
        COUNT(DISTINCT user_id) as unique_users,
        SUM(price::numeric) as total_amount
    FROM mongo.transactions
    WHERE created_at >= '2026-01-01 14:55:00'::timestamp
      AND (source IS NULL OR source != 'pos')
      AND product_type = 'recurrent'
      AND reason = 'paybox payment init failed'
    GROUP BY DATE(created_at)
    ORDER BY error_date ASC
    """
    
    print("🔌 Подключение к PostgreSQL...")
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    print("📊 Выполнение запроса...")
    cursor.execute(query)
    results = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    print(f"✅ Получено {len(results)} записей")
    
    return results


def plot_error_graph(data):
    """Строит график ошибок по датам."""
    if not data:
        print("❌ Нет данных для построения графика")
        return
    
    # Разделяем данные на списки
    dates = [row[0] for row in data]
    error_counts = [row[1] for row in data]
    unique_users = [row[2] for row in data]
    
    # Создаем фигуру с двумя подграфиками
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle('График возникновения ошибок "paybox payment init failed"', 
                 fontsize=16, fontweight='bold')
    
    # График 1: Количество ошибок по датам
    ax1.plot(dates, error_counts, marker='o', linewidth=2, 
             markersize=6, color='#e74c3c', label='Количество ошибок')
    ax1.fill_between(dates, error_counts, alpha=0.3, color='#e74c3c')
    ax1.set_ylabel('Количество ошибок', fontsize=12, fontweight='bold')
    ax1.set_title('Динамика ошибок', fontsize=13, pad=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper left')
    
    # Добавляем значения на график
    for i, (date, count) in enumerate(zip(dates, error_counts)):
        if i % 2 == 0:  # Показываем каждую вторую точку, чтобы не перегружать
            ax1.annotate(f'{count}', 
                        xy=(date, count), 
                        xytext=(0, 10),
                        textcoords='offset points',
                        ha='center',
                        fontsize=9,
                        bbox=dict(boxstyle='round,pad=0.3', 
                                facecolor='white', 
                                edgecolor='gray', 
                                alpha=0.7))
    
    # График 2: Количество уникальных пользователей
    ax2.bar(dates, unique_users, color='#3498db', alpha=0.7, 
            label='Уникальные пользователи')
    ax2.set_xlabel('Дата', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Уникальные пользователи', fontsize=12, fontweight='bold')
    ax2.set_title('Количество затронутых пользователей', fontsize=13, pad=10)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.legend(loc='upper left')
    
    # Форматирование оси X для обоих графиков
    for ax in [ax1, ax2]:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    
    # Сохраняем график
    filename = f'data/error_graph_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"\n✅ График сохранен: {filename}")
    
    # Показываем график
    plt.show()


def print_statistics(data):
    """Выводит статистику по ошибкам."""
    if not data:
        return
    
    total_errors = sum(row[1] for row in data)
    total_users = sum(row[2] for row in data)
    avg_errors = total_errors / len(data)
    max_errors = max(row[1] for row in data)
    max_date = [row[0] for row in data if row[1] == max_errors][0]
    
    print("\n" + "=" * 60)
    print("📈 СТАТИСТИКА ОШИБОК")
    print("=" * 60)
    print(f"Период анализа:         {data[0][0]} - {data[-1][0]}")
    print(f"Всего дней с ошибками:  {len(data)}")
    print(f"Общее количество ошибок: {total_errors}")
    print(f"Среднее в день:         {avg_errors:.1f}")
    print(f"Максимум в день:        {max_errors} (дата: {max_date})")
    print(f"Всего затронуто пользователей: {total_users}")
    print("=" * 60)


if __name__ == "__main__":
    print("\n🚀 Запуск визуализации ошибок транзакций...\n")
    
    try:
        # Получаем данные
        data = fetch_error_data()
        
        if data:
            # Выводим статистику
            print_statistics(data)
            
            # Строим график
            print("\n📊 Построение графика...")
            plot_error_graph(data)
        else:
            print("\n⚠️  Данные не найдены")
    
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
