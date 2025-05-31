from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.setting import UserSetting
from app.repositories.base import CRUDBase
from app.schemas.setting import SettingUpdate


# --- Репозиторий для CRUD операций с моделью UserSetting ---
class UserSettingRepository(CRUDBase[UserSetting, BaseModel, SettingUpdate]):

    def get(self, db: Session, *, user_id: int) -> Optional[UserSetting]:
        """ Получает настройки пользователя по user_id """
        return db.get(self.model, user_id)

    def get_or_create(self, db: Session, *, user_id: int) -> UserSetting:
        """ Получает настройки пользователя по ID.
        Если не существуют – создаёт запись с настройками по умолчанию и возвращает её. """
        instance = self.get(db=db, user_id=user_id)
        if instance:
            return instance

        new_settings = self.model(user_id=user_id)
        db.add(new_settings)
        db.commit()
        db.refresh(new_settings)
        return new_settings


# --- Экземпляр репозитория ---
setting_repository = UserSettingRepository(UserSetting)