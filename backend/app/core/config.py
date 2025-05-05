from typing import Optional
from dotenv import load_dotenv
from pydantic import PostgresDsn, model_validator
from pydantic_settings import BaseSettings


# --- Загрузка переменных окружения (из .env) ---
load_dotenv(verbose=True)


class Settings(BaseSettings):
    # --- Параметры подключения к БД ---
    DB_NAME: str = "Ural_Steel"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: str = "5432"

    # --- Переменные для JWT ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- URL БД (будет вычислен) ---
    SQLALCHEMY_DATABASE_URL: Optional[PostgresDsn] = None

    # --- Валидатор соберёт URL после загрузки остальных полей ---
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        self.SQLALCHEMY_DATABASE_URL = PostgresDsn.build(
            scheme="postgresql+psycopg2",
            path=f"{self.DB_NAME}",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=int(self.DB_PORT)
        )
        return self


# --- Экземпляр настроек ---
settings = Settings()

# --- Проверка ---
if not settings.SECRET_KEY or settings.SECRET_KEY == "default_secret_needs_changing":
    print("!!! ВНИМАНИЕ: SECRET_KEY не установлен или используется небезопасный дефолт!")
    print("!!! Пожалуйста, сгенерируйте ключ и установите его в .env файле !!!")