"""
Зависимости для FastAPI приложения.
Обеспечивает доступ к базе данных и другим ресурсам.
"""
from typing import Generator
from sqlalchemy.orm import Session

from src.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Зависимость для получения сессии базы данных.
    
    Использование:
    ```python
    @app.get("/items")
    def read_items(db: Session = Depends(get_db)):
        # используем db
    ```
    
    Yields:
        Session: Сессия SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Можно добавить другие зависимости позже:
# - get_current_user для аутентификации
# - get_settings для конфигурации
# - и т.д.