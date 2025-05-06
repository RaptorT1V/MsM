from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings


'''
=========================
    Работа с паролями    
=========================
'''


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ Проверяет, соответствует ли введенный пароль хешу из БД """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """ Генерирует хеш для нового пароля """
    return pwd_context.hash(password)


'''
=============================
    Работа с JWT-токенами    
=============================
'''


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """ Генерирует новый JWT-токен доступа """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


'''
def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """ Декодирует JWT токен и получает данные (payload) """
    try:
        payload = jwt.decode(
             token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
'''