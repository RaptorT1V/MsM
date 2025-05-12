from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.rule import MonitoringRule
from app.models.user import User
from app.repositories.rule_repository import rule_repository
from app.services.permissions import get_user_access_scope, can_user_access_parameter
from app.schemas.rule import RuleCreate, RuleUpdate


'''
============================================
    Функции сервиса для Monitoring Rules    
============================================
'''


def get_rule(*, db: Session, rule_id: int, current_user: User) -> Optional[MonitoringRule]:
    """ Получает конкретное правило по ID, если оно принадлежит текущему пользователю """
    rule = rule_repository.get(db=db, rule_id=rule_id)
    if not rule or rule.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Правило не найдено или у вас нет к нему доступа"
        )
    return rule


def get_user_rules(*, db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[MonitoringRule]:
    """ Получает список правил текущего пользователя с пагинацией """
    return rule_repository.get_by_user(db=db, user_id=current_user.user_id, skip=skip, limit=limit)


def create_rule(*, db: Session, rule_in: RuleCreate, current_user: User) -> MonitoringRule:
    """ Создаёт новое правило мониторинга для текущего пользователя.
    Проверяет право доступа пользователя к указанному параметру. """
    # 1. Проверяет доступ к параметру, для которого создаётся правило
    scope = get_user_access_scope(db=db, user=current_user)
    if not can_user_access_parameter(db=db, scope=scope, target_parameter_id=rule_in.parameter_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для создания правила для этого параметра"
        )
    # 2. Вызывает метод репозитория для создания правила с указанием владельца
    new_rule = rule_repository.create_with_owner(db=db, obj_in=rule_in, user_id=current_user.user_id)
    return new_rule


def update_rule(*, db: Session, rule_id: int, rule_in: RuleUpdate, current_user: User) -> Optional[MonitoringRule]:
    """ Обновляет правило, если оно принадлежит текущему пользователю """
    # 1. Получает правило и проверяет права владения
    db_rule = get_rule(db=db, rule_id=rule_id, current_user=current_user)
    # 2. Проверяет, не пытается ли пользователь сменить parameter_id
    update_data = rule_in.model_dump(exclude_unset=True)
    if "parameter_id" in update_data and update_data["parameter_id"] != db_rule.parameter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Изменение параметра, к которому привязано правило, не допускается."
        )
    # 3. Вызывает универсальный update из репозитория
    return rule_repository.update(db=db, db_obj=db_rule, obj_in=update_data)


def delete_rule(*, db: Session, rule_id: int, current_user: User) -> Optional[MonitoringRule]:
    """ Удаляет правило, если оно принадлежит текущему пользователю """
    # 1. Получает правило и проверяет права владения
    db_rule = get_rule(db=db, rule_id=rule_id, current_user=current_user)  # noqa F841: Неиспользуемая переменная нужна для проверки прав доступа
    # 2. Удаляет правило через репозиторий
    return rule_repository.remove(db=db, rule_id=rule_id)


'''
====================================
    Функции для импорта/экспорта    
====================================
'''


def export_user_rules(*, db: Session, current_user: User) -> List[Dict[str, Any]]:
    """ Формирует данные правил пользователя для экспорта """
    rules = get_user_rules(db=db, current_user=current_user, limit=10000)
    export_data = []
    for rule in rules:
        export_data.append({
            "parameter_id": rule.parameter_id,
            "rule_name": rule.rule_name,
            "is_active": rule.is_active,
            "comparison_operator": rule.comparison_operator,
            "threshold": rule.threshold,
            # TODO: В БУДУЩЕМ можно будет добавить parameter_type_name, actuator_name и т.д.
        })
    return export_data


def import_user_rules(*, db: Session, current_user: User, rules_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """ Импортирует правила для пользователя, используя bulk insert """
    skipped_count = 0
    created_rules_count = 0
    scope = get_user_access_scope(db=db, user=current_user)
    rules_to_create: List[RuleCreate] = []

    for rule_data in rules_data:
        parameter_id = rule_data.get("parameter_id")
        if parameter_id is None: skipped_count += 1; continue
        if not can_user_access_parameter(db=db, scope=scope, target_parameter_id=parameter_id):
            skipped_count += 1; continue
        try:
            rule_in = RuleCreate(**rule_data)
            rules_to_create.append(rule_in)
        except Exception as e:
            print(f"Ошибка валидации данных правила для parameter_id {parameter_id}: {e}")
            skipped_count += 1

    if rules_to_create:
        try:
            created_rules = rule_repository.bulk_create_with_owner(
                db=db, rules_in=rules_to_create, user_id=current_user.user_id
            )
            created_rules_count = len(created_rules)
        except Exception as e:
            print(f"Ошибка при массовой вставке правил: {e}")
            db.rollback()

    print(f"Импорт завершен. Успешно создано: {created_rules_count}, Пропущено: {skipped_count}")
    return {"imported": created_rules_count, "skipped": skipped_count}