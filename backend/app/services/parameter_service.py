import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.parameter import ParameterType, Parameter, ParameterData
from app.models.user import User
from app.repositories.parameter_repository import parameter_type_repository, parameter_repository, parameter_data_repository
from app.services.equipment_service import get_user_access_scope
from app.services.permissions import can_user_access_actuator, can_user_access_parameter


'''
====================================================
    Сервисные функции для параметров и их данных    
====================================================
'''


def get_all_parameter_types(*, db: Session, skip: int = 0, limit: int = 100) -> List[ParameterType]:
    """ Получает список всех типов параметров """
    return parameter_type_repository.get_multi(db=db, skip=skip, limit=limit)


def get_parameters_for_actuator(*, db: Session, current_user: User, actuator_id: int, skip: int = 0, limit: int = 100) -> List[Parameter]:
    """ Получает список доступных пользователю параметров для актуатора """
    scope = get_user_access_scope(db=db, user=current_user)

    # 1. Проверяет доступ к актуатору
    if not can_user_access_actuator(db=db, scope=scope, target_actuator_id=actuator_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к параметрам этого актуатора")

    # 2. Получает параметры
    return parameter_repository.get_by_actuator(db=db, actuator_id=actuator_id, skip=skip, limit=limit)


def get_parameter_details(*, db: Session, current_user: User, parameter_id: int) -> Parameter:
    """ Получает детали конкретного параметра, доступного пользователю """
    # 1. Получает параметр
    parameter = parameter_repository.get(db=db, parameter_id=parameter_id)
    if not parameter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Параметр не найден")

    # 2. Проверяет доступ к актуатору этого параметра
    scope = get_user_access_scope(db=db, user=current_user)
    if not can_user_access_actuator(db=db, scope=scope, target_actuator_id=parameter.actuator_id):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому параметру")

    return parameter


def get_parameter_data(*, db: Session, current_user: User, parameter_id: int, start_time: datetime.datetime, end_time: datetime.datetime, limit: Optional[int] = None) -> List[ParameterData]:
    """ Получает данные временного ряда для параметра, доступного пользователю """
    scope = get_user_access_scope(db=db, user=current_user)

    # 1. Получает параметр и проверяет доступ к нему (через его актуатор)
    if not can_user_access_parameter(db=db, scope=scope, target_parameter_id=parameter_id):
         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к данным этого параметра")

    # 2. Получает данные временного ряда
    return parameter_data_repository.get_range(db=db, parameter_id=parameter_id, start_time=start_time, end_time=end_time, limit=limit)