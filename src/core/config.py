"""
Конфигурация приложения.
Использует pydantic-settings для загрузки переменных окружения.
"""
import os
from pathlib import Path
from typing import Optional, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Базовые пути
    BASE_DIR: ClassVar[Path] = Path(__file__).parent.parent.parent
    ENV_FILE: ClassVar[Path] = BASE_DIR / ".env"
    
    # База данных
    DATABASE_URL: str = "sqlite:///./congratulations.db"
    
    # API ключи (будут добавлены позже)
    GIGACHAT_API_KEY: Optional[str] = None
    KANDINSKY_API_KEY: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    
    # SMTP настройки (будут добавлены позже)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # Настройки приложения
    DEBUG: bool = True
    USE_REAL_AI: bool = False  # Пока используем заглушки
    BIRTHDAY_DAYS_AHEAD: int = 7
    DEFAULT_TONE: str = "дружеский"
    
    # Конфигурация pydantic
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Игнорируем лишние переменные
    )


# Глобальный экземпляр настроек
settings = Settings()