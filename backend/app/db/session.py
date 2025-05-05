from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


# --- Создание "движка" SQLAlchemy (Engine) ---
engine = create_engine(settings.SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# --- Создание "фабрики сессий" (SessionLocal) ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Функция-зависимость FastAPI для получения сессии БД ---
def get_db() -> Generator[Session, None, None]:
    """
    Предоставляет сессию БД для одного API-запроса.
    Гарантирует закрытие сессии после завершения запроса.
    """
    db: Session | None = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db is not None:
            db.close()