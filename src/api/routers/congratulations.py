"""
Роутер для работы с поздравлениями.
Содержит эндпоинты для генерации, отправки и управления поздравлениями.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.core.database import get_db
from src.core.models import Client, Congratulation
from src.core.config import settings
from src.modules.generator.text_generator import get_text_generator
from src.modules.trigger.event_checker import check_today_birthdays

# Создаем роутер
router = APIRouter()


@router.post("/congratulations/generate")
async def generate_congratulation(
    client_id: int = Query(..., description="ID клиента"),
    event_type: str = Query("birthday", description="Тип события (birthday, professional, holiday)"),
    tone: Optional[str] = Query(None, description="Тон поздравления (официальный, дружеский и т.д.)"),
    use_ai: bool = Query(False, description="Использовать AI для генерации"),
    db: Session = Depends(get_db)
):
    """
    Сгенерировать персонализированное поздравление для клиента.
    """
    # Проверяем существование клиента
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Клиент с ID {client_id} не найден")
    
    # Получаем генератор
    generator = get_text_generator(use_ai=use_ai)
    
    try:
        # Генерируем текст
        result = generator.generate_for_client(
            db=db,
            client_id=client_id,
            event_type=event_type,
            tone=tone,
            use_cache=True
        )
        
        return {
            "success": True,
            "congratulation": {
                "text": result["text"],
                "client_id": client_id,
                "client_name": client.full_name,
                "event_type": event_type,
                "generated_at": result["generated_at"],
                "method": result["method"],
                "tone": result["tone"],
                "length": result["length"],
                "preview": result["text"][:100] + "..." if len(result["text"]) > 100 else result["text"]
            },
            "client_info": {
                "id": client.id,
                "name": client.full_name,
                "email": client.email,
                "company": client.company_name,
                "position": client.position,
                "segment": client.segment
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@router.post("/congratulations/generate/batch")
async def generate_batch_congratulations(
    client_ids: List[int] = Query(..., description="Список ID клиентов"),
    event_type: str = Query("birthday", description="Тип события"),
    use_ai: bool = Query(False, description="Использовать AI для генерации"),
    db: Session = Depends(get_db)
):
    """
    Массовая генерация поздравлений для нескольких клиентов.
    """
    if len(client_ids) > 10:
        raise HTTPException(status_code=400, detail="Максимальное количество клиентов за раз: 10")
    
    # Проверяем существование клиентов
    clients = db.query(Client).filter(Client.id.in_(client_ids)).all()
    found_ids = [c.id for c in clients]
    
    # Ищем отсутствующих клиентов
    missing_ids = set(client_ids) - set(found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Клиенты не найдены: {', '.join(map(str, missing_ids))}"
        )
    
    # Получаем генератор
    generator = get_text_generator(use_ai=use_ai)
    
    # Генерируем
    results = generator.batch_generate(db, client_ids, event_type)
    
    return {
        "success": True,
        "total": len(results),
        "successful": sum(1 for r in results if r.get("success", True)),
        "failed": sum(1 for r in results if not r.get("success", True)),
        "results": results
    }


@router.post("/congratulations/generate/today")
async def generate_today_congratulations(
    use_ai: bool = Query(False, description="Использовать AI для генерации"),
    max_clients: int = Query(5, ge=1, le=20, description="Максимальное количество клиентов"),
    db: Session = Depends(get_db)
):
    """
    Автоматическая генерация поздравлений для клиентов с ДР сегодня.
    """
    # Находим клиентов с ДР сегодня
    events = check_today_birthdays(db)
    
    if not events:
        return {
            "success": True,
            "message": "На сегодня нет дней рождения",
            "total": 0,
            "generated": 0
        }
    
    # Ограничиваем количество
    limited_events = events[:max_clients]
    client_ids = [event["client_id"] for event in limited_events]
    
    # Генерируем
    generator = get_text_generator(use_ai=use_ai)
    results = generator.batch_generate(db, client_ids, "birthday")
    
    # Собираем статистику
    successful = []
    failed = []
    
    for result in results:
        if result.get("success", True):
            successful.append({
                "client_id": result["client_id"],
                "client_name": result.get("client_name", "Unknown"),
                "preview": result.get("text", "")[:50] + "..."
            })
        else:
            failed.append({
                "client_id": result["client_id"],
                "error": result.get("error", "Unknown error")
            })
    
    return {
        "success": True,
        "total_clients": len(events),
        "processed": len(limited_events),
        "generated": len(successful),
        "failed": len(failed),
        "successful": successful,
        "failed_list": failed,
        "generated_at": datetime.now().isoformat()
    }


@router.post("/congratulations/send")
async def send_congratulation(
    client_id: int = Query(..., description="ID клиента"),
    text: str = Query(..., description="Текст поздравления"),
    channel: str = Query("email", description="Канал отправки (email, telegram, sms)"),
    save_to_history: bool = Query(True, description="Сохранить в историю"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Отправить поздравление клиенту.
    Пока симулирует отправку, но сохраняет в историю.
    """
    # Проверяем клиента
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail=f"Клиент с ID {client_id} не найден")
    
    # Проверяем текст
    if not text or len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Текст поздравления слишком короткий")
    
    # Определяем статус (симуляция или реальная отправка)
    if channel == "email" and all([
        settings.SMTP_HOST,
        settings.SMTP_USER,
        settings.SMTP_PASSWORD
    ]):
        status = "pending"  # Будет отправлено реально
    else:
        status = "simulated"  # Симуляция
    
    # Создаем запись в истории
    congrat = Congratulation(
        client_id=client_id,
        event_type="birthday",  # TODO: определить тип события
        text=text[:2000],  # Ограничиваем длину для БД
        sent_via=channel,
        status=status,
        sent_at=datetime.now()
    )
    
    db.add(congrat)
    db.commit()
    db.refresh(congrat)
    
    # В фоновом режиме можем выполнить реальную отправку
    if background_tasks and status == "pending":
        # TODO: Реальная отправка через фоновую задачу
        pass
    
    return {
        "success": True,
        "message": f"Поздравление для {client.full_name} отправлено ({status})",
        "congratulation_id": congrat.id,
        "client_email": client.email,
        "channel": channel,
        "status": status,
        "sent_at": congrat.sent_at.isoformat() if congrat.sent_at else None
    }


