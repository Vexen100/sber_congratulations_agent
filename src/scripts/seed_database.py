from src.core.database import SessionLocal, engine, Base
from src.core.models import Client
import datetime

# Создаем таблицы
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Тестовые клиенты
test_clients = [
    Client(
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        birthday=datetime.date(1990, 3, 15),
        company="ООО ТехноПром",
        segment="VIP"
    ),
    Client(
        first_name="Мария",
        last_name="Петрова",
        email="maria@example.com",
        birthday=datetime.date(1985, 5, 22),
        company="АО Весна",
        segment="лояльный"
    ),
    Client(
        first_name="Алексей",
        last_name="Сидоров",
        email="alex@example.com",
        birthday=datetime.date(1978, 11, 30),
        company="ПАО Газпром",
        segment="новый"
    ),
    Client(
        first_name="Екатерина",
        last_name="Смирнова",
        email="ekaterina@example.com",
        birthday=datetime.date(1992, 7, 8),
        company="Яндекс",
        segment="VIP"
    ),
    Client(
        first_name="Дмитрий",
        last_name="Кузнецов",
        email="dmitry@example.com",
        birthday=datetime.date(1980, 9, 14),
        company="Сбер",
        segment="лояльный"
    ),
]

try:
    db.add_all(test_clients)
    db.commit()
    print(f"✅ Добавлено {len(test_clients)} тестовых клиентов")
    print("Примеры клиентов:")
    for client in test_clients:
        print(f"  - {client.first_name} {client.last_name} ({client.company})")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    db.rollback()
finally:
    db.close()