from pydantic import BaseModel
from typing import Optional


# --- Схема для ответа с токеном доступа ---
class Token(BaseModel):
    access_token: str  # JWT-токен
    token_type: str = "bearer"  # Тип токена (стандарт OAuth2)


# --- Схема для данных, хранящихся в payload JWT-токена ---
class TokenData(BaseModel):
    user_id: Optional[int] = None