from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.setting import UserSetting as UserSettingModel
from app.models.user import User as UserModel
from app.schemas.setting import SettingRead, SettingUpdate
from app.services import setting_service


router = APIRouter(prefix="/settings", tags=["User Settings"])


@router.get("/me", response_model=SettingRead)
async def read_settings_me(*, db: Session = Depends(deps.get_db),
                           current_user: UserModel = Depends(deps.get_current_user)) -> UserSettingModel:
    """ Получает настройки текущего пользователя """
    settings = setting_service.get_settings(db=db, current_user=current_user)
    return settings


@router.put("/me", response_model=SettingRead)
async def update_settings_me(*, db: Session = Depends(deps.get_db), settings_in: SettingUpdate,
                             current_user: UserModel = Depends(deps.get_current_user)) -> UserSettingModel:
    """ Обновляет настройки текущего пользователя """
    updated_settings = setting_service.update_settings(
        db=db, current_user=current_user, settings_in=settings_in
    )
    return updated_settings