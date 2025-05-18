from pydantic import BaseModel
from typing import Any, cast, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.orm import Session
from app.db.base_class import Base


# --- Generic-типы ---
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


# --- Базовый класс для CRUD ---
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100,
                  order_by: Optional[List[ColumnElement]] = None, options: Optional[List] = None) -> List[ModelType]:
        """ Получает список записей из БД с возможностью пропуска (skip) и ограничения (limit).
        Используется для пагинации. """
        statement = select(self.model)
        if options:
            statement = statement.options(*options)
        if order_by is not None:
            for ob_column in order_by:
                statement = statement.order_by(ob_column)
        statement = statement.offset(skip).limit(limit)
        result = db.execute(statement)
        return cast(List[ModelType], result.scalars().all())

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """ Создаёт новую запись в БД на основе Pydantic схемы """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)  # Создание экземпляра ORM модели
        db.add(db_obj)  # Добавление в сессию
        db.commit()  # Сохранение в БД
        db.refresh(db_obj)  # Обновление объекта из БД
        return db_obj

    def update(self, db: Session, *, db_obj: ModelType, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:  # noqa B902: "Используется self неявно: через ModelType/UpdateSchemaType и для возможности override"
        """ Обновляет существующую запись в БД данными из Pydantic схемы или словаря.
        Обновляются только те поля, которые присутствуют в obj_in. """
        obj_data = jsonable_encoder(db_obj)  # Текущие данные объекта

        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj