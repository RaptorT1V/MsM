from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from typing import Generator
import os

# --- Загрузка переменных окружения ---
load_dotenv()

DB_NAME = os.getenv("DB_NAME", "Ural_Steel")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")

# --- Формирование URL для подключения ---
SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f"Database URL: postgresql+psycopg2://{DB_USER}:*****@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# --- Создание "Движка" SQLAlchemy (Engine) ---
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# --- Создание "Фабрики Сессий" (SessionLocal) ---
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