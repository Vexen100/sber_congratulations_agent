"""
Основное приложение FastAPI.
Точка входа для всего API.
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from src.core.config import settings
from .dependencies import get_db
from .routers import clients  # будем создавать в следующем файле
from .routers import congratulations

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request

# Настройка шаблонов
templates = Jinja2Templates(directory="src/frontend/templates")

# Создаем экземпляр FastAPI приложения
app = FastAPI(
    title="Sber Congratulations Agent API",
    description="API для автоматической отправки персонализированных поздравлений",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,  # Swagger только в режиме отладки
    redoc_url="/redoc" if settings.DEBUG else None,  # ReDoc только в режиме отладки
)

# Монтируем статические файлы (если будут)
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

# Добавляем роутеры для веб-страниц
@app.get("/", response_class=HTMLResponse)
async def web_index(request: Request):
    from src.core.config import settings
    from src.modules.sender.email_sender import EmailSender
    
    sender = EmailSender()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "debug_mode": settings.DEBUG,
        "smtp_configured": sender.is_configured
    })

@app.get("/clients", response_class=HTMLResponse)
async def web_clients(request: Request):
    return templates.TemplateResponse("clients.html", {"request": request})

@app.get("/send", response_class=HTMLResponse)
async def web_send(request: Request):
    return templates.TemplateResponse("send.html", {"request": request})

@app.get("/congratulations", response_class=HTMLResponse)
async def web_congratulations(request: Request):
    return templates.TemplateResponse("congratulations.html", {"request": request})

# Настраиваем CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],  # В продакшене нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(clients.router, prefix="/api/v1", tags=["clients"])
app.include_router(congratulations.router, prefix="/api/v1", tags=["congratulations"])

# Базовые эндпоинты
@app.get("/")
async def root():
    """
    Корневой эндпоинт.
    Возвращает информацию о сервисе.
    """
    return {
        "service": "Sber Congratulations Agent",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs" if settings.DEBUG else "disabled in production"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Проверка здоровья системы.
    Проверяет доступность базы данных и других сервисов.
    """
    try:
        # Проверяем соединение с БД
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "mode": "development" if settings.DEBUG else "production"
    }


@app.get("/config")
async def show_config():
    """
    Показывает текущую конфигурацию (только в режиме отладки).
    """
    if not settings.DEBUG:
        raise HTTPException(status_code=403, detail="Configuration endpoint is disabled in production")
    
    return {
        "debug": settings.DEBUG,
        "database_url": settings.DATABASE_URL[:50] + "..." if len(settings.DATABASE_URL) > 50 else settings.DATABASE_URL,
        "use_real_ai": settings.USE_REAL_AI,
        "birthday_days_ahead": settings.BIRTHDAY_DAYS_AHEAD,
    }

@app.get("/clients", response_class=HTMLResponse)
async def web_clients(request: Request):
    return templates.TemplateResponse("clients.html", {"request": request})

@app.get("/send", response_class=HTMLResponse)
async def web_send(request: Request):
    return templates.TemplateResponse("send.html", {"request": request})

@app.get("/congratulations", response_class=HTMLResponse)
async def web_congratulations(request: Request):
    return templates.TemplateResponse("congratulations.html", {"request": request})


# Точка входа для запуска приложения напрямую
if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning"
    )