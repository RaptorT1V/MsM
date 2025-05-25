from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.config import settings
from app.schemas.token import Token
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=Token)
async def login_for_access_token(*, db: Session = Depends(get_db),
                                 form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    """ Аутентифицирует пользователя и возвращает JWT токен доступа.
    Принимает 'username' (который является email или телефоном) и 'password'. """
    user = auth_service.authenticate_user(db=db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email/телефон или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Создаёт токен доступа
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        db=db,
        user_id=user.user_id,
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")