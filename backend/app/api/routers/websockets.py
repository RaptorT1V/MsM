from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from app.api import deps
from app.db.session import get_db
from app.models.user import User as UserModel
from app.services.permissions import get_user_access_scope, can_user_access_parameter
from app.services.websocket_service import connection_manager


router = APIRouter(prefix="/ws", tags=["WebSockets"])


# --- WebSocket Эндпоинт ---
@router.websocket("/live_data/{parameter_id_str}")
async def websocket_endpoint(websocket: WebSocket, parameter_id_str: str,
                             current_user: UserModel = Depends(deps.get_current_user_ws),
                             db: Session = Depends(get_db)):
    """ WebSocket-эндпоинт для подписки на real-time обновления данных конкретного параметра.
    Аутентификация обязательна. """
    if not current_user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
        return

    try:
        parameter_id = int(parameter_id_str)
    except ValueError:
        await websocket.close(code=status.WS_1007_INVALID_FRAME_PAYLOAD_DATA, reason="Invalid parameter ID format")
        return

    user_scope = get_user_access_scope(db=db, user=current_user)
    if not can_user_access_parameter(scope=user_scope, target_parameter_id=parameter_id, db=db):
        print(f"[WS_Endpoint]  User {current_user.user_id} - Access DENIED for parameter_id: {parameter_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Access Denied to parameter")
        return

    print(f"[WS_Endpoint]  User {current_user.user_id} connected for parameter_id: {parameter_id}")
    await connection_manager.connect(websocket, parameter_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WS_Endpoint]  User {current_user.user_id} for parameter_id={parameter_id} sent: {data}")
            if data.lower() == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        print(f"[WS_Endpoint]  User {current_user.user_id} disconnected from parameter_id: {parameter_id}")
    except Exception as e:
        print(f"[WS_Endpoint]  Error for user {current_user.user_id}, parameter_id={parameter_id}: {type(e).__name__} - {e}")
    finally:
        connection_manager.disconnect(websocket, parameter_id)
        print(f"[WS_Endpoint]  Connection for user {current_user.user_id}, parameter_id={parameter_id} removed from manager.")