"""
Тесты для статистики клиентов за 2025 год.
"""

import pytest
import pymongo
from datetime import datetime, timedelta
from collections import Counter
from bson import ObjectId
from src.utils.repository_helpers import get_collection, normalize_ids
from src.config.db_config import MONGO_URI_PROD, DB_NAME


@pytest.fixture(scope="session")
def db():
    """
    Фикстура для подключения к MongoDB PROD.
    Переопределяет фикстуру из tests/backend/conftest.py для использования PROD базы.
    """
    print("\n🔌 Connecting to MongoDB PROD...")
    client = pymongo.MongoClient(MONGO_URI_PROD)
    db = client[DB_NAME]
    yield db
    print("\n🧹 Closing Mongo PROD connection.")
    client.close()


def _normalize_group_training_id(group_training_id):
    """Нормализует ID групповой тренировки в ObjectId."""
    if isinstance(group_training_id, str):
        normalized_ids = normalize_ids([group_training_id])
        return normalized_ids[0] if normalized_ids else None
    elif isinstance(group_training_id, ObjectId):
        return group_training_id
    return None


def _get_event_date(event):
    """Извлекает дату из поля time.start события."""
    time_obj = event.get("time")
    if isinstance(time_obj, dict):
        return time_obj.get("start")
    return None


def _get_week_start_date(year, week_num):
    """Вычисляет дату начала недели по ISO номеру недели."""
    start_date = datetime.strptime(f"{year}-W{week_num:02d}-1", "%Y-W%W-%w").date()
    if start_date.year != year:
        start_date = datetime(year, 1, 1).date()
        while start_date.weekday() != 0:
            start_date += timedelta(days=1)
        start_date += timedelta(weeks=week_num - 1)
    return start_date


def _calculate_streaks(sorted_weeks, check_year_transition=False):
    """Вычисляет непрерывные стрики из отсортированного списка недель."""
    streaks = []
    if not sorted_weeks:
        return streaks
    
    current_streak = [sorted_weeks[0]]
    
    for i in range(1, len(sorted_weeks)):
        prev_year, prev_week = sorted_weeks[i - 1]
        curr_year, curr_week = sorted_weeks[i]
        
        is_next_week = False
        if curr_year == prev_year:
            if curr_week == prev_week + 1:
                is_next_week = True
        elif check_year_transition and curr_year == prev_year + 1:
            if curr_week == 1 and prev_week >= 52:
                is_next_week = True
        
        if is_next_week:
            current_streak.append((curr_year, curr_week))
        else:
            if current_streak:
                streaks.append(current_streak)
            current_streak = [(curr_year, curr_week)]
    
    if current_streak:
        streaks.append(current_streak)
    
    return streaks


