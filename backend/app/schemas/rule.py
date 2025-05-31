import datetime
from typing import Optional

from pydantic import BaseModel, Field


'''
==================================
    Схемы для Monitoring Rules     
==================================
'''


# --- Базовая схема для правила ---
class RuleBase(BaseModel):
    parameter_id: int
    rule_name: Optional[str] = Field(None, max_length=110)
    comparison_operator: str = Field(..., pattern=r"^(<|>)$", max_length=1)
    threshold: float
    is_active: bool = True


# --- Схема для создания нового правила ---
class RuleCreate(RuleBase):
    pass


# --- Схема для чтения правила ---
class RuleRead(RuleBase):
    rule_id: int
    user_id: int
    created_at: datetime.datetime

    model_config = {
        "from_attributes": True
    }


# --- Схема для обновления правила ---
class RuleUpdate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=110)
    comparison_operator: Optional[str] = Field(default=None, pattern=r"^(<|>)$", max_length=1)
    threshold: Optional[float] = None
    is_active: Optional[bool] = None


'''
========================
    Схемы для Alerts     
========================
'''


# --- Базовая схема для тревоги ---
class AlertBase(BaseModel):
    rule_id: int
    parameter_data_id: int
    alert_message: Optional[str] = Field(None, max_length=250)
    is_read: bool = False
    alert_timestamp: datetime.datetime


# --- Схема для создания тревоги внутри бэкенда ---
class AlertCreateInternal(BaseModel):
    rule_id: int
    parameter_data_id: int
    alert_message: Optional[str] = None


# --- Схема для чтения тревоги ---
class AlertRead(AlertBase):
    alert_id: int

    model_config = {
        "from_attributes": True
    }


# --- Схема для обновления тревоги ---
class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None