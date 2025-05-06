import enum
from typing import Any, Dict, List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.enums import LineTypesEnum
from app.models.user import User
from app.models.equipment import Line, Aggregate, Actuator
from app.models.parameter import Parameter
from app.repositories.equipment_repository import shop_repository, line_repository, aggregate_repository, actuator_repository
from app.repositories.parameter_repository import parameter_repository


# --- Enum для типов доступа ---
class ScopeTypeEnum(str, enum.Enum):
    ALL = "all"
    SHOP = "shop"
    LINE = "line"
    NONE = "none"


# --- Структура для области видимости пользователя ---
class AccessScope(BaseModel):
    scope_type: ScopeTypeEnum
    allowed_shop_ids: List[int] = []
    allowed_line_ids: List[int] = []


# --- Словарь-маппинг "Роль -> Права" ---
ROLE_SCOPES_CONFIG: Dict[str, Dict[str, Any]] = {
    "Директор":                         {"scope_type": ScopeTypeEnum.ALL},
    "Главный аналитик":                 {"scope_type": ScopeTypeEnum.ALL},
    "Начальник аглофабрики":            {"scope_type": ScopeTypeEnum.SHOP, "shop_name": "Агломерационный цех"},
    "Начальник ЭСПЦ":                   {"scope_type": ScopeTypeEnum.SHOP, "shop_name": "Электросталеплавильный цех"},
    "Аналитик 1-ой линии аглофабрики":  {"scope_type": ScopeTypeEnum.LINE, "shop_name": "Агломерационный цех", "line_type": LineTypesEnum.FIRST},
    "Аналитик 2-ой линии аглофабрики":  {"scope_type": ScopeTypeEnum.LINE, "shop_name": "Агломерационный цех", "line_type": LineTypesEnum.SECOND},
    "Аналитик 1-ой линии ЭСПЦ":         {"scope_type": ScopeTypeEnum.LINE, "shop_name": "Электросталеплавильный цех", "line_type": LineTypesEnum.FIRST},
    "Аналитик 2-ой линии ЭСПЦ":         {"scope_type": ScopeTypeEnum.LINE, "shop_name": "Электросталеплавильный цех", "line_type": LineTypesEnum.SECOND},
    # TODO: Добавить другие должности в будущем
}


# --- Функция определения прав доступа ---
def get_user_access_scope(*, db: Session, user: User) -> AccessScope:
    """ Определяет область видимости пользователя на основе его должности """
    if not user.job_title:
        return AccessScope(scope_type=ScopeTypeEnum.NONE)

    job_title_name = user.job_title.job_title_name
    role_config = ROLE_SCOPES_CONFIG.get(job_title_name)

    # Если должности нет в конфиге или нет прав - возвращает NONE
    if not role_config:
        return AccessScope(scope_type=ScopeTypeEnum.NONE)

    scope = AccessScope(scope_type=role_config["scope_type"])

    # Получает реальные ID на основе имен из конфига
    if scope.scope_type == ScopeTypeEnum.SHOP:
        shop = shop_repository.get_by_name(db, name=role_config["shop_name"])
        if shop:
            scope.allowed_shop_ids = [shop.shop_id]
        else:  # Если цех из конфига не найден в БД, сбрасывает права
            print(f"Warning: Shop '{role_config['shop_name']}' not found for role '{job_title_name}'. Access set to NONE.")
            scope.scope_type = ScopeTypeEnum.NONE
    elif scope.scope_type == ScopeTypeEnum.LINE:
        shop = shop_repository.get_by_name(db, name=role_config["shop_name"])
        if shop:
            line = line_repository.get_by_shop_and_type(
                db, shop_id=shop.shop_id, line_type=role_config["line_type"]
            )
            if line:
                scope.allowed_line_ids = [line.line_id]
            else:  # Если линия из конфига не найдена в БД, сбрасывает права
                print(f"Warning: Line '{role_config['line_type'].value}' in shop '{role_config['shop_name']}' not found for role '{job_title_name}'. Access set to NONE.")
                scope.scope_type = ScopeTypeEnum.NONE
        else:  # Если цех из конфига не найден, сбрасывает права
            print(f"Warning: Shop '{role_config['shop_name']}' not found for role '{job_title_name}'. Access set to NONE.")
            scope.scope_type = ScopeTypeEnum.NONE
    return scope


'''
===================================================================
    Вспомогательные функции проверки доступа (используют scope)    
===================================================================
'''


def can_user_access_shop(scope: AccessScope, target_shop_id: int, *, db: Session) -> bool:
    """ Может ли пользователь видеть данный цех? """
    if scope.scope_type == ScopeTypeEnum.ALL: return True
    if scope.scope_type == ScopeTypeEnum.SHOP:
        return target_shop_id in scope.allowed_shop_ids
    if scope.scope_type == ScopeTypeEnum.LINE:
        shop_ids = line_repository.get_shop_ids_for_lines(db=db, line_ids=scope.allowed_line_ids)
        return target_shop_id in shop_ids
    return False


def can_user_access_line(db: Session, scope: AccessScope, target_line_id: int) -> bool:
    """ Может ли пользователь видеть данную линию? """
    if scope.scope_type == ScopeTypeEnum.ALL:
        return True
    if scope.scope_type == ScopeTypeEnum.LINE:
        return target_line_id in scope.allowed_line_ids
    if scope.scope_type == ScopeTypeEnum.SHOP:
        line = line_repository.get(db=db, line_id=target_line_id)
        return line is not None and line.shop_id in scope.allowed_shop_ids
    return False


def can_user_access_aggregate(db: Session, scope: AccessScope, target_aggregate_id: int) -> bool:
    """ Может ли пользователь видеть данный агрегат? (через доступ к линии) """
    aggregate = aggregate_repository.get(db=db, aggregate_id=target_aggregate_id)
    if not aggregate:
        return False
    return can_user_access_line(db=db, scope=scope, target_line_id=aggregate.line_id)


def can_user_access_actuator(db: Session, scope: AccessScope, target_actuator_id: int) -> bool:
    """ Может ли пользователь видеть данный актуатор? (через доступ к агрегату) """
    actuator = actuator_repository.get(db=db, actuator_id=target_actuator_id)
    if not actuator:
        return False
    return can_user_access_aggregate(db=db, scope=scope, target_aggregate_id=actuator.aggregate_id)


def can_user_access_parameter(db: Session, scope: AccessScope, target_parameter_id: int) -> bool:
    """ Может ли пользователь видеть данный параметр? (через доступ к актуатору) """
    parameter = parameter_repository.get(db=db, parameter_id=target_parameter_id)
    if not parameter:
        return False
    return can_user_access_actuator(db=db, scope=scope, target_actuator_id=parameter.actuator_id)