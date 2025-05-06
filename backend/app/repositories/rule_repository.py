from typing import Any, Dict, Optional, Union, List, cast
from sqlalchemy import select, update as sqlalchemy_update
from sqlalchemy.orm import Session
from app.models.rule import Alert, MonitoringRule
from app.repositories.base import CRUDBase
from app.schemas.rule import AlertCreateInternal, AlertUpdate, RuleCreate, RuleUpdate


'''
========================================
    Репозиторий для Monitoring Rules     
========================================
'''


# --- Репозиторий для CRUD операций с моделью MonitoringRule ---
class MonitoringRuleRepository(CRUDBase[MonitoringRule, RuleCreate, RuleUpdate]):

    def get(self, db: Session, *, rule_id: int) -> Optional[MonitoringRule]:
        """ Получает правило по ID """
        return db.get(self.model, rule_id)

    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[MonitoringRule]:
        """ Получает список правил для конкретного пользователя с пагинацией """
        statement = (select(self.model).where(self.model.user_id == user_id).order_by(self.model.rule_id).offset(skip).limit(limit))
        result = db.execute(statement)
        return cast(List[MonitoringRule], result.scalars().all())

    def get_by_parameter(self, db: Session, *, parameter_id: int, skip: int = 0, limit: int = 100) -> List[MonitoringRule]:
        """ Получает список правил для конкретного параметра с пагинацией """
        statement = (select(self.model).where(self.model.parameter_id == parameter_id).order_by(self.model.rule_id).offset(skip).limit(limit))
        result = db.execute(statement)
        return cast(List[MonitoringRule], result.scalars().all())

    def get_active_by_parameter(self, db: Session, *, parameter_id: int) -> List[MonitoringRule]:
        """ Получает ВСЕ АКТИВНЫЕ правила для конкретного параметра (для проверки тревог) """
        statement = select(self.model).where(self.model.parameter_id == parameter_id, self.model.is_active == True)
        result = db.execute(statement)
        return cast(List[MonitoringRule], result.scalars().all())

    def create_with_owner(self, db: Session, *, obj_in: RuleCreate, user_id: int) -> MonitoringRule:
        """ Создаёт новое правило, указав владельца """
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data, user_id=user_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def bulk_create_with_owner(self, db: Session, *, rules_in: List[RuleCreate], user_id: int) -> List[MonitoringRule]:
        """ Массово создаёт правила для пользователя """
        objects_to_create = []
        for rule_schema in rules_in:
            obj_in_data = rule_schema.model_dump()
            db_obj = self.model(**obj_in_data, user_id=user_id)
            objects_to_create.append(db_obj)

        if not objects_to_create:
            return []
        db.add_all(objects_to_create)
        db.commit()
        return objects_to_create

    def remove(self, db: Session, *, rule_id: int) -> Optional[MonitoringRule]:
        """ Удаляет правило по ID """
        obj = self.get(db=db, rule_id=rule_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


'''
==============================
    Репозиторий для Alerts    
==============================
'''


# --- Репозиторий для CRUD операций с моделью Alert ---
class AlertRepository(CRUDBase[Alert, AlertCreateInternal, AlertUpdate]):

    def get(self, db: Session, *, alert_id: int) -> Optional[Alert]:
        """ Получает тревогу по ID """
        return db.get(self.model, alert_id)

    def get_by_user(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100, only_unread: bool = False) -> List[Alert]:
        """ Получает список тревог для конкретного пользователя (через правило) с пагинацией """
        statement = (select(self.model).join(MonitoringRule).where(MonitoringRule.user_id == user_id))

        if only_unread:
            statement = statement.where(self.model.is_read == False)

        statement = statement.order_by(self.model.alert_timestamp.desc()).offset(skip).limit(limit)
        result = db.execute(statement)
        return cast(List[Alert], result.scalars().all())

    def mark_as_read(self, db: Session, *, db_obj: Alert) -> Alert:
        """ Отмечает тревогу как прочитанную """
        return self.update(db=db, db_obj=db_obj, obj_in={"is_read": True})

    def mark_all_as_read_for_user(self, db: Session, *, user_id: int) -> int:
        """ Отмечает все тревоги пользователя как прочитанные """
        statement = (
            sqlalchemy_update(self.model)
            .where(self.model.rule_id.in_(
                select(MonitoringRule.rule_id).where(MonitoringRule.user_id == user_id))
            )
            .where(self.model.is_read == False)
            .values(is_read=True)
            .execution_options(synchronize_session="fetch")
        )
        result = db.execute(statement)
        db.commit()
        return cast(int, result.rowcount)

    def remove(self, db: Session, *, alert_id: int) -> Optional[Alert]:
        """ Удаляет тревогу по ID """
        obj = self.get(db=db, alert_id=alert_id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj


# --- Экземпляры репозиториев ---
rule_repository = MonitoringRuleRepository(MonitoringRule)
alert_repository = AlertRepository(Alert)