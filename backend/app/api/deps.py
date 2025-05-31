from typing import Optional

from fastapi import Depends, HTTPException, status, Query, WebSocket
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
        user_role_from_payload = payload.get("role")
        if user_id_from_sub is None:
            raise credentials_exception

        token_data = TokenData(user_id=int(user_id_from_sub), role=user_role_from_payload)
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


async def get_current_user_ws(websocket: WebSocket, db: Session = Depends(get_db),
                              token: Optional[str] = Query(None)) -> Optional[User]:
    """ Зависимость для аутентификации пользователя в WebSocket-соединении через токен в query-параметре.
    Закрывает WebSocket с соответствующим кодом при ошибке. """
    credentials_exception_ws = status.WS_1008_POLICY_VIOLATION

    if token is None:
        print("WS Auth Error: Token not provided in query.")
        await websocket.close(code=credentials_exception_ws, reason="Token not provided")
        return None

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_from_sub: Optional[str] = payload.get("sub")
        user_role_from_payload: Optional[str] = payload.get("role")

        if user_id_from_sub is None:
            print("WS Auth Error: Token payload missing 'sub' (user_id).")
            await websocket.close(code=credentials_exception_ws, reason="Invalid token payload (sub missing)")
            return None

        token_data = TokenData(user_id=int(user_id_from_sub), role=user_role_from_payload)
    except JWTError:
        print("WS Auth Error: JWTError - Could not validate credentials.")
        await websocket.close(code=credentials_exception_ws, reason="Invalid token (JWTError)")
        return None
    except ValidationError:
        print("WS Auth Error: ValidationError for TokenData.")
        await websocket.close(code=credentials_exception_ws, reason="Invalid token data (ValidationError)")
        return None
    except ValueError:
        print("WS Auth Error: ValueError for user_id in token.")
        await websocket.close(code=credentials_exception_ws, reason="Invalid user_id format in token")
        return None

    user = user_service.get_user(db=db, user_id=token_data.user_id)
    if user is None:
        print(f"WS Auth Error: User with id {token_data.user_id} not found.")
        await websocket.close(code=credentials_exception_ws, reason="User not found")
        return None

    print(f"WS Auth Success: User {user.user_id} authenticated for WebSocket.")
    return user