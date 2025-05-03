from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.enums import AlarmTypesEnum


# --- Базовая схема для настроек ---
class SettingBase(BaseModel):
    theme: str = Field(default='light', pattern=r'^(light|dark)$')
    language: str = Field(default='ru', pattern=r'^(ru|en)$')
    alarm_types: List[AlarmTypesEnum] = [AlarmTypesEnum.NOTIFICATION]
    is_rules_public: bool = False


# --- Схема для обновления настроек ---
class SettingUpdate(BaseModel):
    theme: Optional[str] = Field(default=None, pattern=r'^(light|dark)$')
    language: Optional[str] = Field(default=None, pattern=r'^(ru|en)$')
    alarm_types: Optional[List[AlarmTypesEnum]] = None
    is_rules_public: Optional[bool] = None


# --- Схема для чтения настроек ---
class SettingRead(SettingBase):
    user_id: int

    model_config = {
        "from_attributes": True
    }