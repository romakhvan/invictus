"""
Утилиты для работы с тестовыми данными.
"""

from typing import Dict, Any
import random
import string
from datetime import datetime, timedelta


class TestDataGenerator:
    """Генератор тестовых данных."""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Генерация случайной строки."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    @staticmethod
    def random_email(domain: str = "test.com") -> str:
        """Генерация случайного email."""
        username = TestDataGenerator.random_string(8)
        return f"{username}@{domain}"
    
    @staticmethod
    def random_phone() -> str:
        """Генерация случайного номера телефона."""
        return f"+7{random.randint(9000000000, 9999999999)}"
    
    @staticmethod
    def random_date(start_date: datetime = None, days_range: int = 365) -> datetime:
        """Генерация случайной даты."""
        if start_date is None:
            start_date = datetime.now()
        random_days = random.randint(0, days_range)
        return start_date + timedelta(days=random_days)


class TestUsers:
    """Тестовые пользователи для UI тестов."""
    
    # Примеры тестовых пользователей
    # ВАЖНО: Замените на реальные тестовые данные вашего приложения
    ADMIN = {
        "username": "admin",
        "password": "admin123",
        "email": "admin@test.com"
    }
    
    REGULAR_USER = {
        "username": "testuser",
        "password": "testpass123",
        "email": "testuser@test.com"
    }
    
    COACH = {
        "username": "coach",
        "password": "coach123",
        "email": "coach@test.com"
    }
    
    @classmethod
    def get_user(cls, user_type: str = "regular") -> Dict[str, str]:
        """
        Получить тестового пользователя по типу.
        
        Args:
            user_type: Тип пользователя (admin, regular, coach)
        
        Returns:
            Словарь с данными пользователя
        """
        users = {
            "admin": cls.ADMIN,
            "regular": cls.REGULAR_USER,
            "coach": cls.COACH
        }
        return users.get(user_type, cls.REGULAR_USER)


class TestConfig:
    """Конфигурация для тестов."""
    
    # Таймауты
    DEFAULT_TIMEOUT = 10
    LONG_TIMEOUT = 30
    SHORT_TIMEOUT = 5
    
    # Повторные попытки
    MAX_RETRIES = 3
    RETRY_DELAY = 1
    
    # Тестовые данные
    TEST_DOMAIN = "test.com"
    TEST_PREFIX = "autotest_"

