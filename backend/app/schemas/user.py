import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# --- Базовая схема для пользователя ---
class UserBase(BaseModel):
    email: EmailStr
    phone: str = Field(pattern=r'^\+7\d{10}$')
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    job_titles_id: int


# --- Схема для создания пользователя ---
class UserCreate(UserBase):
    password: str


# --- Схема для чтения данных пользователя ---
class UserRead(UserBase):
    user_id: int
    created_at: datetime.datetime
    job_title_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# --- Схема для чтения данных пользователя со всеми полями из БД, включая хеш пароля ---
class UserInDB(UserRead):
    password_hash: str


# --- Схема для смены пароля пользователем ---
class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str


# --- Схема для обновления данных админом ---
class UserUpdateAdmin(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, pattern=r'^\+7\d{10}$')
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    job_titles_id: Optional[int] = None