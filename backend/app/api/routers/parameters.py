import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.parameter import ParameterType, Parameter, ParameterData
from app.models.user import User as UserModel
from app.schemas.parameter import ParameterTypeRead, ParameterRead, ParameterDataRead
from app.services import parameter_service


router = APIRouter(prefix="/parameters", tags=["Parameters & Data"])


'''
======================================
    Эндпоинты для типов параметров    
======================================
'''


@router.get("/types/", response_model=List[ParameterTypeRead])
async def read_parameter_types(*, db: Session = Depends(deps.get_db),
                               _current_user: UserModel = Depends(deps.get_current_user),
                               skip: int = 0, limit: int = 900) -> List[ParameterType]:
    """ Получает список всех типов параметров.
    Требуется аутентификация пользователя. """
    parameter_types = parameter_service.get_all_parameter_types(db=db, skip=skip, limit=limit)
    return parameter_types


'''
====================================================
    Эндпоинты для конкретных параметров (связок)    
====================================================
'''


@router.get("/actuator/{actuator_id}/", response_model=List[ParameterRead])
async def read_parameters_for_actuator(*, actuator_id: int, db: Session = Depends(deps.get_db),
                                       current_user: UserModel = Depends(deps.get_current_user),
                                       skip: int = 0, limit: int = 200) -> List[Parameter]:
    """ Получает список параметров для выбранного актуатора.
    Список фильтруется согласно правам доступа текущего пользователя. """
    parameters = parameter_service.get_parameters_for_actuator(
        db=db, current_user=current_user, actuator_id=actuator_id, skip=skip, limit=limit
    )
    return parameters


'''
============================================
    Эндпоинты для данных временных рядов
============================================
'''


@router.get("/{parameter_id}/data/", response_model=List[ParameterDataRead])
async def read_parameter_data(*, parameter_id: int, db: Session = Depends(deps.get_db),
                              start_time: datetime.datetime = Query(..., description="Начало временного диапазона"),
                              end_time: datetime.datetime = Query(..., description="Конец временного диапазона"),
                              limit: Optional[int] = Query(None, description="Максимальное количество записей", ge=1),
                              current_user: UserModel = Depends(deps.get_current_user)) -> List[ParameterData]:
    """ Получает данные временного ряда для выбранного параметра за определенный период.
    Доступ к параметру проверяется на уровне сервиса. """
    if start_time >= end_time:
        raise HTTPException(
            status_code=400,
            detail="Время начала должно быть меньше времени окончания."
        )

    max_range_days = 30
    if (end_time - start_time) > datetime.timedelta(days=max_range_days):
        raise HTTPException(
            status_code=400,
            detail=f"Запрашиваемый диапазон не может превышать {max_range_days} дней."
        )

    data = parameter_service.get_parameter_data(
        db=db,
        current_user=current_user,
        parameter_id=parameter_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    return data