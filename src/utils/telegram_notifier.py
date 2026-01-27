"""
Модуль для отправки результатов тестов в Telegram.
Поддерживает отправку в разные топики супергруппы в зависимости от категории теста.
"""

import os
import requests
from typing import Optional, Dict, Any
from datetime import datetime


# Конфигурация топиков по категориям тестов
TOPIC_MAPPING = {
    "personal_trainings": 2,  # Тесты персональных тренировок
    "payment": 10,             # Тесты платежей
    "notifications": 4,        # Общие уведомления и остальные тесты
}


class TelegramNotifier:
    """Класс для отправки уведомлений в Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Инициализация notifier.
        
        Args:
            bot_token: Токен Telegram бота
            chat_id: ID чата/группы для отправки сообщений
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(
        self, 
        message: str, 
        thread_id: Optional[int] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        """
        Отправка сообщения в Telegram.
        
        Args:
            message: Текст сообщения
            thread_id: ID топика (для супергрупп с Topics)
            parse_mode: Режим парсинга (HTML или Markdown)
        
        Returns:
            True если отправка успешна, False иначе
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        if thread_id:
            payload["message_thread_id"] = thread_id
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка отправки в Telegram: {e}")
            return False
    
    def determine_topic_id(self, test_file_path: str) -> int:
        """
        Определение ID топика на основе пути к тестовому файлу.
        
        Args:
            test_file_path: Путь к файлу с тестом
        
        Returns:
            ID топика для отправки
        """
        test_file_path_lower = test_file_path.lower()
        
        # Проверка на personal_trainings
        if "personal_training" in test_file_path_lower:
            return TOPIC_MAPPING["personal_trainings"]
        
        # Проверка на payment
        if "payment" in test_file_path_lower:
            return TOPIC_MAPPING["payment"]
        
        # По умолчанию - notifications
        return TOPIC_MAPPING["notifications"]
    
    def format_test_results(
        self,
        passed: int,
        failed: int,
        skipped: int,
        errors: int,
        duration: float,
        category: str = "Все тесты",
        report_url: Optional[str] = None
    ) -> str:
        """
        Форматирование результатов тестов для отправки.
        
        Args:
            passed: Количество пройденных тестов
            failed: Количество упавших тестов
            skipped: Количество пропущенных тестов
            errors: Количество тестов с ошибками
            duration: Время выполнения (в секундах)
            category: Категория тестов
            report_url: Ссылка на полный отчёт
        
        Returns:
            Отформатированное сообщение
        """
        total = passed + failed + skipped + errors
        status_emoji = "✅" if failed == 0 and errors == 0 else "❌"
        
        # Форматирование времени
        if duration < 60:
            time_str = f"{duration:.2f}с"
        else:
            minutes = int(duration // 60)
            seconds = duration % 60
            time_str = f"{minutes}м {seconds:.2f}с"
        
        # Форматирование даты и времени
        now = datetime.now()
        date_str = now.strftime("%d.%m.%Y %H:%M")
        
        message = f"{status_emoji} <b>Результаты тестов: {category}</b>\n\n"
        message += f"📊 <b>Статистика:</b>\n"
        message += f"  • Всего: {total}\n"
        message += f"  • ✅ Пройдено: {passed}\n"
        
        if failed > 0:
            message += f"  • ❌ Упало: {failed}\n"
        if skipped > 0:
            message += f"  • ⏭ Пропущено: {skipped}\n"
        if errors > 0:
            message += f"  • 🔥 Ошибки: {errors}\n"
        
        message += f"\n⏱ <b>Время выполнения:</b> {time_str}\n"
        message += f"📅 <b>Дата:</b> {date_str}"
        
        # Добавляем ссылку на отчёт, если она передана
        if report_url:
            message += f"\n\n📊 <a href='{report_url}'>Открыть полный отчёт</a>"
        
        return message
    
    def send_test_results(
        self,
        passed: int,
        failed: int,
        skipped: int,
        errors: int,
        duration: float,
        test_file_path: str = "",
        category: str = "Все тесты",
        report_url: Optional[str] = None
    ) -> bool:
        """
        Отправка результатов тестов в соответствующий топик.
        
        Args:
            passed: Количество пройденных тестов
            failed: Количество упавших тестов
            skipped: Количество пропущенных тестов
            errors: Количество тестов с ошибками
            duration: Время выполнения
            test_file_path: Путь к файлу с тестом (для определения топика)
            category: Категория тестов (для отображения)
            report_url: Ссылка на полный отчёт
        
        Returns:
            True если отправка успешна
        """
        topic_id = self.determine_topic_id(test_file_path)
        message = self.format_test_results(
            passed, failed, skipped, errors, duration, category, report_url
        )
        return self.send_message(message, thread_id=topic_id)


def get_telegram_notifier() -> Optional[TelegramNotifier]:
    """
    Создание экземпляра TelegramNotifier из переменных окружения.
    
    Returns:
        TelegramNotifier или None если настройки не заданы
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        return None
    
    return TelegramNotifier(bot_token, chat_id)


def send_test_notification(
    passed: int,
    failed: int,
    skipped: int,
    errors: int,
    duration: float,
    test_file_path: str = "",
    category: str = "Все тесты",
    report_url: Optional[str] = None
) -> bool:
    """
    Удобная функция для отправки результатов тестов.
    
    Args:
        passed: Количество пройденных тестов
        failed: Количество упавших тестов
        skipped: Количество пропущенных тестов
        errors: Количество тестов с ошибками
        duration: Время выполнения
        test_file_path: Путь к файлу с тестом
        category: Категория тестов
        report_url: Ссылка на полный отчёт (Allure или другой)
    
    Returns:
        True если отправка успешна, False иначе
    """
    notifier = get_telegram_notifier()
    if not notifier:
        print("⚠️ Telegram notifier не настроен (отсутствуют переменные окружения)")
        return False
    
    return notifier.send_test_results(
        passed, failed, skipped, errors, duration, test_file_path, category, report_url
    )
