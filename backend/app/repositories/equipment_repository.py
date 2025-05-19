from pydantic import BaseModel
from typing import cast, List, Optional
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session
from app.models.equipment import Shop, AggregateType, ActuatorType, Line, Aggregate, Actuator
from app.models.enums import LineTypesEnum
from app.repositories.base import CRUDBase


'''
====================================
    Репозитории для справочников     
====================================
'''


# --- Репозиторий для цехов ---
class ShopRepository(CRUDBase[Shop, BaseModel, BaseModel]):

    def get(self, db: Session, *, shop_id: int) -> Optional[Shop]:
        """ Получает цех по ID """
        return db.get(self.model, shop_id)

    def get_by_name(self, db: Session, *, name: str) -> Optional[Shop]:
        """ Получает цех по имени """
        statement = select(self.model).where(self.model.shop_name == name)
        return db.execute(statement).scalar_one_or_none()

    def remove(self, db: Session, *, shop_id: int) -> Optional[Shop]:
        """ Удаляет цех по ID """
        obj = self.get(db=db, shop_id=shop_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении Shop {shop_id}: {e}")
                db.rollback()
                return None
        return None


# --- Репозиторий для типов агрегатов ---
class AggregateTypeRepository(CRUDBase[AggregateType, BaseModel, BaseModel]):

    def get(self, db: Session, *, aggregate_type_id: int) -> Optional[AggregateType]:
        """ Получает тип агрегата по ID """
        return db.get(self.model, aggregate_type_id)

    def get_by_name(self, db: Session, *, name: str) -> Optional[AggregateType]:
        """ Получает тип агрегата по имени """
        statement = select(self.model).where(self.model.aggregate_type_name == name)
        return db.execute(statement).scalar_one_or_none()

    def remove(self, db: Session, *, aggregate_type_id: int) -> Optional[AggregateType]:
        """ Удаляет тип агрегата по ID """
        obj = self.get(db=db, aggregate_type_id=aggregate_type_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении AggregateType {aggregate_type_id}: {e}")
                db.rollback()
                return None
        return None


# --- Репозиторий для типов актуаторов ---
class ActuatorTypeRepository(CRUDBase[ActuatorType, BaseModel, BaseModel]):

    def get(self, db: Session, *, actuator_type_id: int) -> Optional[ActuatorType]:
        """ Получает тип актуатора по ID """
        return db.get(self.model, actuator_type_id)

    def get_by_name(self, db: Session, *, name: str) -> Optional[ActuatorType]:
        """ Получает тип актуатора по имени """
        statement = select(self.model).where(self.model.actuator_type_name == name)
        return db.execute(statement).scalar_one_or_none()

    def remove(self, db: Session, *, actuator_type_id: int) -> Optional[ActuatorType]:
        """ Удаляет тип актуатора по ID """
        obj = self.get(db=db, actuator_type_id=actuator_type_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении ActuatorType {actuator_type_id}: {e}")
                db.rollback()
                return None
        return None


'''
================================
    Репозитории для иерархии     
================================
'''


# --- Репозиторий для линий ---
class LineRepository(CRUDBase[Line, BaseModel, BaseModel]):

    def get(self, db: Session, *, line_id: int) -> Optional[Line]:
        """ Получает линию по ID """
        return db.get(self.model, line_id)

    def get_by_shop(self, db: Session, *, shop_id: int, skip: int = 0, limit: int = 100) -> List[Line]:
        """ Получает линии для конкретного цеха с пагинацией """
        statement = (select(self.model).where(self.model.shop_id == shop_id).offset(skip).limit(limit))
        result = db.execute(statement)
        return cast(List[Line], result.scalars().all())

    def get_by_shop_and_type(self, db: Session, *, shop_id: int, line_type: LineTypesEnum) -> Optional[Line]:
        """ Получает конкретную линию в цехе по её типу """
        statement = select(self.model).where(self.model.shop_id == shop_id, self.model.line_type == line_type)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_shop_ids_for_lines(self, db: Session, *, line_ids: List[int]) -> List[int]:
        """ Получает список уникальных ID цехов для заданного списка ID линий """
        if not line_ids:
            return []
        statement = select(distinct(self.model.shop_id)).where(self.model.line_id.in_(line_ids))
        result = db.execute(statement)
        return cast(List[int], result.scalars().all())

    def get_by_shop_and_ids(self, db: Session, *, shop_id: int, allowed_line_ids: List[int], skip: int = 0, limit: int = 100) -> List[Line]:
        """ Получает линии для конкретного цеха, но только те, что есть в списке allowed_line_ids.
        Используется для пользователей с доступом ScopeTypeEnum.LINE. """
        if not allowed_line_ids:
            return []
        statement = (
            select(self.model)
            .where(self.model.shop_id == shop_id, self.model.line_id.in_(allowed_line_ids))
            .offset(skip)
            .limit(limit)
        )
        result = db.execute(statement)
        return cast(List[Line], result.scalars().all())

    def remove(self, db: Session, *, line_id: int) -> Optional[Line]:
        """ Удаляет линию по ID (с каскадным удалением агрегатов) """
        obj = self.get(db=db, line_id=line_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении Line {line_id}: {e}")
                db.rollback()
                return None
        return None


# --- Репозиторий для агрегатов ---
class AggregateRepository(CRUDBase[Aggregate, BaseModel, BaseModel]):

    def get(self, db: Session, *, aggregate_id: int) -> Optional[Aggregate]:
        """ Получает агрегат по ID """
        return db.get(self.model, aggregate_id)

    def get_by_line(self, db: Session, *, line_id: int, skip: int = 0, limit: int = 100) -> List[Aggregate]:
        """ Получает агрегаты для конкретной линии с пагинацией """
        statement = (select(self.model).where(self.model.line_id == line_id).offset(skip).limit(limit))
        result = db.execute(statement)
        return cast(List[Aggregate], result.scalars().all())

    def remove(self, db: Session, *, aggregate_id: int) -> Optional[Aggregate]:
        """ Удаляет агрегат по ID (с каскадным удалением актуаторов) """
        obj = self.get(db=db, aggregate_id=aggregate_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении Aggregate {aggregate_id}: {e}")
                db.rollback()
                return None
        return None


# --- Репозиторий для актуаторов ---
class ActuatorRepository(CRUDBase[Actuator, BaseModel, BaseModel]):

    def get(self, db: Session, *, actuator_id: int) -> Optional[Actuator]:
        """ Получает актуатор по ID """
        return db.get(self.model, actuator_id)

    def get_by_aggregate(self, db: Session, *, aggregate_id: int, skip: int = 0, limit: int = 100) -> List[Actuator]:
        """ Получает актуаторы для конкретного агрегата с пагинацией """
        statement = (select(self.model).where(self.model.aggregate_id == aggregate_id).offset(skip).limit(limit))
        result = db.execute(statement)
        return cast(List[Actuator], result.scalars().all())

    def remove(self, db: Session, *, actuator_id: int) -> Optional[Actuator]:
        """ Удаляет актуатор по ID (с каскадным удалением параметров) """
        obj = self.get(db=db, actuator_id=actuator_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении Actuator {actuator_id}: {e}")
                db.rollback()
                return None
        return None


# --- Экземпляры репозиториев ---
shop_repository = ShopRepository(Shop)
aggregate_type_repository = AggregateTypeRepository(AggregateType)
actuator_type_repository = ActuatorTypeRepository(ActuatorType)
line_repository = LineRepository(Line)
aggregate_repository = AggregateRepository(Aggregate)
actuator_repository = ActuatorRepository(Actuator)