from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User as UserModel
from app.models.rule import Alert as AlertModel
from app.schemas.rule import AlertRead
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts"])


'''
==========================================
    Эндпоинты для управления тревогами    
==========================================
'''


@router.get("/me/", response_model=List[AlertRead])
async def read_my_alerts(*, db: Session = Depends(deps.get_db),
                         current_user: UserModel = Depends(deps.get_current_user),
                         skip: int = 0, limit: int = 100,
                         only_unread: bool = False) -> List[AlertModel]:
    """ Получает список тревог для текущего пользователя.
    Можно отфильтровать только непрочитанные. """
    alerts = alert_service.get_alerts_for_user(
        db=db, current_user=current_user, skip=skip, limit=limit, only_unread=only_unread
    )
    return alerts


@router.patch("/{alert_id}/read/", response_model=AlertRead)
async def mark_alert_as_read(*, alert_id: int, db: Session = Depends(deps.get_db),
                             current_user: UserModel = Depends(deps.get_current_user)) -> AlertModel:
    """ Помечает конкретную тревогу как прочитанную.
    Доступно только если тревога принадлежит правилу текущего пользователя. """
    updated_alert = alert_service.mark_specific_alert_as_read(
        db=db, alert_id=alert_id, current_user=current_user
    )
    if updated_alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тревога не найдена")
    return updated_alert


@router.post("/me/read-all/", response_model=Dict[str, int])
async def mark_all_my_alerts_as_read(*, db: Session = Depends(deps.get_db),
                                     current_user: UserModel = Depends(deps.get_current_user)) -> Dict[str, int]:
    """ Помечает все непрочитанные тревоги текущего пользователя как прочитанные.
    Возвращает количество помеченных тревог. """
    marked_count = alert_service.mark_all_user_alerts_as_read(
        db=db, current_user=current_user
    )
    return {"marked_as_read": marked_count}