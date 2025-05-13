from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.api import deps
from app.models.user import User as UserModel
from app.services import user_service
from app.schemas.user import UserCreate, UserRead, UserUpdateAdmin, UserUpdatePassword


router = APIRouter(prefix="/users", tags=["Users"])


'''
===========================================
    Эндпоинты для текущего пользователя    
===========================================
'''


@router.get("/me", response_model=UserRead)
async def read_user_me(current_user: UserModel = Depends(deps.get_current_user)) -> UserModel:
    """ Получает данные текущего аутентифицированного пользователя """
    return current_user


@router.put("/me/password", status_code=status.HTTP_200_OK)
async def change_password_me(password_data: UserUpdatePassword, db: Session = Depends(deps.get_db),
                             current_user: UserModel = Depends(deps.get_current_user)) -> Dict[str, str]:
    """ Изменяет пароль текущего пользователя """
    user_service.change_password(db=db, current_user=current_user, password_data=password_data)
    return {"message": "Пароль успешно изменен"}


'''
=====================================
    Эндпоинты для администраторов    
=====================================
'''


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(user_in: UserCreate, db: Session = Depends(deps.get_db),
                               _current_admin: UserModel = Depends(deps.get_current_admin_user)) -> UserModel:
    """ Создаёт нового пользователя (только для админов) """
    db_user = user_service.create_user(db=db, user_in=user_in)
    return db_user


@router.get("/", response_model=List[UserRead])
async def read_users_by_admin(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db),
                              _current_admin: UserModel = Depends(deps.get_current_admin_user)) -> List[UserModel]:
    """ Получает список всех пользователей (только для админов) """
    users = user_service.get_all_users_admin(db=db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserRead)
async def read_user_by_admin(user_id: int,db: Session = Depends(deps.get_db),
                             _current_admin: UserModel = Depends(deps.get_current_admin_user)) -> UserModel:
    """ Получает данные конкретного пользователя по ID (только для админов) """
    db_user = user_service.get_user(db=db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return db_user


@router.put("/{user_id}", response_model=UserRead)
async def update_user_by_admin(user_id: int, user_in: UserUpdateAdmin, db: Session = Depends(deps.get_db),
                               _current_admin: UserModel = Depends(deps.get_current_admin_user)) -> UserModel:
    """ Обновляет данные пользователя по ID (только для админов) """
    user_to_update = user_service.get_user(db=db, user_id=user_id)
    if not user_to_update:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь для обновления не найден")
    updated_user = user_service.update_user(
        db=db, user_to_update=user_to_update, user_in=user_in
    )
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_admin(user_id: int, db: Session = Depends(deps.get_db),
                               _current_admin: UserModel = Depends(deps.get_current_admin_user)):
    """ Удаляет пользователя по ID (только для админов) """
    deleted_user = user_service.delete_user(db=db, user_id_to_delete=user_id)
    if not deleted_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь для удаления не найден")
    return Response(status_code=status.HTTP_204_NO_CONTENT)