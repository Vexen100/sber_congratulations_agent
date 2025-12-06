from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from src.core.database import engine, get_db, Base  # <- ВАЖНО!
from src.core.models import Client
import datetime

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sber Congratulations Agent",
    version="1.0.0",
    description="AI-агент для автоматической генерации поздравительных сообщений"
)

# Настройка шаблонов и статики
templates = Jinja2Templates(directory="src/frontend/templates")
app.mount("/static", StaticFiles(directory="src/frontend/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/clients", response_class=HTMLResponse)
async def clients_page(request: Request, db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return templates.TemplateResponse("clients.html", {
        "request": request,
        "clients": clients
    })

@app.get("/api/clients")
async def get_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return {"clients": [
        {
            "id": client.id,
            "name": f"{client.first_name} {client.last_name}",
            "email": client.email,
            "company": client.company,
            "segment": client.segment
        }
        for client in clients
    ]}

@app.get("/api/stats")
async def get_stats():
    return {
        "project": "Sber Congratulations Agent",
        "status": "active_development",
        "version": "1.0.0",
        "modules_ready": 3,
        "total_modules": 15
    }