import datetime
from typing import cast, List, Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session
from app.models.equipment import Shop, AggregateType, ActuatorType, Line, Aggregate, Actuator
from app.models.parameter import ParameterType, Parameter, ParameterData
from app.repositories.base import CRUDBase


# --- Репозиторий для типов параметров ---
class ParameterTypeRepository(CRUDBase[ParameterType, BaseModel, BaseModel]):

    def get(self, db: Session, *, parameter_type_id: int) -> Optional[ParameterType]:
        """ Получает тип параметра по ID """
        return db.get(self.model, parameter_type_id)

    def get_by_name(self, db: Session, *, name: str) -> Optional[ParameterType]:
        """ Получает тип параметра по имени """
        statement = select(self.model).where(self.model.parameter_type_name == name)
        return db.execute(statement).scalar_one_or_none()

    def remove(self, db: Session, *, parameter_type_id: int) -> Optional[ParameterType]:
        """ Удаляет тип параметра по ID """
        obj = self.get(db=db, parameter_type_id=parameter_type_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении ParameterType {parameter_type_id}: {e}")
                db.rollback()
                return None
        return None


# --- Репозиторий для параметров (связь "Актуатор <-> Тип Параметра") ---
class ParameterRepository(CRUDBase[Parameter, BaseModel, BaseModel]):

    def get(self, db: Session, *, parameter_id: int) -> Optional[Parameter]:
        """ Получает параметр по ID """
        return db.get(self.model, parameter_id)

    def get_by_actuator(self, db: Session, *, actuator_id: int, skip: int = 0, limit: int = 100) -> List[Parameter]:
        """ Получает параметры для конкретного актуатора с пагинацией """
        statement = (select(self.model).where(self.model.actuator_id == actuator_id).offset(skip).limit(limit))
        result = db.execute(statement)
        return cast(List[Parameter], result.scalars().all())

    def get_by_actuator_and_type(self, db: Session, *, actuator_id: int, parameter_type_id: int) -> Optional[Parameter]:
        """ Получает конкретный параметр по актуатору и типу """
        statement = select(self.model).where(self.model.actuator_id == actuator_id, self.model.parameter_type_id == parameter_type_id)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def remove(self, db: Session, *, parameter_id: int) -> Optional[Parameter]:
        """ Удаляет параметр по ID (с каскадным удалением данных и правил) """
        obj = self.get(db=db, parameter_id=parameter_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# --- Репозиторий для данных параметров (Time-Series) ---
class ParameterDataRepository:  # НЕ наследуется от CRUDBase, т.к. операции специфичны для временных рядов

    def __init__(self, model: type[ParameterData]):
        """ Инициализация репозитория моделью ParameterData """
        self.model = model

    def get_latest(self, db: Session, *, parameter_id: int) -> Optional[ParameterData]:
        """ Получает самую последнюю запись для параметра """
        statement = (select(self.model).where(self.model.parameter_id == parameter_id).order_by(self.model.data_timestamp.desc()).limit(1))
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_range(self, db: Session, *, parameter_id: int, start_time: datetime.datetime, end_time: datetime.datetime, limit: Optional[int] = None) -> List[ParameterData]:
        """ Получает данные для параметра в заданном временном диапазоне """
        statement = (
            select(self.model)
            .where(
                self.model.parameter_id == parameter_id,
                self.model.data_timestamp >= start_time,
                self.model.data_timestamp <= end_time
            )
            .order_by(self.model.data_timestamp.asc())
        )
        if limit:
            statement = statement.limit(limit)

        result = db.execute(statement)
        return cast(List[ParameterData], result.scalars().all())


    def get_by_data_id_with_details(self, db: Session, *, parameter_data_id: int) -> Optional[ParameterData]:
        """ Получает запись ParameterData по ее parameter_data_id
        с предзагрузкой всех связанных данных, необходимых для формирования сообщения тревоги """
        statement = (
            select(self.model)
            .options(
                # Загружает все необходимые связи одним запросом
                joinedload(self.model.parameter)
                .joinedload(Parameter.parameter_type),
                joinedload(self.model.parameter)
                .joinedload(Parameter.actuator)
                .joinedload(Actuator.actuator_type),
                joinedload(self.model.parameter)
                .joinedload(Parameter.actuator)
                .joinedload(Actuator.aggregate)
                .joinedload(Aggregate.aggregate_type),
                joinedload(self.model.parameter)
                .joinedload(Parameter.actuator)
                .joinedload(Actuator.aggregate)
                .joinedload(Aggregate.line)
                .joinedload(Line.shop)
            )
            .where(self.model.parameter_data_id == parameter_data_id)
        )
        result = db.execute(statement)
        return result.scalar_one_or_none()


# --- Экземпляры репозиториев ---
parameter_type_repository = ParameterTypeRepository(ParameterType)
parameter_repository = ParameterRepository(Parameter)
parameter_data_repository = ParameterDataRepository(ParameterData)