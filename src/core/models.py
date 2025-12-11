"""
Модели базы данных (SQLAlchemy).
Содержит минимальный набор таблиц для начала.
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Boolean
from sqlalchemy.sql import func
from datetime import datetime

from .database import Base  # Импортируем Base из database.py


class Client(Base):
    """
    Модель клиента.
    Содержит основную информацию о клиенте для поздравлений.
    """
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Основная информация
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Информация о компании
    company_name = Column(String(255))
    position = Column(String(100))
    
    # Сегментация
    segment = Column(String(50), default="Новый")  # VIP, Лояльный, Новый
    
    # Даты
    birthday = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Методы для удобства
    @property
    def full_name(self) -> str:
        """Полное имя клиента."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.full_name}', email='{self.email}')>"


class Congratulation(Base):
    """
    Модель отправленного поздравления.
    Хранит историю всех отправленных поздравлений.
    """
    __tablename__ = "congratulations"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с клиентом
    client_id = Column(Integer, index=True, nullable=False)
    
    # Информация о поздравлении
    event_type = Column(String(50), default="birthday")  # birthday, holiday, professional
    text = Column(Text, nullable=False)
    
    # Канал отправки
    sent_via = Column(String(50), default="email")  # email, telegram, sms
    
    # Статус
    status = Column(String(50), default="pending")  # pending, sent, failed, simulated
    
    # Даты
    sent_at = Column(DateTime, server_default=func.now())
    
    # Для аналитики (позже)
    opened = Column(Boolean, default=False)
    opened_at = Column(DateTime, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Congratulation(id={self.id}, client_id={self.client_id}, status='{self.status}')>"


# Экспортируем все модели
__all__ = ["Client", "Congratulation"]