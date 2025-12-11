"""
Модуль для проверки событий (триггеров).
Обнаруживает дни рождения и другие события для поздравлений.
"""
from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import extract

from src.core.models import Client
from src.core.config import settings


class EventChecker:
    """Класс для проверки событий."""
    
    def __init__(self, db_session: Session):
        """
        Инициализация проверщика событий.
        
        Args:
            db_session: Сессия базы данных SQLAlchemy
        """
        self.db = db_session
    
    def check_birthdays(self, days_ahead: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Находит клиентов с днями рождения в ближайшие N дней.
        
        Args:
            days_ahead: Количество дней для проверки (по умолчанию из настроек)
            
        Returns:
            Список событий с информацией о клиентах
        """
        if days_ahead is None:
            days_ahead = settings.BIRTHDAY_DAYS_AHEAD
        
        today = date.today()
        events = []
        
        # Получаем всех клиентов
        clients = self.db.query(Client).all()
        
        for client in clients:
            # Вычисляем дату дня рождения в текущем году
            birthday_this_year = client.birthday.replace(year=today.year)
            
            # Если день рождения уже прошел в этом году, берем следующий год
            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)
            
            # Проверяем, попадает ли в диапазон
            days_until = (birthday_this_year - today).days
            
            if 0 <= days_until <= days_ahead:
                event = {
                    "type": "birthday",
                    "client_id": client.id,
                    "client_name": client.full_name,
                    "client_email": client.email,
                    "client_segment": client.segment,
                    "birthday": client.birthday.isoformat(),
                    "upcoming_date": birthday_this_year.isoformat(),
                    "days_until": days_until,
                    "is_today": days_until == 0,
                    "priority": self._calculate_priority(client, days_until),
                    "metadata": {
                        "company": client.company_name,
                        "position": client.position,
                        "phone": client.phone
                    }
                }
                events.append(event)
        
        # Сортируем по приоритету и дате
        events.sort(key=lambda x: (x["priority"], x["days_until"]))
        
        return events
    
    def check_today_birthdays(self) -> List[Dict[str, Any]]:
        """
        Находит клиентов с днями рождения сегодня.
        
        Returns:
            Список клиентов с ДР сегодня
        """
        today = date.today()
        
        events = []
        for client in self.db.query(Client).all():
            if client.birthday.month == today.month and client.birthday.day == today.day:
                event = {
                    "type": "birthday",
                    "client_id": client.id,
                    "client_name": client.full_name,
                    "client_email": client.email,
                    "client_segment": client.segment,
                    "birthday": client.birthday.isoformat(),
                    "days_until": 0,
                    "is_today": True,
                    "priority": "high",
                    "metadata": {
                        "company": client.company_name,
                        "position": client.position,
                        "phone": client.phone
                    }
                }
                events.append(event)
        
        return events
    
    def check_birthdays_by_date(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Находит клиентов с днями рождения в конкретную дату.
        
        Args:
            target_date: Дата для проверки
            
        Returns:
            Список клиентов с ДР в указанную дату
        """
        events = []
        for client in self.db.query(Client).all():
            if client.birthday.month == target_date.month and client.birthday.day == target_date.day:
                event = {
                    "type": "birthday",
                    "client_id": client.id,
                    "client_name": client.full_name,
                    "client_email": client.email,
                    "client_segment": client.segment,
                    "birthday": client.birthday.isoformat(),
                    "target_date": target_date.isoformat(),
                    "priority": self._calculate_priority(client, 0),
                    "metadata": {
                        "company": client.company_name,
                        "position": client.position,
                        "phone": client.phone
                    }
                }
                events.append(event)
        
        return events
    
    def _calculate_priority(self, client: Client, days_until: int) -> str:
        """
        Вычисляет приоритет события.
        
        Args:
            client: Объект клиента
            days_until: Сколько дней до события
            
        Returns:
            Приоритет: "high", "medium" или "low"
        """
        # Если сегодня ДР
        if days_until == 0:
            return "high"
        
        # VIP клиенты имеют высокий приоритет
        if client.segment == "VIP" and days_until <= 3:
            return "high"
        
        # Лояльные клиенты - средний приоритет
        if client.segment == "Лояльный" and days_until <= 2:
            return "medium"
        
        # Для остальных - низкий приоритет или по умолчанию
        if days_until <= 1:
            return "medium"
        
        return "low"
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Возвращает статистику по событиям.
        
        Returns:
            Словарь со статистикой
        """
        today = date.today()
        
        # Подсчитываем клиентов
        total_clients = self.db.query(Client).count()
        
        # Дни рождения сегодня
        today_birthdays = len(self.check_today_birthdays())
        
        # Дни рождения на этой неделе
        week_birthdays = len(self.check_birthdays(days_ahead=7))
        
        # Распределение по сегментам
        segments = {}
        for client in self.db.query(Client).all():
            seg = client.segment or "Не указан"
            segments[seg] = segments.get(seg, 0) + 1
        
        return {
            "total_clients": total_clients,
            "birthdays_today": today_birthdays,
            "birthdays_this_week": week_birthdays,
            "segments": segments,
            "checked_at": date.today().isoformat()
        }


# Функции для удобного использования
def check_today_birthdays(db: Session) -> List[Dict[str, Any]]:
    """Проверяет дни рождения на сегодня."""
    checker = EventChecker(db)
    return checker.check_today_birthdays()


def check_upcoming_birthdays(db: Session, days_ahead: Optional[int] = None) -> List[Dict[str, Any]]:
    """Проверяет дни рождения на ближайшие N дней."""
    checker = EventChecker(db)
    return checker.check_birthdays(days_ahead)


def get_events_statistics(db: Session) -> Dict[str, Any]:
    """Возвращает статистику по событиям."""
    checker = EventChecker(db)
    return checker.get_statistics()


if __name__ == "__main__":
    # Тестирование модуля
    from src.core.database import SessionLocal
    
    print("🧪 Тестирование модуля event_checker...")
    
    db = SessionLocal()
    try:
        checker = EventChecker(db)
        
        print("1. Проверка дней рождения сегодня:")
        today_events = checker.check_today_birthdays()
        print(f"   Найдено: {len(today_events)}")
        for event in today_events[:3]:  # Показываем первые 3
            print(f"   - {event['client_name']} ({event['client_email']})")
        
        print("\n2. Проверка дней рождения на неделю:")
        week_events = checker.check_birthdays(days_ahead=7)
        print(f"   Найдено: {len(week_events)}")
        
        print("\n3. Статистика:")
        stats = checker.get_statistics()
        print(f"   Всего клиентов: {stats['total_clients']}")
        print(f"   ДР сегодня: {stats['birthdays_today']}")
        print(f"   ДР на неделе: {stats['birthdays_this_week']}")
        print(f"   Сегменты: {stats['segments']}")
        
    finally:
        db.close()