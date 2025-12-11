"""
Подключение к базе данных.
Создает движок SQLAlchemy и сессии.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from .config import settings


# Создаем движок базы данных
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Выводим SQL запросы в режиме отладки
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Базовый класс для моделей
Base = declarative_base()


def get_db() -> Generator:
    """
    Генератор для получения сессии БД.
    Используется как зависимость в FastAPI.
    
    Yields:
        Session: Сессия SQLAlchemy
        
    Пример:
        ```python
        db = next(get_db())
        # используем db
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Функция для создания таблиц
def create_tables() -> None:
    """Создает все таблицы в базе данных."""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Таблицы созданы в {settings.DATABASE_URL}")