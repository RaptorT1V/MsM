from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserCreate, UserUpdateAdmin, UserUpdatePassword
from app.services.auth_service import get_password_hash, verify_password


def create_user(*, db: Session, user_in: UserCreate) -> User:
    """ Создаёт нового пользователя в БД.
    Выполняет проверку на уникальность email/телефона.
    Хеширует пароль перед сохранением. """
    existing_user = user_repository.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует.",
        )

    existing_user_phone = user_repository.get_by_phone(db, phone=user_in.phone)
    if existing_user_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким номером телефона уже существует.",
        )

    hashed_password = get_password_hash(user_in.password)
    db_user = user_repository.create_user(
        db=db, obj_in=user_in, hashed_password=hashed_password
    )
    return db_user


def change_password(*, db: Session, current_user: User, password_data: UserUpdatePassword) -> bool:
    """ Изменяет пароль для текущего пользователя (выполняется пользователем).
    Проверяет старый пароль перед установкой нового. """
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный текущий пароль"
        )

    new_hashed_password = get_password_hash(password_data.new_password)
    user_repository.update(
        db=db, db_obj=current_user, obj_in={"password_hash": new_hashed_password}
    )
    return True


def update_user(*, db: Session, user_to_update: User, user_in: UserUpdateAdmin) -> User:
    """ Обновляет данные пользователя (выполняется администратором).
    Проверяет уникальность email/телефона, если они изменяются. """
    update_data = user_in.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] != user_to_update.email:
        existing_user = user_repository.get_by_email(db, email=update_data["email"])
        if existing_user and existing_user.user_id != user_to_update.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Этот email уже занят другим пользователем.",
            )

    if "phone" in update_data and update_data["phone"] != user_to_update.phone:
        existing_user_phone = user_repository.get_by_phone(db, phone=update_data["phone"])
        if existing_user_phone and existing_user_phone.user_id != user_to_update.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Этот номер телефона уже занят другим пользователем.",
            )

    updated_user = user_repository.update(
        db=db, db_obj=user_to_update, obj_in=update_data
    )
    return updated_user


def get_user(*, db: Session, user_id: int) -> Optional[User]:
    """ Получает пользователя по ID (для админа) """
    return user_repository.get(db=db, user_id=user_id)


def get_all_users_admin(db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
    """ Получает список всех пользователей (для админа) """
    return user_repository.get_multi(db=db, skip=skip, limit=limit)


def delete_user(*, db: Session, user_id_to_delete: int, current_admin_user: User) -> Optional[User]:
    """ Удаляет пользователя по ID (для админа).
    Администратор не может удалить сам себя и не может удалить последнего админа в системе.
    Возвращает удаленный объект User или None, если пользователь не найден. """
    user_to_delete = user_repository.get(db=db, user_id=user_id_to_delete)

    # Если должностей администратора всего 1 (например "админ" ИЛИ "директор"), такая проверка сойдёт.
    if user_to_delete and user_to_delete.job_title and user_to_delete.job_title.job_title_name in settings.ADMIN_JOB_TITLES:
        admin_role_id = user_to_delete.job_title_id
        admins_count = db.query(User).filter(User.job_title_id == admin_role_id).count()
        if admins_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Нельзя удалить последнего администратора в системе."
            )

    if user_id_to_delete == current_admin_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Администратор не может удалить свой собственный аккаунт."
        )

    deleted_user = user_repository.remove(db=db, user_id=user_id_to_delete)
    return deleted_user