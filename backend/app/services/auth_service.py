from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import user_repository


'''
==========================================
    Работа с паролями и аутентификация    
==========================================
'''


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Проверяет, соответствует ли введенный пароль хешу из БД """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """ Генерирует хеш для нового пароля """
    return pwd_context.hash(password)


def authenticate_user(*, db: Session, username: str, password: str) -> Optional[User]:
    """ Аутентифицирует пользователя по имени пользователя (email или телефон) и паролю.
    Возвращает объект User в случае успеха, иначе None. """
    user = user_repository.get_by_email(db, email=username)
    if not user:
        user = user_repository.get_by_phone(db, phone=username)

    if not user or not verify_password(password, user.password_hash):
        return None
    return user


'''
=============================
    Работа с JWT-токенами    
=============================
'''


def create_access_token(*, db: Session, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """ Генерирует новый JWT-токен доступа """
    to_encode = {"sub": str(user_id)}

    user = user_repository.get(db, user_id=user_id)
    if user and user.job_title:
        to_encode["role"] = user.job_title.job_title_name
    else:
        to_encode["role"] = None

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt