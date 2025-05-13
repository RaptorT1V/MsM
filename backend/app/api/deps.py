from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenData
from app.services import user_service


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")  # URL для получения токена (будет создан в auth.py)


async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """ Зависимость для получения текущего пользователя на основе JWT токена.
    Декодирует токен, извлекает ID пользователя, получает пользователя из БД.
    Вызывает HTTPException при ошибках. """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_from_sub = payload.get("sub")
        if user_id_from_sub is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id_from_sub))
    except JWTError:
        raise credentials_exception
    except ValidationError:
        raise credentials_exception
    except ValueError:
        raise credentials_exception

    user = user_service.get_user(db=db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """ Проверяет, является ли текущий аутентифицированный пользователь администратором.
    Если нет - выбрасывает HTTPException 403. """
    if not current_user.job_title or \
       current_user.job_title.job_title_name not in settings.ADMIN_JOB_TITLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для выполнения этой операции"
        )
    return current_user