"""
Роутер для работы с клиентами.
Содержит эндпоинты для CRUD операций и получения информации о клиентах.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.core.database import get_db
from src.core.models import Client, Congratulation

# Создаем роутер
router = APIRouter()


@router.get("/clients", response_model=List[dict])
async def get_clients(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Лимит записей"),
    search: Optional[str] = Query(None, description="Поиск по имени или email"),
    segment: Optional[str] = Query(None, description="Фильтр по сегменту (VIP, Лояльный, Новый)"),
    db: Session = Depends(get_db)
):
    """
    Получить список клиентов с пагинацией и фильтрацией.
    """
    query = db.query(Client)
    
    # Применяем поиск
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Client.first_name.ilike(search_term),
                Client.last_name.ilike(search_term),
                Client.email.ilike(search_term),
                Client.company_name.ilike(search_term)
            )
        )
    
    # Фильтр по сегменту
    if segment:
        query = query.filter(Client.segment == segment)
    
    # Применяем пагинацию
    clients = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": client.id,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "full_name": client.full_name,
            "email": client.email,
            "phone": client.phone,
            "birthday": client.birthday.isoformat(),
            "company": client.company_name,
            "position": client.position,
            "segment": client.segment,
            "created_at": client.created_at.isoformat() if client.created_at else None,
        }
        for client in clients
    ]


@router.get("/clients/{client_id}")
async def get_client(client_id: int, db: Session = Depends(get_db)):
    """
    Получить детальную информацию о клиенте по ID.
    """
    client = db.query(Client).filter(Client.id == client_id).first()
    
    if not client:
        raise HTTPException(status_code=404, detail=f"Клиент с ID {client_id} не найден")
    
    # Получаем историю поздравлений для этого клиента
    congratulations = db.query(Congratulation).filter(
        Congratulation.client_id == client_id
    ).order_by(Congratulation.sent_at.desc()).limit(10).all()
    
    return {
        "client": {
            "id": client.id,
            "first_name": client.first_name,
            "last_name": client.last_name,
            "full_name": client.full_name,
            "email": client.email,
            "phone": client.phone,
            "birthday": client.birthday.isoformat(),
            "company": client.company_name,
            "position": client.position,
            "segment": client.segment,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None,
        },
        "congratulations_history": [
            {
                "id": c.id,
                "event_type": c.event_type,
                "sent_via": c.sent_via,
                "sent_at": c.sent_at.isoformat() if c.sent_at else None,
                "status": c.status
            }
            for c in congratulations
        ],
        "total_congratulations": len(congratulations)
    }


@router.get("/clients/birthdays/upcoming")
async def get_upcoming_birthdays(
    days: int = Query(7, ge=1, le=365, description="Количество дней для поиска"),
    db: Session = Depends(get_db)
):
    """
    Получить список клиентов с днями рождения в ближайшие N дней.
    """
    today = date.today()
    
    # Находим всех клиентов
    all_clients = db.query(Client).all()
    
    upcoming = []
    for client in all_clients:
        # Вычисляем дату рождения в текущем году
        birthday_this_year = client.birthday.replace(year=today.year)
        
        # Если день рождения уже прошел в этом году, берем следующий год
        if birthday_this_year < today:
            birthday_this_year = birthday_this_year.replace(year=today.year + 1)
        
        # Проверяем, попадает ли в диапазон
        days_until = (birthday_this_year - today).days
        if 0 <= days_until <= days:
            upcoming.append({
                "client_id": client.id,
                "full_name": client.full_name,
                "email": client.email,
                "birthday": client.birthday.isoformat(),
                "upcoming_date": birthday_this_year.isoformat(),
                "days_until": days_until,
                "is_today": days_until == 0,
                "segment": client.segment
            })
    
    # Сортируем по ближайшим датам
    upcoming.sort(key=lambda x: x["days_until"])
    
    return {
        "period_days": days,
        "today": today.isoformat(),
        "total": len(upcoming),
        "clients": upcoming
    }


@router.get("/clients/birthdays/today")
async def get_today_birthdays(db: Session = Depends(get_db)):
    """
    Получить список клиентов с днями рождения сегодня.
    """
    today = date.today()
    
    clients_today = []
    for client in db.query(Client).all():
        if client.birthday.month == today.month and client.birthday.day == today.day:
            clients_today.append({
                "client_id": client.id,
                "full_name": client.full_name,
                "email": client.email,
                "birthday": client.birthday.isoformat(),
                "segment": client.segment,
                "company": client.company_name,
                "position": client.position
            })
    
    return {
        "date": today.isoformat(),
        "total": len(clients_today),
        "clients": clients_today
    }


@router.post("/clients")
async def create_client(
    client_data: dict,
    db: Session = Depends(get_db)
):
    """
    Создать нового клиента.
    Временный эндпоинт для тестирования.
    """
    # Валидация данных
    required_fields = ["first_name", "last_name", "email", "birthday"]
    for field in required_fields:
        if field not in client_data:
            raise HTTPException(status_code=400, detail=f"Поле {field} обязательно")
    
    try:
        # Парсим дату рождения
        birthday = date.fromisoformat(client_data["birthday"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный формат даты. Используйте YYYY-MM-DD")
    
    # Проверяем, нет ли уже клиента с таким email
    existing_client = db.query(Client).filter(Client.email == client_data["email"]).first()
    if existing_client:
        raise HTTPException(status_code=400, detail="Клиент с таким email уже существует")
    
    # Создаем клиента
    client = Client(
        first_name=client_data["first_name"],
        last_name=client_data["last_name"],
        email=client_data["email"],
        birthday=birthday,
        phone=client_data.get("phone"),
        company_name=client_data.get("company_name"),
        position=client_data.get("position"),
        segment=client_data.get("segment", "Новый")
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return {
        "message": "Клиент успешно создан",
        "client_id": client.id,
        "full_name": client.full_name
    }


# Экспортируем роутер
__all__ = ["router"]