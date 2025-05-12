from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User
from app.repositories.base import CRUDBase
from app.schemas.user import UserCreate, UserUpdateAdmin


# --- Репозиторий для работы с пользователями ---
class UserRepository(CRUDBase[User, UserCreate, UserUpdateAdmin]):

    def get(self, db: Session, *, user_id: int) -> Optional[User]:
        """ Получает пользователя по его ID (pk_users) """
        return db.get(self.model, user_id)

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """ Получает пользователя по email """
        statement = select(self.model).where(self.model.email == email)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def get_by_phone(self, db: Session, *, phone: str) -> Optional[User]:
        """ Получает пользователя по телефону """
        statement = select(self.model).where(self.model.phone == phone)
        result = db.execute(statement)
        return result.scalar_one_or_none()

    def create_user(self, db: Session, *, obj_in: UserCreate, hashed_password: str) -> User:
        """ Создаёт нового пользователя """
        create_data = obj_in.model_dump()
        create_data.pop('password', None)
        db_obj = self.model(**create_data, password_hash=hashed_password)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, user_id: int) -> Optional[User]:
        """ Удаляет пользователя по его ID """
        obj = self.get(db=db, user_id=user_id)
        if obj:
            try:
                db.delete(obj)
                db.commit()
                return obj
            except Exception as e:
                print(f"Ошибка при удалении User {user_id}: {e}")
                db.rollback()
                return None
        return None


# --- Экземпляры репозиториев ---
user_repository = UserRepository(User)