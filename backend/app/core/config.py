from typing import List, Optional, Union

from dotenv import load_dotenv
from pydantic import AnyHttpUrl, model_validator, PostgresDsn
from pydantic_settings import BaseSettings


# --- Загрузка переменных окружения (из .env) ---
load_dotenv(verbose=True)


class Settings(BaseSettings):
    # --- Параметры подключения к БД ---
    DB_NAME: str = "Ural_Steel"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432

    # --- Переменные для JWT ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- Настройки RabbitMQ ---
    RABBITMQ_USER: str = "guest"
    RABBITMQ_PASSWORD: str = "guest"
    RABBITMQ_HOST: str = "127.0.0.1"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_VIRTUAL_HOST: str = "/"
    RABBITMQ_QUEUE_NAME: str = "parameter_data_queue"
    RABBITMQ_LIVE_DATA_EXCHANGE_NAME: str = "live_data_fanout_exchange"
    RABBITMQ_URL: Optional[str] = None

    # --- URL БД (будет вычислен) ---
    SQLALCHEMY_DATABASE_URL: Optional[PostgresDsn] = None

    # --- Настройки CORS ---
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["http://localhost", "http://localhost:8080", "http://localhost:8000", "http://localhost:5000", "http://localhost:3000"]

    # --- Роли администраторов ---
    ADMIN_JOB_TITLES: List[str] = ["Директор"]

    # --- Валидатор соберёт URL после загрузки остальных полей ---
    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        """ Собирает полные URL-адреса для подключения к PostgreSQL и к RabbitMQ """
        self.SQLALCHEMY_DATABASE_URL = PostgresDsn.build(
            scheme="postgresql+psycopg2",
            path=f"{self.DB_NAME}",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT
        )
        self.RABBITMQ_URL = f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VIRTUAL_HOST}"
        return self


# --- Экземпляр настроек ---
settings = Settings()

# --- Проверка ---
if not settings.SECRET_KEY or settings.SECRET_KEY == "default":
    print("!!! ВНИМАНИЕ: SECRET_KEY не установлен или используется небезопасный дефолт!")
    print("!!! Пожалуйста, сгенерируйте ключ и установите его в .env файле !!!")