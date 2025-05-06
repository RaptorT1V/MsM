from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.equipment import Shop, Line, Aggregate, Actuator
from app.models.user import User
from app.repositories.equipment_repository import shop_repository, line_repository, aggregate_repository, actuator_repository
from app.services.permissions import ScopeTypeEnum, get_user_access_scope, can_user_access_shop, can_user_access_line, can_user_access_aggregate


'''
===============================================
    Основные сервисные функции для иерархии    
===============================================
'''


def get_available_shops(*, db: Session, current_user: User) -> List[Shop]:
    """ Получает список доступных пользователю цехов """
    scope = get_user_access_scope(db=db, user=current_user)

    if scope.scope_type == ScopeTypeEnum.NONE:
        return []
    if scope.scope_type == ScopeTypeEnum.ALL:
        return shop_repository.get_multi(db=db, limit=1000)
    if scope.scope_type == ScopeTypeEnum.SHOP:
        shops = [shop_repository.get(db=db, shop_id=s_id) for s_id in scope.allowed_shop_ids]
        return [s for s in shops if s is not None]
    if scope.scope_type == ScopeTypeEnum.LINE:
        shop_ids = line_repository.get_shop_ids_for_lines(db=db, line_ids=scope.allowed_line_ids)
        shops = [shop_repository.get(db=db, shop_id=s_id) for s_id in shop_ids]
        return [s for s in shops if s is not None]
    return []


def get_lines_for_shop(*, db: Session, current_user: User, shop_id: int, skip: int = 0, limit: int = 100) -> List[Line]:
    """ Получает список доступных пользователю линий для цеха """
    scope = get_user_access_scope(db=db, user=current_user)

    # 1. Проверяет доступ к запрашиваемому цеху
    if not can_user_access_shop(scope=scope, target_shop_id=shop_id, db=db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому цеху")

    # 2. Получает линии, фильтруя по правам пользователя
    if scope.scope_type == ScopeTypeEnum.LINE:
        return line_repository.get_by_shop_and_ids(db=db, shop_id=shop_id, allowed_line_ids=scope.allowed_line_ids, skip=skip, limit=limit)
    else:
        return line_repository.get_by_shop(db=db, shop_id=shop_id, skip=skip, limit=limit)


def get_aggregates_for_line(*, db: Session, current_user: User, line_id: int, skip: int = 0, limit: int = 100) -> List[Aggregate]:
    """ Получает список доступных пользователю агрегатов для линии """
    scope = get_user_access_scope(db=db, user=current_user)

    # 1. Проверяет доступ к линии
    if not can_user_access_line(db=db, scope=scope, target_line_id=line_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этой линии")

    # 2. Получает агрегаты
    return aggregate_repository.get_by_line(db=db, line_id=line_id, skip=skip, limit=limit)


def get_actuators_for_aggregate(*, db: Session, current_user: User, aggregate_id: int, skip: int = 0, limit: int = 100) -> List[Actuator]:
    """ Получает список доступных пользователю актуаторов для агрегата """
    scope = get_user_access_scope(db=db, user=current_user)

    # 1. Проверяет доступ к агрегату
    if not can_user_access_aggregate(db=db, scope=scope, target_aggregate_id=aggregate_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет доступа к этому агрегату")

    # 2. Получает актуаторы
    return actuator_repository.get_by_aggregate(db=db, aggregate_id=aggregate_id, skip=skip, limit=limit)