from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# --- КОНВЕНЦИЯ ИМЕНОВАНИЯ: ПРЕФИКСНЫЙ СТИЛЬ ---
POSTGRES_ALEMBIC_NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",   # Index:  ix_users_job_title_id
    "uq": "uq_%(table_name)s_%(column_0_name)s",    # Unique: uq_users_email
    "ck": "ck_%(table_name)s_%(constraint_name)s",  # Check:  ck_user_phone_format
    "fk": "fk_%(table_name)s_%(column_0_name)s",    # Foreign Key: fk_users_job_title_id
    "pk": "pk_%(table_name)s"                       # Primary Key: pk_users
}


# --- Базовый класс для всех моделей SQLAlchemy ---
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=POSTGRES_ALEMBIC_NAMING_CONVENTION)