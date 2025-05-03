from pydantic import BaseModel
from app.models.enums import LineTypesEnum


'''
==============================
    Схемы для справочников     
==============================
'''


# --- Базовая схема для цеха ---
class ShopBase(BaseModel):
    shop_name: str


# --- Схема для чтения данных цеха ---
class ShopRead(ShopBase):
    shop_id: int

    model_config = {
        "from_attributes": True
    }


# --- Базовая схема для типа агрегата ---
class AggregateTypeBase(BaseModel):
    aggregate_type_name: str


# --- Схема для чтения данных типа агрегата ---
class AggregateTypeRead(AggregateTypeBase):
    aggregate_type_id: int

    model_config = {
        "from_attributes": True
    }


# --- Базовая схема для типа актуатора ---
class ActuatorTypeBase(BaseModel):
    actuator_type_name: str


# --- Схема для чтения данных типа актуатора ---
class ActuatorTypeRead(ActuatorTypeBase):
    actuator_type_id: int

    model_config = {
        "from_attributes": True
    }


'''
==========================
    Схемы для иерархии     
==========================
'''


# --- Базовая схема для линии ---
class LineBase(BaseModel):
    shop_id: int
    line_type: LineTypesEnum


# --- Схема для чтения данных линии ---
class LineRead(LineBase):
    line_id: int

    model_config = {
        "from_attributes": True
    }


# --- Базовая схема для агрегата ---
class AggregateBase(BaseModel):
    line_id: int
    aggregate_type_id: int


# --- Схема для чтения данных агрегата ---
class AggregateRead(AggregateBase):
    aggregate_id: int

    model_config = {
        "from_attributes": True
    }


# --- Базовая схема для актуатора ---
class ActuatorBase(BaseModel):
    aggregate_id: int
    actuator_type_id: int


# --- Схема для чтения данных актуатора ---
class ActuatorRead(ActuatorBase):
    actuator_id: int

    model_config = {
        "from_attributes": True
    }