@router.get("/congratulations")
async def get_congratulations_history(
    skip: int = Query(0, ge=0, description="Смещение"),
    limit: int = Query(50, ge=1, le=100, description="Лимит"),
    client_id: Optional[int] = Query(None, description="Фильтр по ID клиента"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    channel: Optional[str] = Query(None, description="Фильтр по каналу"),
    db: Session = Depends(get_db)
):
    """
    Получить историю отправленных поздравлений.
    """
    query = db.query(Congratulation)
    
    # Применяем фильтры
    if client_id is not None:
        query = query.filter(Congratulation.client_id == client_id)
    
    if status:
        query = query.filter(Congratulation.status == status)
    
    if channel:
        query = query.filter(Congratulation.sent_via == channel)
    
    # Получаем данные
    congratulations = query.order_by(desc(Congratulation.sent_at)).offset(skip).limit(limit).all()
    
    # Получаем информацию о клиентах для отображения
    client_ids = [c.client_id for c in congratulations]
    clients = {c.id: c for c in db.query(Client).filter(Client.id.in_(client_ids)).all()} if client_ids else {}
    
    return {
        "total": query.count(),
        "skip": skip,
        "limit": limit,
        "congratulations": [
            {
                "id": c.id,
                "client_id": c.client_id,
                "client_name": clients.get(c.client_id, Client()).full_name if c.client_id in clients else "Неизвестный клиент",
                "event_type": c.event_type,
                "text_preview": c.text[:100] + "..." if len(c.text) > 100 else c.text,
                "sent_via": c.sent_via,
                "status": c.status,
                "sent_at": c.sent_at.isoformat() if c.sent_at else None,
                "opened": c.opened,
                "opened_at": c.opened_at.isoformat() if c.opened_at else None
            }
            for c in congratulations
        ]
    }


@router.get("/congratulations/{congratulation_id}")
async def get_congratulation_details(
    congratulation_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить детальную информацию о конкретном поздравлении.
    """
    congrat = db.query(Congratulation).filter(Congratulation.id == congratulation_id).first()
    
    if not congrat:
        raise HTTPException(status_code=404, detail=f"Поздравление с ID {congratulation_id} не найдено")
    
    # Получаем информацию о клиенте
    client = db.query(Client).filter(Client.id == congrat.client_id).first()
    
    return {
        "id": congrat.id,
        "client": {
            "id": client.id if client else None,
            "name": client.full_name if client else "Неизвестный клиент",
            "email": client.email if client else None,
            "company": client.company_name if client else None
        } if client else None,
        "event_type": congrat.event_type,
        "text": congrat.text,
        "sent_via": congrat.sent_via,
        "status": congrat.status,
        "sent_at": congrat.sent_at.isoformat() if congrat.sent_at else None,
        "opened": congrat.opened,
        "opened_at": congrat.opened_at.isoformat() if congrat.opened_at else None,
        "created_at": congrat.sent_at.isoformat() if congrat.sent_at else None  # Для совместимости
    }


@router.post("/congratulations/test/generator")
async def test_generator(
    use_ai: bool = Query(False, description="Использовать AI"),
    db: Session = Depends(get_db)
):
    """
    Тестовый эндпоинт для проверки генератора.
    """
    # Получаем случайного клиента
    import random
    clients = db.query(Client).limit(10).all()
    
    if not clients:
        raise HTTPException(status_code=404, detail="Нет клиентов для тестирования")
    
    client = random.choice(clients)
    generator = get_text_generator(use_ai=use_ai)
    
    # Генерируем несколько вариантов
    templates = ["vip", "loyal", "new", "default"]
    results = []
    
    for template in templates:
        # Временно меняем сегмент клиента для теста
        original_segment = client.segment
        client.segment = template.capitalize()
        
        result = generator.generate_for_client(db, client.id, "birthday")
        
        results.append({
            "template": template,
            "segment": client.segment,
            "text_preview": result["text"][:150] + "..." if len(result["text"]) > 150 else result["text"],
            "length": result["length"],
            "tone": result["tone"]
        })
        
        # Восстанавливаем сегмент
        client.segment = original_segment
    
    return {
        "client": {
            "id": client.id,
            "name": client.full_name,
            "original_segment": client.segment
        },
        "test_results": results,
        "generator_mode": "ai" if use_ai else "template"
    }