from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import json
from app.api import deps
from app.models.user import User as UserModel
from app.models.rule import MonitoringRule as MonitoringRuleModel
from app.schemas.rule import RuleCreate, RuleRead, RuleUpdate
from app.services import rule_service


router = APIRouter(prefix="/rules", tags=["Monitoring Rules"])


'''
======================================
    Эндпоинты для Monitoring Rules    
======================================
'''


@router.post("/", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
async def create_monitoring_rule(*, rule_in: RuleCreate, db: Session = Depends(deps.get_db),
                                 current_user: UserModel = Depends(deps.get_current_user)) -> MonitoringRuleModel:
    """ Создаёт новое правило мониторинга для текущего пользователя """
    new_rule = rule_service.create_rule(db=db, rule_in=rule_in, current_user=current_user)
    return new_rule


@router.get("/me/", response_model=List[RuleRead])
async def read_my_monitoring_rules(*, db: Session = Depends(deps.get_db),
                                   current_user: UserModel = Depends(deps.get_current_user),
                                   skip: int = 0, limit: int = 100) -> List[MonitoringRuleModel]:
    """ Получает список всех правил мониторинга, созданных текущим пользователем """
    rules = rule_service.get_user_rules(db=db, current_user=current_user, skip=skip, limit=limit)
    return rules


@router.get("/{rule_id}/", response_model=RuleRead)
async def read_monitoring_rule(*, rule_id: int, db: Session = Depends(deps.get_db),
                               current_user: UserModel = Depends(deps.get_current_user)) -> MonitoringRuleModel:
    """ Получает детали конкретного правила мониторинга по его ID.
    Доступно, только если правило принадлежит текущему пользователю. """
    rule = rule_service.get_rule(db=db, rule_id=rule_id, current_user=current_user)
    return rule


@router.put("/{rule_id}/", response_model=RuleRead)
async def update_monitoring_rule(*, rule_id: int, rule_in: RuleUpdate, db: Session = Depends(deps.get_db),
                                 current_user: UserModel = Depends(deps.get_current_user)) -> MonitoringRuleModel:
    """ Обновляет существующее правило мониторинга.
    Доступно, только если правило принадлежит текущему пользователю. """
    updated_rule = rule_service.update_rule(db=db, rule_id=rule_id, rule_in=rule_in, current_user=current_user)
    return updated_rule


@router.delete("/{rule_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitoring_rule(*, rule_id: int, db: Session = Depends(deps.get_db),
                                 current_user: UserModel = Depends(deps.get_current_user)) -> None:
    """ Удаляет правило мониторинга.
    Доступно, только если правило принадлежит текущему пользователю. """
    rule_service.delete_rule(db=db, rule_id=rule_id, current_user=current_user)


'''
=============================================
    Эндпоинты для импорта/экспорта правил    
=============================================
'''


@router.get("/me/export/", response_model=List[Dict[str, Any]])
async def export_my_rules(*, db: Session = Depends(deps.get_db),
                          current_user: UserModel = Depends(deps.get_current_user)) -> List[Dict[str, Any]]:
    """ Экспортирует все правила текущего пользователя в формате JSON """
    exported_rules = rule_service.export_user_rules(db=db, current_user=current_user)
    return exported_rules


@router.post("/me/import/", response_model=Dict[str, int])
async def import_rules(*, upload_file: UploadFile = File(...), db: Session = Depends(deps.get_db),
                          current_user: UserModel = Depends(deps.get_current_user)) -> Dict[str, int]:
    """ Импортирует правила из JSON файла.
    Файл должен содержать список объектов правил.
    Сервис проверяет права доступа к параметрам для каждого импортируемого правила.
    Возвращает количество импортированных и пропущенных правил.
    """
    if not upload_file.content_type == "application/json":
        raise HTTPException(status_code=400, detail="Неверный тип файла. Ожидается JSON.")
    try:
        contents = await upload_file.read()
        rules_data = json.loads(contents)
        if not isinstance(rules_data, list):
            raise HTTPException(status_code=400, detail="Содержимое файла должно быть списком правил.")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Не удалось декодировать JSON файл.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка чтения файла: {e}")
    finally:
        await upload_file.close()

    result = rule_service.import_user_rules(db=db, current_user=current_user, rules_data=rules_data)
    return result