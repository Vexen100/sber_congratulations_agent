"""
Скрипт для заполнения базы данных тестовыми данными.
Запустите этот скрипт, чтобы добавить тестовых клиентов.
"""
import sys
import random
from datetime import date, timedelta
from pathlib import Path

# Добавляем корень проекта в путь Python
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session

from src.core.database import SessionLocal, engine
from src.core.models import Client, Congratulation
from src.core.config import settings


def clear_database(db: Session):
    """Очистить базу данных от старых данных."""
    print("🧹 Очищаем базу данных...")
    db.query(Congratulation).delete()
    db.query(Client).delete()
    db.commit()
    print("✅ База данных очищена")


def create_test_clients(db: Session, count: int = 20):
    """Создать тестовых клиентов."""
    print(f"👥 Создаем {count} тестовых клиентов...")
    
    # Списки для генерации случайных данных
    first_names = ["Иван", "Анна", "Алексей", "Мария", "Дмитрий", "Екатерина", "Сергей", "Ольга", "Андрей", "Наталья"]
    last_names = ["Иванов", "Петрова", "Сидоров", "Смирнова", "Кузнецов", "Васильева", "Попов", "Новикова", "Федоров", "Морозова"]
    companies = ["ООО 'Рога и Копыта'", "АО 'СтройГрад'", "ИП 'ТехноПрофи'", "ЗАО 'МеталлПром'", 
                 "ОАО 'НефтеГаз'", "ООО 'ИТ-Сервис'", "АО 'БанкСтандарт'", "ИП 'РозничнаяСеть'"]
    positions = ["Генеральный директор", "Финансовый директор", "Технический директор", "Коммерческий директор", 
                 "Менеджер по продажам", "Бухгалтер", "Инженер", "Аналитик"]
    segments = ["VIP", "Лояльный", "Новый"]
    
    clients = []
    today = date.today()
    
    for i in range(count):
        # Генерируем случайные данные
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        # Генерируем email
        email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
        
        # Генерируем дату рождения:
        # - 2 клиента с ДР сегодня
        # - 3 клиента с ДР завтра
        # - 5 клиентов с ДР на этой неделе
        # - Остальные - случайные даты
        if i < 2:
            birthday = today  # Сегодня
        elif i < 5:
            birthday = today + timedelta(days=1)  # Завтра
        elif i < 10:
            days_ahead = random.randint(2, 7)
            birthday = today + timedelta(days=days_ahead)  # На этой неделе
        else:
            # Случайная дата за последние 20-60 лет
            years_ago = random.randint(20, 60)
            random_date = today - timedelta(days=365 * years_ago)
            # Устанавливаем случайный день и месяц
            birthday = date(random_date.year, random.randint(1, 12), random.randint(1, 28))
        
        client = Client(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=f"+7916{random.randint(1000000, 9999999)}",
            company_name=random.choice(companies),
            position=random.choice(positions),
            segment=random.choice(segments),
            birthday=birthday
        )
        
        clients.append(client)
    
    db.add_all(clients)
    db.commit()
    
    print(f"✅ Создано {len(clients)} тестовых клиентов")
    
    # Выводим статистику
    print("\n📊 Статистика клиентов:")
    print(f"   - С ДР сегодня: {sum(1 for c in clients if c.birthday.month == today.month and c.birthday.day == today.day)}")
    print(f"   - С ДР завтра: {sum(1 for c in clients if c.birthday.month == today.month and c.birthday.day == (today.day + 1))}")
    print(f"   - С ДР на этой неделе: {sum(1 for c in clients if 0 <= (date(today.year, c.birthday.month, c.birthday.day) - today).days <= 7)}")
    
    return clients


def create_test_congratulations(db: Session, clients):
    """Создать тестовые отправленные поздравления."""
    print("\n🎉 Создаем тестовую историю поздравлений...")
    
    congratulations = []
    event_types = ["birthday", "holiday", "professional"]
    sent_via_options = ["email", "telegram", "sms"]
    status_options = ["sent", "simulated", "failed"]
    
    # Для каждого клиента создаем 0-3 поздравлений
    for client in clients[:10]:  # Только для первых 10 клиентов
        num_congrats = random.randint(0, 3)
        
        for _ in range(num_congrats):
            # Случайная дата в прошлом
            days_ago = random.randint(1, 365)
            sent_date = date.today() - timedelta(days=days_ago)
            
            congrat = Congratulation(
                client_id=client.id,
                event_type=random.choice(event_types),
                text=f"Тестовое поздравление для {client.first_name} {client.last_name}",
                sent_via=random.choice(sent_via_options),
                sent_at=sent_date,
                status=random.choice(status_options),
                opened=random.choice([True, False])
            )
            
            if congrat.opened:
                congrat.opened_at = sent_date + timedelta(hours=random.randint(1, 24))
            
            congratulations.append(congrat)
    
    db.add_all(congratulations)
    db.commit()
    
    print(f"✅ Создано {len(congratulations)} тестовых поздравлений")


def main():
    """Основная функция."""
    print("=" * 60)
    print("📦 ЗАПОЛНЕНИЕ БАЗЫ ДАННЫХ ТЕСТОВЫМИ ДАННЫМИ")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Спрашиваем подтверждение
        response = input("Очистить существующие данные и создать тестовые? (y/N): ")
        if response.lower() != 'y':
            print("❌ Операция отменена")
            return
        
        # Выполняем
        clear_database(db)
        clients = create_test_clients(db, count=20)
        create_test_congratulations(db, clients)
        
        print("\n" + "=" * 60)
        print("✅ БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!")
        print("\n🎯 Дальнейшие действия:")
        print("1. Проверьте API: http://localhost:8000/api/v1/clients")
        print("2. Проверьте дни рождения: http://localhost:8000/api/v1/clients/birthdays/today")
        print("3. Проверьте Swagger: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()