def test_get_first_visit_date_by_user_id(db):
    """
    🧪 Тест: получение даты первого посещения клиента по userID.
    Фильтр: type: 'enter', период: 2025 год.
    """
    print("\n" + "=" * 80)
    print("СТАТИСТИКА КЛИЕНТА")
    print("=" * 80)
    
    # Пример userID - замените на реальный для тестирования
    # user_id = "507f1f77bcf86cd799439011"  # Пример ObjectId в виде строки
    user_id = '61f3c72b0410407f1865dcf1'
    
    if not user_id:
        print("⚠️ Тест пропущен: userID не указан")
        return
    
    # Нормализуем userID в ObjectId
    normalized_ids = normalize_ids([user_id])
    if not normalized_ids:
        print(f"❌ Неверный формат userID: {user_id}")
        return
    
    user_object_id = normalized_ids[0]
    
    # Определяем период 2025 года
    start_date_2025 = datetime(2025, 1, 1, 0, 0, 0)
    end_date_2025 = datetime(2025, 12, 31, 23, 59, 59)
    
    # Получаем коллекцию accesscontrols
    access_col = get_collection(db, "accesscontrols")
    
    # Формируем запрос: user + type: 'enter' + период 2025 года
    # Исключаем все записи с полем "err"
    query = {
        "user": user_object_id,
        "type": "enter",
        "time": {
            "$gte": start_date_2025,
            "$lte": end_date_2025
        },
        "err": {"$exists": False}
    }
    
    print(f"\n📋 ПАРАМЕТРЫ ЗАПРОСА")
    print(f"   User ID: {user_id}")
    print(f"   Type: 'enter'")
    print(f"   Период: {start_date_2025.strftime('%d.%m.%Y')} - {end_date_2025.strftime('%d.%m.%Y')}")
    print(f"   Исключены все записи с полем 'err'")
    
    # Считаем общее количество входов за 2025 год (без ошибок)
    total_visits_count = access_col.count_documents(query)
    
    # Считаем количество входов с ошибками для статистики
    query_with_error = {
        "user": user_object_id,
        "type": "enter",
        "time": {
            "$gte": start_date_2025,
            "$lte": end_date_2025
        },
        "err": {"$exists": True}
    }
    excluded_visits_count = access_col.count_documents(query_with_error)
    
    # Получаем все входы для подсчета уникальных дней
    all_visits = list(access_col.find(
        query,
        {"time": 1, "club": 1}
    ))
    
    # Извлекаем уникальные даты (без времени)
    unique_dates = {
        visit.get("time").date()
        for visit in all_visits
        if visit.get("time")
    }
    unique_days_count = len(unique_dates)
    
    # Анализ времени входов по периодам дня
    # Время в базе - UTC, местное время Алматы - UTC+5
    TIME_OFFSET_HOURS = 5
    
    time_periods = {
        "Утренние": 0,      # 05:00 - 11:59 (местное время)
        "Дневные": 0,       # 12:00 - 16:59 (местное время)
        "Вечерние": 0       # 17:00 - 00:00 (04:59) (местное время)
    }
    
    for visit in all_visits:
        visit_time = visit.get("time")
        if visit_time:
            # Прибавляем смещение для получения местного времени (UTC+5)
            local_time = visit_time + timedelta(hours=TIME_OFFSET_HOURS)
            hour = local_time.hour
            
            # Утренние: 05:00–11:59 (местное время)
            if 5 <= hour < 12:
                time_periods["Утренние"] += 1
            # Дневные: 12:00–16:59 (местное время)
            elif 12 <= hour < 17:
                time_periods["Дневные"] += 1
            # Вечерние: 17:00–00:00 (04:59) (местное время)
            else:  # hour >= 17 или hour < 5
                time_periods["Вечерние"] += 1
    
    # Находим самый популярный период
    most_popular_period = max(time_periods.items(), key=lambda x: x[1])
    
    print(f"\n🕐 РАСПРЕДЕЛЕНИЕ ПО ВРЕМЕНИ СУТОК (местное время Алматы, UTC+5)")
    print(f"   Утренние (05:00 - 11:59): {time_periods['Утренние']} входов")
    print(f"   Дневные (12:00 - 16:59): {time_periods['Дневные']} входов")
    print(f"   Вечерние (17:00 - 04:59): {time_periods['Вечерние']} входов")
    
    if most_popular_period[1] > 0:
        period_name, count = most_popular_period
        percentage = (count / total_visits_count * 100) if total_visits_count > 0 else 0
        print(f"   🏆 Самый популярный период: {period_name} ({count} входов, {percentage:.1f}%)")
    
    # Подсчитываем стрики по неделям (непрерывные серии недель посещений)
    # Определяем недели, в которые были посещения
    weeks_with_visits = {
        visit_date.isocalendar()[:2]  # (year, week_num)
        for visit_date in unique_dates
        if visit_date.isocalendar()[0] == 2025
    }
    
    # Сортируем недели и находим непрерывные стрики
    sorted_weeks = sorted(weeks_with_visits)
    streaks = _calculate_streaks(sorted_weeks, check_year_transition=False)
    
    # Выводим информацию о стриках
    if streaks:
        print(f"\n🔥 СТРИКИ ПО НЕДЕЛЯМ (непрерывные серии посещений)")
        print(f"   Всего стриков: {len(streaks)}")
        
        # Сортируем стрики по длине (от большего к меньшему)
        sorted_streaks = sorted(streaks, key=len, reverse=True)
        
        # Находим самый длинный стрик
        longest_streak = sorted_streaks[0] if sorted_streaks else []
        longest_streak_length = len(longest_streak)
        
        print(f"   Самый длинный стрик: {longest_streak_length} недель")
        
        # Выводим информацию о каждом стрике
        print(f"\n   Детали стриков:")
        for idx, streak in enumerate(sorted_streaks[:10], 1):  # Показываем топ-10
            start_year, start_week = streak[0]
            end_year, end_week = streak[-1]
            
            start_date = _get_week_start_date(start_year, start_week)
            end_date = start_date + timedelta(days=6)  # Воскресенье той же недели
            
            # Для последней недели стрика
            if end_week != start_week:
                end_date = _get_week_start_date(end_year, end_week) + timedelta(days=6)
            
            print(f"   Стрик #{idx}: {len(streak)} недель (недели {start_week}-{end_week} 2025)")
        
        if len(sorted_streaks) > 10:
            print(f"   ... и еще {len(sorted_streaks) - 10} стриков")
        
        # Статистика по стрикам
        streak_lengths = [len(s) for s in streaks]
        avg_streak_length = sum(streak_lengths) / len(streak_lengths) if streak_lengths else 0
        print(f"\n   Статистика стриков:")
        print(f"   Средняя длина стрика: {avg_streak_length:.1f} недель")
        print(f"   Минимальная длина: {min(streak_lengths)} недель")
        print(f"   Максимальная длина: {max(streak_lengths)} недель")
    else:
        print(f"\n🔥 Стрики по неделям: нет данных (нет посещений)")
    
    # Подсчитываем стрики по неделям за всё время (не только 2025 год)
    print(f"\n" + "=" * 80)
    print("СТАТИСТИКА ЗА ВСЁ ВРЕМЯ")
    print("=" * 80)
    
    print(f"\n🔥 СТРИКИ ПО НЕДЕЛЯМ")
    
    # Получаем все входы за всё время (без фильтра по году)
    # Исключаем все записи с полем "err"
    query_all_time = {
        "user": user_object_id,
        "type": "enter",
        "err": {"$exists": False}
    }
    
    all_visits_all_time = list(access_col.find(
        query_all_time,
        {"time": 1, "club": 1}
    ))
    
    # Извлекаем уникальные даты за всё время
    unique_dates_all_time = {
        visit.get("time").date()
        for visit in all_visits_all_time
        if visit.get("time")
    }
    
    # Определяем недели, в которые были посещения за всё время
    weeks_with_visits_all_time = {
        visit_date.isocalendar()[:2]  # (year, week_num)
        for visit_date in unique_dates_all_time
    }
    
    # Сортируем недели и находим непрерывные стрики за всё время
    sorted_weeks_all_time = sorted(weeks_with_visits_all_time)
    streaks_all_time = _calculate_streaks(sorted_weeks_all_time, check_year_transition=True)
    
    # Выводим информацию о стриках за всё время
    if streaks_all_time:
        print(f"   Всего стриков: {len(streaks_all_time)}")
        print(f"   Всего недель с посещениями: {len(weeks_with_visits_all_time)}")
        
        # Сортируем стрики по длине (от большего к меньшему)
        sorted_streaks_all_time = sorted(streaks_all_time, key=len, reverse=True)
        
        # Находим самый длинный стрик
        longest_streak_all_time = sorted_streaks_all_time[0] if sorted_streaks_all_time else []
        longest_streak_length_all_time = len(longest_streak_all_time)
        
        print(f"   Самый длинный стрик: {longest_streak_length_all_time} недель")
        
        # Выводим информацию о топ-10 стриках
        print(f"\n   Детали топ-10 стриков:")
        for idx, streak in enumerate(sorted_streaks_all_time[:10], 1):
            start_year, start_week = streak[0]
            end_year, end_week = streak[-1]
            
            start_date = _get_week_start_date(start_year, start_week)
            end_date = _get_week_start_date(end_year, end_week) + timedelta(days=6)
            
            if start_year == end_year:
                print(f"   Стрик #{idx}: {len(streak)} недель (недели {start_week}-{end_week} {start_year}, "
                      f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})")
            else:
                print(f"   Стрик #{idx}: {len(streak)} недель ({start_week} неделя {start_year} - "
                      f"{end_week} неделя {end_year}, {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})")
        
        if len(sorted_streaks_all_time) > 10:
            print(f"   ... и еще {len(sorted_streaks_all_time) - 10} стриков")
        
        # Статистика по стрикам за всё время
        streak_lengths_all_time = [len(s) for s in streaks_all_time]
        avg_streak_length_all_time = sum(streak_lengths_all_time) / len(streak_lengths_all_time) if streak_lengths_all_time else 0
        print(f"\n   Статистика стриков за всё время:")
        print(f"   Средняя длина стрика: {avg_streak_length_all_time:.1f} недель")
        print(f"   Минимальная длина: {min(streak_lengths_all_time)} недель")
        print(f"   Максимальная длина: {max(streak_lengths_all_time)} недель")
        
        # Период первого и последнего посещения
        if unique_dates_all_time:
            first_visit_date = min(unique_dates_all_time)
            last_visit_date = max(unique_dates_all_time)
            total_days = (last_visit_date - first_visit_date).days + 1
            print(f"\n   Период активности:")
            print(f"   Первое посещение: {first_visit_date.strftime('%d.%m.%Y')}")
            print(f"   Последнее посещение: {last_visit_date.strftime('%d.%m.%Y')}")
            print(f"   Всего дней в периоде: {total_days}")
            print(f"   Дней с посещениями: {len(unique_dates_all_time)}")
            if total_days > 0:
                activity_percentage = (len(unique_dates_all_time) / total_days * 100)
                print(f"   Процент активности: {activity_percentage:.1f}%")
    else:
        print(f"\n🔥 Стрики по неделям за всё время: нет данных (нет посещений)")
    
    # Подсчитываем посещения по месяцам
    visits_by_month = Counter()
    for visit in all_visits:
        visit_time = visit.get("time")
        if visit_time:
            # Формируем ключ "ГГГГ-ММ" для группировки по месяцам
            month_key = visit_time.strftime("%Y-%m")
            visits_by_month[month_key] += 1
    
    # Находим самый посещаемый месяц
    most_visited_month = None
    most_visited_count = 0
    if visits_by_month:
        most_visited_month, most_visited_count = visits_by_month.most_common(1)[0]
    
    # Названия месяцев на русском
    month_names = {
        "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
        "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
        "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
    }
    
    print(f"\n" + "=" * 80)
    print("СТАТИСТИКА ЗА 2025 ГОД")
    print("=" * 80)
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА")
    print(f"   Всего входов (type='enter', без ошибок): {total_visits_count}")
    if excluded_visits_count > 0:
        print(f"   Исключено входов с полем 'err': {excluded_visits_count}")
    print(f"   Уникальных дней с входами: {unique_days_count}")
    
    # Выводим статистику по месяцам
    if visits_by_month:
        print(f"\n📅 ПОСЕЩЕНИЯ ПО МЕСЯЦАМ")
        # Сортируем по месяцам (хронологически)
        sorted_months = sorted(visits_by_month.items())
        for month_key, count in sorted_months:
            year, month = month_key.split("-")
            month_name = month_names.get(month, month)
            print(f"   {month_name} 2025: {count} посещений")
        
        # Выводим самый посещаемый месяц
        if most_visited_month:
            year, month = most_visited_month.split("-")
            month_name = month_names.get(month, month)
            print(f"   🏆 Самый посещаемый месяц: {month_name} 2025 ({most_visited_count} посещений)")
    else:
        print(f"\n📅 ПОСЕЩЕНИЯ ПО МЕСЯЦАМ: нет данных")
    
    # Подсчитываем посещения по клубам
    clubs_col = get_collection(db, "clubs")
    club_visits_counter = Counter()
    club_ids_set = set()
    
    for visit in all_visits:
        club_id = visit.get("club")
        if club_id:
            # Нормализуем ID клуба
            if isinstance(club_id, str):
                normalized_ids = normalize_ids([club_id])
                if normalized_ids:
                    club_id = normalized_ids[0]
            if isinstance(club_id, ObjectId):
                club_visits_counter[str(club_id)] += 1
                club_ids_set.add(club_id)
    
    # Получаем названия клубов из коллекции clubs
    club_info = {}
    if club_ids_set:
        club_ids_list = list(club_ids_set)
        clubs = list(clubs_col.find(
            {"_id": {"$in": club_ids_list}},
            {"name": 1}
        ))
        
        for club in clubs:
            club_info[str(club["_id"])] = club.get("name", "Неизвестный клуб")
        
        # Для ID, которые не найдены в БД
        for club_id in club_ids_list:
            if str(club_id) not in club_info:
                club_info[str(club_id)] = "Клуб не найден"
    
    # Выводим статистику по клубам
    if club_visits_counter:
        print(f"\n🏢 ПОСЕЩЕНИЯ ПО КЛУБАМ")
        # Сортируем по количеству посещений (от большего к меньшему)
        sorted_clubs = sorted(club_visits_counter.items(), key=lambda x: x[1], reverse=True)
        
        for idx, (club_id, count) in enumerate(sorted_clubs, 1):
            club_name = club_info.get(club_id, "Неизвестный клуб")
            print(f"   {idx}. {club_name}: {count} посещений")
        
        # Статистика по уникальным клубам
        unique_clubs_count = len(club_visits_counter)
        total_club_visits = sum(club_visits_counter.values())
        if unique_clubs_count > 0:
            avg_visits = total_club_visits / unique_clubs_count
            print(f"\n   📈 Статистика:")
            print(f"      Уникальных клубов: {unique_clubs_count}")
            print(f"      Всего посещений: {total_club_visits}")
            print(f"      Среднее на клуб: {avg_visits:.1f}")
            
            # Самый посещаемый клуб
            most_visited_club_id, most_visited_count = sorted_clubs[0]
            most_visited_club_name = club_info.get(most_visited_club_id, "Неизвестный клуб")
            print(f"      🏆 Самый посещаемый: {most_visited_club_name} ({most_visited_count} посещений)")
    else:
        print(f"\n🏢 ПОСЕЩЕНИЯ ПО КЛУБАМ: нет данных")
        print(f"   В записях accesscontrols не найдено поле club")
    
    # Подсчитываем посещения по клубам за всё время
    print(f"\n🏢 ПОСЕЩЕНИЯ ПО КЛУБАМ")
    
    club_visits_counter_all_time = Counter()
    club_ids_set_all_time = set()
    
    for visit in all_visits_all_time:
        club_id = visit.get("club")
        if club_id:
            # Нормализуем ID клуба
            if isinstance(club_id, str):
                normalized_ids = normalize_ids([club_id])
                if normalized_ids:
                    club_id = normalized_ids[0]
            if isinstance(club_id, ObjectId):
                club_visits_counter_all_time[str(club_id)] += 1
                club_ids_set_all_time.add(club_id)
    
    # Получаем названия клубов из коллекции clubs (если еще не получены)
    if club_ids_set_all_time:
        # Определяем, какие ID клубов еще не получены
        already_loaded_str_ids = set(club_info.keys())
        new_club_ids = [
            cid for cid in club_ids_set_all_time 
            if str(cid) not in already_loaded_str_ids
        ]
        
        if new_club_ids:
            new_clubs = list(clubs_col.find(
                {"_id": {"$in": new_club_ids}},
                {"name": 1}
            ))
            
            for club in new_clubs:
                club_info[str(club["_id"])] = club.get("name", "Неизвестный клуб")
            
            # Для ID, которые не найдены в БД
            found_ids = {str(club["_id"]) for club in new_clubs}
            for club_id in new_club_ids:
                if str(club_id) not in found_ids:
                    club_info[str(club_id)] = "Клуб не найден"
    
    # Выводим статистику по клубам за всё время
    if club_visits_counter_all_time:
        # Сортируем по количеству посещений (от большего к меньшему)
        sorted_clubs_all_time = sorted(club_visits_counter_all_time.items(), key=lambda x: x[1], reverse=True)
        
        for idx, (club_id, count) in enumerate(sorted_clubs_all_time, 1):
            club_name = club_info.get(club_id, "Неизвестный клуб")
            print(f"   {idx}. {club_name}: {count} посещений")
        
        # Статистика по уникальным клубам за всё время
        unique_clubs_count_all_time = len(club_visits_counter_all_time)
        if unique_clubs_count_all_time > 0:
            total_club_visits_all_time = sum(club_visits_counter_all_time.values())
            avg_visits_all_time = total_club_visits_all_time / unique_clubs_count_all_time
            print(f"\n   📈 Статистика:")
            print(f"      Уникальных клубов: {unique_clubs_count_all_time}")
            print(f"      Всего посещений: {total_club_visits_all_time}")
            print(f"      Среднее на клуб: {avg_visits_all_time:.1f}")
            
            # Самый посещаемый клуб за всё время
            most_visited_club_id_all_time, most_visited_count_all_time = sorted_clubs_all_time[0]
            most_visited_club_name_all_time = club_info.get(most_visited_club_id_all_time, "Неизвестный клуб")
            print(f"      🏆 Самый посещаемый: {most_visited_club_name_all_time} ({most_visited_count_all_time} посещений)")
    else:
        print(f"   Нет данных (в записях accesscontrols не найдено поле club)")
    
    # Подсчитываем общее время в клубе (сопоставляем входы и выходы)
    # Исключаем все записи с полем "err"
    query_exit = {
        "user": user_object_id,
        "type": "exit",
        "time": {
            "$gte": start_date_2025,
            "$lte": end_date_2025
        },
        "err": {"$exists": False}
    }
    
    # Получаем все входы и выходы, отсортированные по времени
    all_enters = list(access_col.find(
        query,
        {"time": 1, "type": 1}
    ).sort("time", 1))
    
    all_exits = list(access_col.find(
        query_exit,
        {"time": 1, "type": 1}
    ).sort("time", 1))
    
    # Сопоставляем входы с выходами и считаем общее время
    # Для каждого входа ищем ближайший следующий выход
    total_time_in_club = timedelta(0)
    matched_pairs = []
    exit_index = 0  # Индекс следующего неиспользованного выхода
    
    for enter in all_enters:
        enter_time = enter.get("time")
        if not enter_time:
            continue
        
        # Ищем ближайший выход после этого входа, начиная с текущего индекса
        best_exit = None
        best_exit_index = None
        best_time_diff = None
        
        # Начинаем поиск с текущего индекса выхода (выходы отсортированы)
        for idx in range(exit_index, len(all_exits)):
            exit_record = all_exits[idx]
            exit_time = exit_record.get("time")
            if not exit_time:
                continue
            
            # Выход должен быть после входа
            if exit_time > enter_time:
                time_diff = exit_time - enter_time
                # Выбираем ближайший выход (с минимальной разницей)
                if best_exit is None or time_diff < best_time_diff:
                    best_exit = exit_record
                    best_exit_index = idx
                    best_time_diff = time_diff
                # Если нашли выход и следующий выход дальше, можно прервать поиск
                elif best_exit is not None:
                    break
        
        # Если нашли подходящий выход, добавляем пару
        if best_exit is not None:
            exit_time = best_exit.get("time")
            total_time_in_club += best_time_diff
            matched_pairs.append((enter_time, exit_time, best_time_diff))
            exit_index = best_exit_index + 1  # Следующий вход начнет поиск с этого индекса
    
    # Форматируем общее время
    total_seconds = int(total_time_in_club.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    print(f"\n⏱️  ВРЕМЯ В КЛУБЕ (из accesscontrols)")
    if total_time_in_club > timedelta(0):
        print(f"   Всего времени: {hours} ч. {minutes} мин. {seconds} сек. ({total_seconds / 3600:.2f} ч.)")
        print(f"   Сопоставлено пар вход/выход: {len(matched_pairs)}")
        
        # Средняя длительность одной тренировки
        if len(matched_pairs) > 0:
            avg_duration_seconds = total_seconds / len(matched_pairs)
            avg_hours = int(avg_duration_seconds) // 3600
            avg_minutes = (int(avg_duration_seconds) % 3600) // 60
            avg_secs = int(avg_duration_seconds) % 60
            print(f"   📈 Средняя длительность тренировки: {avg_hours} ч. {avg_minutes} мин. {avg_secs} сек. ({avg_duration_seconds / 60:.1f} мин.)")
    else:
        print(f"   Время в клубе: 0 (нет сопоставленных пар вход/выход)")
        print(f"   Входов: {len(all_enters)}, Выходов: {len(all_exits)}")
    
    # Подсчитываем общее время из entrymonthstatistics за 2025 год
    entry_stats_col = get_collection(db, "entrymonthstatistics")
    
    # Формируем запрос для entrymonthstatistics за 2025 год
    # Пробуем разные варианты структуры данных
    query_entry_stats = {"user": user_object_id}
    
    # Получаем все записи пользователя для анализа структуры
    all_user_records = list(entry_stats_col.find(query_entry_stats).limit(10))
    
    entry_stats_records = []
    
    if all_user_records:
        # Анализируем структуру первой записи
        sample_record = all_user_records[0]
        print(f"\n🔍 Структура entrymonthstatistics (пример): {list(sample_record.keys())}")
        if "month" in sample_record:
            print(f"   Пример значения month: {sample_record.get('month')}")
        
        # Если есть поле month (формат "YYYY-MM"), фильтруем по нему
        if "month" in sample_record:
            # Получаем все записи пользователя и фильтруем в коде
            all_records = list(entry_stats_col.find(
                query_entry_stats,
                {"duration": 1, "month": 1, "visits": 1, "isDeleted": 1}
            ))
            
            # Фильтруем записи за 2025 год
            # Формат month может быть "MM/YYYY" или "YYYY-MM"
            for record in all_records:
                if record.get("isDeleted"):
                    continue
                month_value = record.get("month")
                if month_value:
                    # Проверяем разные форматы month
                    if isinstance(month_value, str):
                        # Формат "MM/YYYY" - ищем "/2025"
                        if "/2025" in month_value:
                            entry_stats_records.append(record)
                        # Формат "YYYY-MM" - ищем начинается с "2025-"
                        elif month_value.startswith("2025-"):
                            entry_stats_records.append(record)
                        # Формат "YYYYMM" - ищем начинается с "2025"
                        elif month_value.startswith("2025") and len(month_value) >= 4:
                            entry_stats_records.append(record)
        # Если есть поле year
        elif "year" in sample_record:
            query_with_year = {**query_entry_stats, "year": 2025}
            entry_stats_records = list(entry_stats_col.find(query_with_year, {"duration": 1, "year": 1, "month": 1}))
        # Если есть поле date или createdAt
        elif "date" in sample_record or "createdAt" in sample_record:
            date_field = "date" if "date" in sample_record else "createdAt"
            query_with_date = {
                **query_entry_stats,
                date_field: {"$gte": start_date_2025, "$lte": end_date_2025}
            }
            entry_stats_records = list(entry_stats_col.find(query_with_date, {"duration": 1, date_field: 1}))
    
    # Суммируем duration и visits из всех записей
    total_duration_from_stats = 0
    total_visits_from_stats = 0
    records_count = 0
    
    # Статистика по месяцам из entrymonthstatistics
    duration_by_month_stats = {}  # ключ: "YYYY-MM", значение: duration в секундах
    visits_by_month_stats = {}    # ключ: "YYYY-MM", значение: количество визитов
    
    for record in entry_stats_records:
        duration = record.get("duration")
        visits = record.get("visits")
        month_value = record.get("month")
        
        # Определяем месяц для группировки
        month_key = None
        if month_value:
            if isinstance(month_value, str):
                # Формат "MM/YYYY" -> "YYYY-MM"
                if "/" in month_value:
                    parts = month_value.split("/")
                    if len(parts) == 2:
                        month_key = f"{parts[1]}-{parts[0].zfill(2)}"
                # Формат "YYYY-MM" -> оставляем как есть
                elif "-" in month_value and month_value.startswith("2025"):
                    month_key = month_value
        
        if duration is not None:
            # duration хранится в минутах, конвертируем в секунды
            if isinstance(duration, (int, float)):
                duration_seconds = duration * 60  # Конвертируем минуты в секунды
                total_duration_from_stats += duration_seconds
                
                # Добавляем в статистику по месяцам
                if month_key:
                    if month_key not in duration_by_month_stats:
                        duration_by_month_stats[month_key] = 0
                    duration_by_month_stats[month_key] += duration_seconds
        
        if visits is not None:
            # visits - количество визитов за месяц
            if isinstance(visits, (int, float)):
                total_visits_from_stats += int(visits)
                
                # Добавляем в статистику по месяцам
                if month_key:
                    if month_key not in visits_by_month_stats:
                        visits_by_month_stats[month_key] = 0
                    visits_by_month_stats[month_key] += int(visits)
        
        if duration is not None or visits is not None:
            records_count += 1
    
    # Форматируем время из entrymonthstatistics
    total_duration_seconds = int(total_duration_from_stats)
    duration_hours = total_duration_seconds // 3600
    duration_minutes = (total_duration_seconds % 3600) // 60
    duration_secs = total_duration_seconds % 60
    
    print(f"\n" + "=" * 80)
    print("СТАТИСТИКА ИЗ ENTRYMONTHSTATISTICS")
    print("=" * 80)
    
    print(f"\n📊 Данные за 2025 год:")
    if records_count > 0:
        print(f"   Всего визитов (visits): {total_visits_from_stats}")
        if total_duration_from_stats > 0:
            print(f"   Всего времени: {duration_hours} ч. {duration_minutes} мин. {duration_secs} сек.")
            print(f"   Всего секунд: {total_duration_seconds}")
            print(f"   Всего часов (с дробной частью): {total_duration_from_stats / 3600:.2f}")
        print(f"   Найдено записей: {records_count}")
        
        # Средняя длительность одной тренировки из entrymonthstatistics
        if total_visits_from_stats > 0 and total_duration_from_stats > 0:
            avg_duration_stats_seconds = total_duration_from_stats / total_visits_from_stats
            avg_stats_hours = int(avg_duration_stats_seconds) // 3600
            avg_stats_minutes = (int(avg_duration_stats_seconds) % 3600) // 60
            avg_stats_secs = int(avg_duration_stats_seconds) % 60
            print(f"\n📈 Средняя длительность одной тренировки (из entrymonthstatistics):")
            print(f"   {avg_stats_hours} ч. {avg_stats_minutes} мин. {avg_stats_secs} сек.")
            print(f"   {avg_duration_stats_seconds / 60:.1f} минут")
            print(f"   {avg_duration_stats_seconds:.0f} секунд")
        
        # Выводим статистику по месяцам из entrymonthstatistics
        if duration_by_month_stats:
            print(f"\n📅 Длительность посещений по месяцам (из entrymonthstatistics):")
            sorted_months_stats = sorted(duration_by_month_stats.items())
            for month_key, duration_sec in sorted_months_stats:
                year, month = month_key.split("-")
                month_name = month_names.get(month, month)
                duration_h = duration_sec // 3600
                duration_m = (duration_sec % 3600) // 60
                visits_count = visits_by_month_stats.get(month_key, 0)
                print(f"   {month_name} 2025: {duration_h} ч. {duration_m} мин. ({visits_count} визитов)")
        
        # Сравнение количества визитов
        if total_visits_count > 0:
            visits_diff = abs(total_visits_count - total_visits_from_stats)
            print(f"\n🔍 Сравнение количества визитов:")
            print(f"   accesscontrols: {total_visits_count}")
            print(f"   entrymonthstatistics: {total_visits_from_stats}")
            print(f"   Разница: {visits_diff}")
            if visits_diff == 0:
                print(f"   ✅ Количество визитов совпадает")
            elif visits_diff <= 2:
                print(f"   ⚠️ Небольшое расхождение (разница {visits_diff})")
            else:
                print(f"   ⚠️ Значительное расхождение (разница {visits_diff})")
        
        # Сравнение времени с accesscontrols
        if total_time_in_club > timedelta(0) and total_duration_from_stats > 0:
            diff_seconds = abs(total_seconds - total_duration_seconds)
            diff_hours = diff_seconds / 3600
            print(f"\n🔍 Сравнение времени:")
            print(f"   accesscontrols: {total_seconds} сек. ({total_seconds / 3600:.2f} ч.)")
            print(f"   entrymonthstatistics: {total_duration_seconds} сек. ({total_duration_from_stats / 3600:.2f} ч.)")
            print(f"   Разница: {diff_seconds} сек. ({diff_hours:.2f} ч.)")
            if diff_seconds < 60:
                print(f"   ✅ Время совпадает (разница менее минуты)")
            elif diff_seconds < 3600:
                print(f"   ⚠️ Небольшое расхождение времени (разница менее часа)")
            else:
                print(f"   ⚠️ Значительное расхождение времени (разница более часа)")
    else:
        print(f"   Визиты: {total_visits_from_stats}")
        print(f"   Время в клубе: 0 (записи не найдены или duration отсутствует)")
        print(f"   Проверьте наличие записей для userID {user_id} в entrymonthstatistics за 2025 год")
    
    # Получаем данные из entrylogs
    print(f"\n" + "=" * 80)
    print("ДАННЫЕ ИЗ ENTRYLOGS")
    print("=" * 80)
    
    entrylogs_col = get_collection(db, "entrylogs")
    query_entrylogs = {
        "user": user_object_id,
        "entryDate": {
            "$gte": start_date_2025,
            "$lte": end_date_2025
        }
    }
    
    entrylogs_records = list(entrylogs_col.find(
        query_entrylogs,
        {"_id": 1, "entryDate": 1, "exitDate": 1}
    ))
    
    # Подсчитываем время из entrylogs
    total_duration_entrylogs = timedelta(0)
    entrylogs_visits_count = len(entrylogs_records)
    
    for record in entrylogs_records:
        entry_date = record.get("entryDate")
        exit_date = record.get("exitDate")
        
        if entry_date and exit_date and isinstance(entry_date, datetime) and isinstance(exit_date, datetime):
            if exit_date > entry_date:
                total_duration_entrylogs += exit_date - entry_date
    
    total_duration_entrylogs_seconds = int(total_duration_entrylogs.total_seconds())
    entrylogs_hours = total_duration_entrylogs_seconds // 3600
    entrylogs_minutes = (total_duration_entrylogs_seconds % 3600) // 60
    entrylogs_secs = total_duration_entrylogs_seconds % 60
    
    print(f"\n📊 Статистика из entrylogs за 2025 год:")
    print(f"   Всего записей: {entrylogs_visits_count}")
    if total_duration_entrylogs > timedelta(0):
        print(f"   Всего времени: {entrylogs_hours} ч. {entrylogs_minutes} мин. {entrylogs_secs} сек. ({total_duration_entrylogs_seconds / 3600:.2f} ч.)")
        if entrylogs_visits_count > 0:
            avg_entrylogs_seconds = total_duration_entrylogs_seconds / entrylogs_visits_count
            avg_entrylogs_hours = int(avg_entrylogs_seconds) // 3600
            avg_entrylogs_minutes = (int(avg_entrylogs_seconds) % 3600) // 60
            avg_entrylogs_secs = int(avg_entrylogs_seconds) % 60
            print(f"   📈 Средняя длительность: {avg_entrylogs_hours} ч. {avg_entrylogs_minutes} мин. {avg_entrylogs_secs} сек. ({avg_entrylogs_seconds / 60:.1f} мин.)")
    else:
        print(f"   Время в клубе: 0")
    
    # Получаем данные из entrydaystatistics
    print(f"\n" + "=" * 80)
    print("ДАННЫЕ ИЗ ENTRYDAYSTATISTICS")
    print("=" * 80)
    
    entrydaystats_col = get_collection(db, "entrydaystatistics")
    query_entrydaystats = {"user": user_object_id}
    
    # Получаем все записи пользователя для анализа структуры
    sample_day_record = entrydaystats_col.find_one(query_entrydaystats)
    
    entrydaystats_records = []
    
    if sample_day_record:
        # Анализируем структуру
        print(f"\n🔍 Структура entrydaystatistics (пример): {list(sample_day_record.keys())}")
        
        # Пробуем разные варианты фильтрации по дате
        all_day_records = list(entrydaystats_col.find(
            query_entrydaystats,
            {"duration": 1, "date": 1, "day": 1, "entryDate": 1, "createdAt": 1, "isDeleted": 1, "entryLogs": 1}
        ))
        
        # Фильтруем записи за 2025 год
        for record in all_day_records:
            if record.get("isDeleted"):
                continue
            
            # Пробуем разные поля для даты
            record_date = None
            if "date" in record:
                record_date = record.get("date")
            elif "day" in record:
                record_date = record.get("day")
            elif "entryDate" in record:
                record_date = record.get("entryDate")
            elif "createdAt" in record:
                record_date = record.get("createdAt")
            
            if record_date:
                if isinstance(record_date, datetime):
                    if start_date_2025 <= record_date <= end_date_2025:
                        entrydaystats_records.append(record)
                elif isinstance(record_date, str):
                    # Пробуем разные форматы даты
                    parsed_date = None
                    # Формат "MM/DD/YYYY" (например, "10/12/2025")
                    try:
                        parsed_date = datetime.strptime(record_date, "%m/%d/%Y")
                    except:
                        pass
                    # Формат "YYYY-MM-DD"
                    if not parsed_date:
                        try:
                            parsed_date = datetime.strptime(record_date[:10], "%Y-%m-%d")
                        except:
                            pass
                    # Формат "DD.MM.YYYY"
                    if not parsed_date:
                        try:
                            parsed_date = datetime.strptime(record_date[:10], "%d.%m.%Y")
                        except:
                            pass
                    
                    if parsed_date and start_date_2025 <= parsed_date <= end_date_2025:
                        entrydaystats_records.append(record)
    
    # Подсчитываем duration из entrydaystatistics
    total_duration_entrydaystats = 0
    entrydaystats_visits_count = 0
    
    for record in entrydaystats_records:
        duration = record.get("duration")
        if duration is not None:
            # duration может быть в минутах или секундах
            if isinstance(duration, (int, float)):
                # Предполагаем, что duration в минутах (как в entrymonthstatistics)
                duration_seconds = duration * 60
                total_duration_entrydaystats += duration_seconds
                entrydaystats_visits_count += 1
    
    total_duration_entrydaystats_seconds = int(total_duration_entrydaystats)
    daystats_hours = total_duration_entrydaystats_seconds // 3600
    daystats_minutes = (total_duration_entrydaystats_seconds % 3600) // 60
    daystats_secs = total_duration_entrydaystats_seconds % 60
    
    print(f"\n📊 Статистика из entrydaystatistics за 2025 год:")
    print(f"   Найдено записей: {len(entrydaystats_records)}")
    if total_duration_entrydaystats > 0:
        print(f"   Всего времени: {daystats_hours} ч. {daystats_minutes} мин. {daystats_secs} сек. ({total_duration_entrydaystats / 3600:.2f} ч.)")
        if entrydaystats_visits_count > 0:
            avg_daystats_seconds = total_duration_entrydaystats / entrydaystats_visits_count
            avg_daystats_hours = int(avg_daystats_seconds) // 3600
            avg_daystats_minutes = (int(avg_daystats_seconds) % 3600) // 60
            avg_daystats_secs = int(avg_daystats_seconds) % 60
            print(f"   📈 Средняя длительность: {avg_daystats_hours} ч. {avg_daystats_minutes} мин. {avg_daystats_secs} сек. ({avg_daystats_seconds / 60:.1f} мин.)")
    else:
        print(f"   Время в клубе: 0 (записи не найдены или duration отсутствует)")
    
    # Сравнение всех источников данных
    print(f"\n" + "=" * 80)
    print("СРАВНЕНИЕ ВСЕХ ИСТОЧНИКОВ ДАННЫХ")
    print("=" * 80)
    
    print(f"\n📊 Сравнение количества визитов:")
    print(f"   accesscontrols: {total_visits_count}")
    print(f"   entrymonthstatistics: {total_visits_from_stats}")
    print(f"   entrylogs: {entrylogs_visits_count}")
    
    if total_visits_count > 0:
        if total_visits_count == total_visits_from_stats == entrylogs_visits_count:
            print(f"   ✅ Все источники показывают одинаковое количество визитов")
        else:
            print(f"   ⚠️ Есть расхождения между источниками")
            if total_visits_count != total_visits_from_stats:
                print(f"      Разница accesscontrols vs entrymonthstatistics: {abs(total_visits_count - total_visits_from_stats)}")
            if total_visits_count != entrylogs_visits_count:
                print(f"      Разница accesscontrols vs entrylogs: {abs(total_visits_count - entrylogs_visits_count)}")
            if total_visits_from_stats != entrylogs_visits_count:
                print(f"      Разница entrymonthstatistics vs entrylogs: {abs(total_visits_from_stats - entrylogs_visits_count)}")
    
    print(f"\n⏱️  Сравнение времени в клубе:")
    sources_time = []
    if total_time_in_club > timedelta(0):
        sources_time.append(("accesscontrols", total_seconds))
    if total_duration_from_stats > 0:
        sources_time.append(("entrymonthstatistics", total_duration_seconds))
    if total_duration_entrylogs > timedelta(0):
        sources_time.append(("entrylogs", total_duration_entrylogs_seconds))
    if total_duration_entrydaystats > 0:
        sources_time.append(("entrydaystatistics", total_duration_entrydaystats_seconds))
    
    if sources_time:
        for source_name, source_seconds in sources_time:
            print(f"   {source_name}: {source_seconds} сек. ({source_seconds / 3600:.2f} ч.)")
        
        if len(sources_time) > 1:
            # Находим минимальное и максимальное значение
            min_seconds = min(s[1] for s in sources_time)
            max_seconds = max(s[1] for s in sources_time)
            diff_seconds = max_seconds - min_seconds
            
            if diff_seconds < 60:
                print(f"   ✅ Все источники показывают одинаковое время (разница менее минуты)")
            elif diff_seconds < 3600:
                print(f"   ⚠️ Небольшое расхождение времени (разница {diff_seconds} сек., {diff_seconds / 60:.1f} мин.)")
            else:
                print(f"   ⚠️ Значительное расхождение времени (разница {diff_seconds} сек., {diff_seconds / 3600:.2f} ч.)")
                print(f"      Минимум: {min_seconds / 3600:.2f} ч., Максимум: {max_seconds / 3600:.2f} ч.")
    else:
        print(f"   Нет данных для сравнения")
    
    # Детальное сравнение entrylogs и entrydaystatistics
    print(f"\n" + "=" * 80)
    print("ДЕТАЛЬНОЕ СРАВНЕНИЕ ENTRYLOGS И ENTRYDAYSTATISTICS")
    print("=" * 80)
    
    # Группируем entrylogs по дням
    entrylogs_by_day = {}  # ключ: дата (date), значение: список (entryDate, exitDate, duration_seconds)
    for record in entrylogs_records:
        entry_date = record.get("entryDate")
        exit_date = record.get("exitDate")
        
        if entry_date and exit_date and isinstance(entry_date, datetime) and isinstance(exit_date, datetime):
            if exit_date > entry_date:
                day_key = entry_date.date()
                duration_seconds = int((exit_date - entry_date).total_seconds())
                
                if day_key not in entrylogs_by_day:
                    entrylogs_by_day[day_key] = []
                entrylogs_by_day[day_key].append({
                    "entryDate": entry_date,
                    "exitDate": exit_date,
                    "duration_seconds": duration_seconds
                })
    
    # Группируем entrydaystatistics по дням
    entrydaystats_by_day = {}  # ключ: дата (date), значение: duration в секундах
    for record in entrydaystats_records:
        duration = record.get("duration")
        if duration is None:
            continue
        
        # Определяем дату записи
        record_date = None
        if "date" in record:
            record_date = record.get("date")
        elif "day" in record:
            record_date = record.get("day")
        elif "entryDate" in record:
            record_date = record.get("entryDate")
        
        if record_date:
            if isinstance(record_date, datetime):
                day_key = record_date.date()
            elif isinstance(record_date, str):
                parsed_date = None
                # Формат "MM/DD/YYYY" (например, "10/12/2025")
                try:
                    parsed_date = datetime.strptime(record_date, "%m/%d/%Y")
                except:
                    pass
                # Формат "YYYY-MM-DD"
                if not parsed_date:
                    try:
                        parsed_date = datetime.strptime(record_date[:10], "%Y-%m-%d")
                    except:
                        pass
                # Формат "DD.MM.YYYY"
                if not parsed_date:
                    try:
                        parsed_date = datetime.strptime(record_date[:10], "%d.%m.%Y")
                    except:
                        pass
                
                if parsed_date:
                    day_key = parsed_date.date()
                else:
                    continue
            else:
                continue
            
            # duration в минутах, конвертируем в секунды
            if isinstance(duration, (int, float)):
                duration_seconds = int(duration * 60)
                if day_key not in entrydaystats_by_day:
                    entrydaystats_by_day[day_key] = 0
                entrydaystats_by_day[day_key] += duration_seconds
    
    # Сравнение по дням
    all_days = set(entrylogs_by_day.keys()) | set(entrydaystats_by_day.keys())
    all_days = sorted([d for d in all_days if d.year == 2025])
    
    if all_days:
        print(f"\n📅 Сравнение по дням (топ-20 дней с наибольшими расхождениями):")
        
        day_comparisons = []
        for day in all_days:
            entrylogs_total = sum(r["duration_seconds"] for r in entrylogs_by_day.get(day, []))
            entrydaystats_total = entrydaystats_by_day.get(day, 0)
            entrylogs_count = len(entrylogs_by_day.get(day, []))
            
            diff_seconds = abs(entrylogs_total - entrydaystats_total)
            day_comparisons.append({
                "day": day,
                "entrylogs_seconds": entrylogs_total,
                "entrydaystats_seconds": entrydaystats_total,
                "entrylogs_count": entrylogs_count,
                "diff_seconds": diff_seconds
            })
        
        # Сортируем по разнице (от большего к меньшему)
        day_comparisons.sort(key=lambda x: x["diff_seconds"], reverse=True)
        
        # Показываем топ-20 дней с расхождениями
        shown_count = 0
        for comp in day_comparisons[:20]:
            if comp["diff_seconds"] > 0 or comp["entrylogs_seconds"] > 0 or comp["entrydaystats_seconds"] > 0:
                day_str = comp["day"].strftime("%d.%m.%Y")
                entrylogs_h = comp["entrylogs_seconds"] // 3600
                entrylogs_m = (comp["entrylogs_seconds"] % 3600) // 60
                daystats_h = comp["entrydaystats_seconds"] // 3600
                daystats_m = (comp["entrydaystats_seconds"] % 3600) // 60
                
                status = "✅" if comp["diff_seconds"] < 60 else "⚠️"
                print(f"   {status} {day_str}: entrylogs={entrylogs_h}ч {entrylogs_m}м ({comp['entrylogs_count']} записей), "
                      f"entrydaystats={daystats_h}ч {daystats_m}м, разница={comp['diff_seconds']//60}м")
                shown_count += 1
        
        if shown_count == 0:
            print(f"   ✅ Все дни совпадают (разница менее минуты)")
        
        # Статистика по расхождениям
        days_with_diff = [c for c in day_comparisons if c["diff_seconds"] >= 60]
        days_perfect_match = [c for c in day_comparisons if c["diff_seconds"] < 60]
        days_only_entrylogs = [c for c in day_comparisons if c["entrylogs_seconds"] > 0 and c["entrydaystats_seconds"] == 0]
        days_only_entrydaystats = [c for c in day_comparisons if c["entrylogs_seconds"] == 0 and c["entrydaystats_seconds"] > 0]
        
        print(f"\n   📈 Статистика по дням:")
        print(f"      Всего дней с данными: {len(all_days)}")
        print(f"      Дней с совпадением (разница < 1 мин): {len(days_perfect_match)}")
        print(f"      Дней с расхождениями (разница >= 1 мин): {len(days_with_diff)}")
        print(f"      Дней только в entrylogs: {len(days_only_entrylogs)}")
        print(f"      Дней только в entrydaystatistics: {len(days_only_entrydaystats)}")
        
        if days_with_diff:
            avg_diff = sum(c["diff_seconds"] for c in days_with_diff) / len(days_with_diff)
            max_diff = max(c["diff_seconds"] for c in days_with_diff)
            print(f"      Средняя разница (для дней с расхождениями): {int(avg_diff // 60)} мин.")
            print(f"      Максимальная разница: {int(max_diff // 60)} мин. ({max_diff // 3600:.1f} ч.)")
        
        # Анализ сопоставления через поле entryLogs
        print(f"\n   🔗 Анализ сопоставления через entryLogs:")
        entrylogs_ids_set = {str(record.get("_id")) for record in entrylogs_records}
        entrydaystats_entrylogs_ids = set()
        
        for record in entrydaystats_records:
            entry_logs = record.get("entryLogs")
            if isinstance(entry_logs, list):
                for entry_log_id in entry_logs:
                    if isinstance(entry_log_id, ObjectId):
                        entrydaystats_entrylogs_ids.add(str(entry_log_id))
        
        matched_ids = entrylogs_ids_set & entrydaystats_entrylogs_ids
        only_in_entrylogs = entrylogs_ids_set - entrydaystats_entrylogs_ids
        only_in_entrydaystats = entrydaystats_entrylogs_ids - entrylogs_ids_set
        
        print(f"      Всего записей в entrylogs: {len(entrylogs_ids_set)}")
        print(f"      Всего ID в entrydaystatistics.entryLogs: {len(entrydaystats_entrylogs_ids)}")
        print(f"      Сопоставлено через entryLogs: {len(matched_ids)}")
        print(f"      Только в entrylogs (не найдены в entrydaystatistics.entryLogs): {len(only_in_entrylogs)}")
        print(f"      Только в entrydaystatistics.entryLogs (не найдены в entrylogs): {len(only_in_entrydaystats)}")
        
        if len(entrylogs_ids_set) > 0:
            match_percentage = (len(matched_ids) / len(entrylogs_ids_set)) * 100
            print(f"      Процент сопоставления: {match_percentage:.1f}%")
    else:
        print(f"\n📅 Сравнение по дням: нет данных")
    
    # Сравнение по месяцам
    entrylogs_by_month = {}  # ключ: "YYYY-MM", значение: duration в секундах
    for day, records in entrylogs_by_day.items():
        month_key = day.strftime("%Y-%m")
        if month_key not in entrylogs_by_month:
            entrylogs_by_month[month_key] = 0
        entrylogs_by_month[month_key] += sum(r["duration_seconds"] for r in records)
    
    entrydaystats_by_month = {}  # ключ: "YYYY-MM", значение: duration в секундах
    for day, duration_seconds in entrydaystats_by_day.items():
        month_key = day.strftime("%Y-%m")
        if month_key not in entrydaystats_by_month:
            entrydaystats_by_month[month_key] = 0
        entrydaystats_by_month[month_key] += duration_seconds
    
    all_months = sorted(set(entrylogs_by_month.keys()) | set(entrydaystats_by_month.keys()))
    
    if all_months:
        print(f"\n📅 Сравнение по месяцам:")
        for month_key in all_months:
            entrylogs_total = entrylogs_by_month.get(month_key, 0)
            entrydaystats_total = entrydaystats_by_month.get(month_key, 0)
            diff_seconds = abs(entrylogs_total - entrydaystats_total)
            
            year, month = month_key.split("-")
            month_name = month_names.get(month, month)
            
            entrylogs_h = entrylogs_total // 3600
            entrylogs_m = (entrylogs_total % 3600) // 60
            daystats_h = entrydaystats_total // 3600
            daystats_m = (entrydaystats_total % 3600) // 60
            
            status = "✅" if diff_seconds < 60 else "⚠️"
            print(f"   {status} {month_name} 2025: entrylogs={entrylogs_h}ч {entrylogs_m}м, "
                  f"entrydaystats={daystats_h}ч {daystats_m}м, разница={diff_seconds//60}м ({diff_seconds/3600:.2f}ч)")
    else:
        print(f"\n📅 Сравнение по месяцам: нет данных")
    
    # Общее сравнение
    print(f"\n📊 Общее сравнение:")
    print(f"   entrylogs: {entrylogs_visits_count} записей, {total_duration_entrylogs_seconds} сек. ({total_duration_entrylogs_seconds / 3600:.2f} ч.)")
    print(f"   entrydaystatistics: {len(entrydaystats_records)} записей, {total_duration_entrydaystats_seconds} сек. ({total_duration_entrydaystats / 3600:.2f} ч.)")
    
    if total_duration_entrylogs_seconds > 0 and total_duration_entrydaystats_seconds > 0:
        total_diff = abs(total_duration_entrylogs_seconds - total_duration_entrydaystats_seconds)
        total_diff_hours = total_diff / 3600
        
        if total_diff < 60:
            print(f"   ✅ Общее время совпадает (разница {total_diff} сек.)")
        elif total_diff < 3600:
            print(f"   ⚠️ Небольшое расхождение общего времени: {total_diff} сек. ({total_diff / 60:.1f} мин.)")
        else:
            print(f"   ⚠️ Значительное расхождение общего времени: {total_diff} сек. ({total_diff_hours:.2f} ч.)")
        
        # Процент расхождения
        avg_time = (total_duration_entrylogs_seconds + total_duration_entrydaystats_seconds) / 2
        if avg_time > 0:
            diff_percentage = (total_diff / avg_time) * 100
            print(f"   Процент расхождения: {diff_percentage:.2f}%")
    
    # Сравнение количества записей
    print(f"\n📊 Сравнение количества записей:")
    print(f"   entrylogs: {entrylogs_visits_count} записей")
    print(f"   entrydaystatistics: {len(entrydaystats_records)} записей")
    
    if entrylogs_visits_count != len(entrydaystats_records):
        count_diff = abs(entrylogs_visits_count - len(entrydaystats_records))
        print(f"   ⚠️ Разница в количестве записей: {count_diff}")
        print(f"      (entrylogs может содержать несколько записей на день, entrydaystatistics - одну запись на день)")
    else:
        print(f"   ✅ Количество записей совпадает")
    
    # Ищем первое посещение (сортируем по времени по возрастанию и берем первую запись)
    first_visit = access_col.find_one(
        query,
        {"_id": 1, "user": 1, "time": 1, "type": 1},
        sort=[("time", 1)]  # Сортировка по возрастанию времени
    )
    
    if first_visit:
        visit_time = first_visit.get("time")
        print(f"\n✅ Найдено первое посещение:")
        print(f"   Дата и время: {visit_time.strftime('%d.%m.%Y %H:%M:%S') if visit_time else 'N/A'}")
        print(f"   User ID: {str(first_visit.get('user', ''))}")
        print(f"   Type: {first_visit.get('type', 'N/A')}")
        print(f"   Document ID: {str(first_visit.get('_id', ''))}")
    else:
        print(f"\n⚠️ Посещения не найдены для userID {user_id} с type='enter' за 2025 год")
        print(f"   Количество входов за 2025 год: 0")
        print(f"   Уникальных дней с входами: 0")
        print(f"   Посещения по месяцам: нет данных")
        print(f"   Общее время в клубе: 0")
        
        # Проверяем, есть ли вообще записи для этого пользователя в 2025 году
        query_without_type = {
            "user": user_object_id,
            "time": {
                "$gte": start_date_2025,
                "$lte": end_date_2025
            },
            "err": {"$exists": False}
        }
        total_visits = access_col.count_documents(query_without_type)
        print(f"   Всего посещений в 2025 году (без фильтра по type, без ошибок): {total_visits}")
        
        # Проверяем, есть ли записи с type='enter' в другие годы
        query_other_years = {
            "user": user_object_id,
            "type": "enter",
            "err": {"$exists": False}
        }
        other_years_visits = access_col.count_documents(query_other_years)
        print(f"   Всего посещений с type='enter' (все годы, без ошибок): {other_years_visits}")
    
    # Подсчитываем количество групповых тренировок через events.participantsList
    print(f"\n" + "=" * 80)
    print("ГРУППОВЫЕ ТРЕНИРОВКИ")
    print("=" * 80)
    
    print(f"\n📊 Статистика за 2025 год:")
    
    events_col = get_collection(db, "events")
    
    # Ищем события, где в participantsList есть элемент с user_id и checkedIn: true
    # Используем $elemMatch для поиска в массиве объектов
    # Фильтруем по полю time.start для определения даты события
    # Вариант 1: ищем по полю user в participantsList
    query_events_user = {
        "participantsList": {
            "$elemMatch": {
                "user": user_object_id,
                "checkedIn": True
            }
        },
        "time.start": {"$gte": start_date_2025, "$lte": end_date_2025}
    }
    events_by_user = list(events_col.find(query_events_user))
    
    # Вариант 2: ищем по полю userId в participantsList
    query_events_userid = {
        "participantsList": {
            "$elemMatch": {
                "userId": user_object_id,
                "checkedIn": True
            }
        },
        "time.start": {"$gte": start_date_2025, "$lte": end_date_2025}
    }
    events_by_userid = list(events_col.find(query_events_userid))
    
    # Выбираем вариант с наибольшим количеством результатов
    all_participant_events = []
    user_field = None
    
    if len(events_by_user) >= len(events_by_userid):
        all_participant_events = events_by_user
        user_field = "user"
    else:
        all_participant_events = events_by_userid
        user_field = "userId"
    
    # Если ничего не найдено, пробуем получить все записи и фильтровать в коде
    if not all_participant_events:
        # Пробуем найти события с participantsList и фильтровать в коде
        all_user_events = list(events_col.find({
            "participantsList": {"$exists": True, "$ne": None},
            "time.start": {"$exists": True}
        }))
        
        # Фильтруем по дате и checkedIn в коде
        for event in all_user_events:
            participants_list = event.get("participantsList", [])
            if not isinstance(participants_list, list):
                continue
            
            # Проверяем, есть ли пользователь с checkedIn: true
            user_found = False
            found_user_field = None
            for participant in participants_list:
                if not isinstance(participant, dict):
                    continue
                
                participant_user = participant.get("user")
                participant_userid = participant.get("userId")
                checked_in = participant.get("checkedIn")
                
                # Проверяем оба варианта полей
                if participant_user == user_object_id and checked_in is True:
                    user_found = True
                    found_user_field = "user"
                    break
                elif participant_userid == user_object_id and checked_in is True:
                    user_found = True
                    found_user_field = "userId"
                    break
            
            if not user_found:
                continue
            
            # Проверяем дату через time.start
            event_date = _get_event_date(event)
            if event_date and isinstance(event_date, datetime):
                if start_date_2025 <= event_date <= end_date_2025:
                    all_participant_events.append(event)
                    if found_user_field and not user_field:
                        user_field = found_user_field
    
    total_group_trainings = len(all_participant_events)
    
    # Собираем информацию о групповых тренировках из grouptrainings
    group_trainings_col = get_collection(db, "grouptrainings")
    
    # Собираем все groupTraining ID и подсчитываем посещения за один проход
    group_training_counter = Counter()
    group_training_ids_set = set()
    
    for event in all_participant_events:
        group_training_id = event.get("groupTraining")
        if not group_training_id:
            continue
        
        normalized_id = _normalize_group_training_id(group_training_id)
        if normalized_id:
            id_str = str(normalized_id)
            group_training_counter[id_str] += 1
            group_training_ids_set.add(normalized_id)
    
    group_training_ids = list(group_training_ids_set)
    
    # Получаем информацию о групповых тренировках из коллекции grouptrainings
    group_training_info = {}
    if group_training_ids:
        # Получаем информацию о всех групповых тренировках одним запросом
        group_trainings = list(group_trainings_col.find(
            {"_id": {"$in": group_training_ids}},
            {"name": 1}
        ))
        
        # Создаем словарь для быстрого доступа
        for gt in group_trainings:
            group_training_info[str(gt["_id"])] = gt.get("name", "Неизвестная тренировка")
        
        # Для ID, которые не найдены в БД
        for gt_id in group_training_ids:
            if str(gt_id) not in group_training_info:
                group_training_info[str(gt_id)] = "Тренировка не найдена"
    
    # Группируем по месяцам
    group_trainings_by_month = Counter()
    for event in all_participant_events:
        event_date = _get_event_date(event)
        if event_date and isinstance(event_date, datetime):
            group_trainings_by_month[event_date.strftime("%Y-%m")] += 1
    
    # Выводим статистику
    print(f"   Всего групповых тренировок: {total_group_trainings}")
    
    # Выводим детальную статистику по каждой групповой тренировке
    if group_training_counter:
        print(f"\n   🏋️ По типам тренировок:")
        # Сортируем по количеству посещений (от большего к меньшему)
        sorted_trainings = sorted(group_training_counter.items(), key=lambda x: x[1], reverse=True)
        
        for idx, (gt_id, count) in enumerate(sorted_trainings, 1):
            training_name = group_training_info.get(gt_id, "Неизвестная тренировка")
            print(f"      {idx}. {training_name}: {count} посещений")
        
        # Статистика по уникальным тренировкам
        unique_trainings_count = len(group_training_counter)
        if unique_trainings_count > 0:
            avg_visits = sum(group_training_counter.values()) / unique_trainings_count
            print(f"\n      📈 Статистика:")
            print(f"         Уникальных типов: {unique_trainings_count}")
            print(f"         Среднее на тип: {avg_visits:.1f}")
    else:
        print(f"   🏋️ По типам тренировок: нет данных (в событиях не найдено поле groupTraining)")
    
    # Статистика по месяцам
    if group_trainings_by_month:
        print(f"\n   📅 По месяцам:")
        sorted_months_gt = sorted(group_trainings_by_month.items())
        for month_key, count in sorted_months_gt:
            year, month = month_key.split("-")
            month_name = month_names.get(month, month)
            print(f"      {month_name} 2025: {count} тренировок")
        
        # Самый активный месяц
        if group_trainings_by_month:
            most_active_month, most_active_count = group_trainings_by_month.most_common(1)[0]
            year, month = most_active_month.split("-")
            month_name = month_names.get(month, month)
            print(f"      🏆 Самый активный месяц: {month_name} 2025 ({most_active_count} тренировок)")
    else:
        print(f"   📅 По месяцам: нет данных")
    
    if total_group_trainings == 0:
        print(f"\n⚠️ Групповые тренировки за 2025 год не найдены")
        print(f"   Проверьте наличие записей для userID {user_id} в коллекции events")
        print(f"   с полем participantsList, где есть элемент с user/userId={user_id} и checkedIn: true")
        
        # Пробуем получить пример записи для понимания структуры
        sample_event = events_col.find_one({"participantsList": {"$exists": True, "$ne": None}})
        if sample_event:
            print(f"\n🔍 Структура events (пример записи с participantsList):")
            print(f"   Поля: {list(sample_event.keys())}")
            participants_list = sample_event.get("participantsList")
            if participants_list:
                print(f"   Тип participantsList: {type(participants_list)}")
                if isinstance(participants_list, list) and len(participants_list) > 0:
                    print(f"   Количество участников в примере: {len(participants_list)}")
                    sample_participant = participants_list[0]
                    if isinstance(sample_participant, dict):
                        print(f"   Пример структуры участника: {list(sample_participant.keys())}")
                        print(f"   Пример участника: {sample_participant}")
