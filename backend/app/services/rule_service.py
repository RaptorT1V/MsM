from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.rule import MonitoringRule
from app.models.user import User
from app.repositories.rule_repository import rule_repository
from app.schemas.rule import RuleCreate, RuleUpdate
from app.services.permissions import get_user_access_scope, can_user_access_parameter


'''
==============================================
    Сервисные функции для Monitoring Rules    
==============================================
'''


def get_rule(*, db: Session, rule_id: int, current_user: User) -> Optional[MonitoringRule]:
    """ Получает конкретное правило по ID, если оно принадлежит текущему пользователю (админам можно всё) """
    rule = rule_repository.get(db=db, rule_id=rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Правило не найдено"
        )

    is_admin = False
    if current_user.job_title and current_user.job_title.job_title_name in settings.ADMIN_JOB_TITLES:
        is_admin = True

    if rule.user_id != current_user.user_id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет доступа к этому правилу"
        )
    return rule


def get_user_rules(*, db: Session, current_user: User, skip: int = 0, limit: int = 100) -> List[MonitoringRule]:
    """ Получает список правил текущего пользователя с пагинацией """
    rules = rule_repository.get_by_user(db=db, user_id=current_user.user_id, skip=skip, limit=limit)
    return rules


def create_rule(*, db: Session, rule_in: RuleCreate, current_user: User) -> MonitoringRule:
    """ Создаёт новое правило мониторинга для текущего пользователя.
    Проверяет право доступа пользователя к указанному параметру. """
    scope = get_user_access_scope(db=db, user=current_user)
    if not can_user_access_parameter(db=db, scope=scope, target_parameter_id=rule_in.parameter_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Нет прав для создания правила для этого параметра"
        )

    try:
        new_rule = rule_repository.create_with_owner(db=db, obj_in=rule_in, user_id=current_user.user_id)
        return new_rule
    except IntegrityError as e:
        db.rollback()
        if hasattr(e.orig, 'diag') and hasattr(e.orig.diag, 'constraint_name') and \
           e.orig.diag.constraint_name == 'uq_monitoring_rules_user_parameter_operator_threshold':  # noqa
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Правило с такими параметрами (параметр, оператор, порог) для вас уже существует."
            )
        print(f"IntegrityError during rule creation: {e.orig}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка базы данных при создании правила."
        )
    except Exception as e:
        db.rollback()
        print(f"Unexpected error during rule creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Непредвиденная ошибка при создании правила."
        )


def update_rule(*, db: Session, rule_id: int, rule_in: RuleUpdate, current_user: User) -> Optional[MonitoringRule]:
    """ Обновляет правило, если оно принадлежит текущему пользователю """
    db_rule = get_rule(db=db, rule_id=rule_id, current_user=current_user)

    update_data = rule_in.model_dump(exclude_unset=True)
    if "parameter_id" in update_data and update_data["parameter_id"] != db_rule.parameter_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Изменение параметра, к которому привязано правило, не допускается."
        )

    updated_rule = rule_repository.update(db=db, db_obj=db_rule, obj_in=update_data)
    return updated_rule


def delete_rule(*, db: Session, rule_id: int, current_user: User) -> Optional[MonitoringRule]:
    """ Удаляет правило, если оно принадлежит текущему пользователю """
    db_rule_to_delete = get_rule(db=db, rule_id=rule_id, current_user=current_user)

    deleted_rule = rule_repository.remove(db=db, rule_id=db_rule_to_delete.rule_id)
    return deleted_rule


'''
=====================================================
    Сервисные функции для импорта/экспорта правил    
=====================================================
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
    """ Импортирует созданные кем-то правила для пользователя, используя bulk insert """
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