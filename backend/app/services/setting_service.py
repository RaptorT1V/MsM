from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.setting import UserSetting
from app.repositories.setting_repository import setting_repository
from app.schemas.setting import SettingUpdate


def get_settings(*, db: Session, current_user: User) -> UserSetting:
    """ Получает настройки для указанного пользователя.
    Если настроек нет, создаёт их со значениями по умолчанию. """
    settings = setting_repository.get_or_create(db=db, user_id=current_user.user_id)
    return settings


def update_settings(*, db: Session, current_user: User, settings_in: SettingUpdate) -> UserSetting:
    """ Обновляет настройки для текущего пользователя.
    Принимает Pydantic схему SettingUpdate с полями для обновления. """
    current_settings = setting_repository.get_or_create(db=db, user_id=current_user.user_id)
    if not current_settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Настройки для данного пользователя не найдены.",
        )

    updated_settings = setting_repository.update(db=db, db_obj=current_settings, obj_in=settings_in)
    return updated_settings