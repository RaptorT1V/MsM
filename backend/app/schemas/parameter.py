import datetime
from pydantic import BaseModel
from typing import Optional


'''
==================================
    Схемы для типов параметров     
==================================
'''


# --- Базовая схема для типа параметра ---
class ParameterTypeBase(BaseModel):
    parameter_type_name: str
    parameter_unit: Optional[str] = None


# --- Схема для чтения данных типа параметра ---
class ParameterTypeRead(ParameterTypeBase):
    parameter_type_id: int

    model_config = {
        "from_attributes": True
    }


'''
============================
    Схемы для параметров     
============================
'''


# --- Базовая схема для параметра ---
class ParameterBase(BaseModel):
    actuator_id: int
    parameter_type_id: int


# --- Схема для чтения данных параметра ---
class ParameterRead(ParameterBase):
    parameter_id: int

    model_config = {
        "from_attributes": True
    }


'''
========================================
    Схемы для данных временных рядов     
========================================
'''


# --- Базовая схема для временных данных параметра ---
class ParameterDataBase(BaseModel):
    parameter_id: int
    parameter_value: float
    data_timestamp: datetime.datetime


# --- Схема для чтения временных данных параметра ---
class ParameterDataRead(ParameterDataBase):
    parameter_data_id: int  # На всякий случай :)

    model_config = {
        "from_attributes": True
    }