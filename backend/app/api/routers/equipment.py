from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User as UserModel
from app.models.equipment import Shop, Line, Aggregate, Actuator, AggregateType, ActuatorType
from app.schemas.equipment import ShopRead, LineRead, AggregateRead, ActuatorRead, AggregateTypeRead, ActuatorTypeRead
from app.services import equipment_service


router = APIRouter(prefix="/equipment", tags=["Equipment Hierarchy"])


'''
==================================
    Эндпоинты для справочников    
==================================
'''


@router.get("/aggregate-types/", response_model=List[AggregateTypeRead])
async def read_aggregate_types(*, db: Session = Depends(deps.get_db),
                               _current_user: UserModel = Depends(deps.get_current_user),
                               skip: int = 0, limit: int = 300) -> List[AggregateType]:
    """ Получает список всех типов агрегатов.
    Требуется аутентификация пользователя. """
    aggregate_types = equipment_service.get_all_aggregate_types(db=db, skip=skip, limit=limit)
    return aggregate_types


@router.get("/actuator-types/", response_model=List[ActuatorTypeRead])
async def read_actuator_types(*, db: Session = Depends(deps.get_db),
                              _current_user: UserModel = Depends(deps.get_current_user),
                              skip: int = 0, limit: int = 600) -> List[ActuatorType]:
    """ Получает список всех типов актуаторов.
    Требуется аутентификация пользователя. """
    actuator_types = equipment_service.get_all_actuator_types(db=db, skip=skip, limit=limit)
    return actuator_types


'''
==============================
    Эндпоинты для иерархии    
==============================
'''


@router.get("/shops/", response_model=List[ShopRead])
async def read_shops(*, db: Session = Depends(deps.get_db),
                     current_user: UserModel = Depends(deps.get_current_user)) -> List[Shop]:
    """ Получает список цехов, доступных текущему пользователю """
    shops = equipment_service.get_available_shops(db=db, current_user=current_user)
    return shops


@router.get("/shops/{shop_id}/lines/", response_model=List[LineRead])
async def read_lines_for_shop(*, shop_id: int, db: Session = Depends(deps.get_db),
                              current_user: UserModel = Depends(deps.get_current_user),
                              skip: int = 0, limit: int = 25) -> List[Line]:
    """ Получает список линий для выбранного цеха.
    Список фильтруется согласно правам доступа текущего пользователя. """
    lines = equipment_service.get_lines_for_shop(
        db=db, current_user=current_user, shop_id=shop_id, skip=skip, limit=limit
    )
    return lines


@router.get("/lines/{line_id}/aggregates/", response_model=List[AggregateRead])
async def read_aggregates_for_line(*, line_id: int, db: Session = Depends(deps.get_db),
                                   current_user: UserModel = Depends(deps.get_current_user),
                                   skip: int = 0, limit: int = 50) -> List[Aggregate]:
    """ Получает список агрегатов для выбранной линии.
    Список фильтруется согласно правам доступа текущего пользователя. """
    aggregates = equipment_service.get_aggregates_for_line(
        db=db, current_user=current_user, line_id=line_id, skip=skip, limit=limit
    )
    return aggregates


@router.get("/aggregates/{aggregate_id}/actuators/", response_model=List[ActuatorRead])
async def read_actuators_for_aggregate(*, aggregate_id: int, db: Session = Depends(deps.get_db),
                                       current_user: UserModel = Depends(deps.get_current_user),
                                       skip: int = 0, limit: int = 100) -> List[Actuator]:
    """ Получает список актуаторов для выбранного агрегата.
    Список фильтруется согласно правам доступа текущего пользователя. """
    actuators = equipment_service.get_actuators_for_aggregate(
        db=db, current_user=current_user, aggregate_id=aggregate_id, skip=skip, limit=limit
    )
    return actuators