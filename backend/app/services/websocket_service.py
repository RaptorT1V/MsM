from typing import Dict, Set

from fastapi import WebSocket


# --- Класс-менеджер, управляющий активными WebSocket-соединениями и подписками клиентов на параметры ---
class ConnectionManager:
    def __init__(self):
        """ Ключ - parameter_id, значение - множество активных WebSocket соединений """
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        print("[WS_Service]  ConnectionManager инициализирован.")

    async def connect(self, websocket: WebSocket, parameter_id: int):
        """ Регистрирует новое WebSocket-соединение для указанного parameter_id """
        await websocket.accept()
        if parameter_id not in self.active_connections:
            self.active_connections[parameter_id] = set()
        self.active_connections[parameter_id].add(websocket)
        print(f"[WS_Service]  Новое соединение для parameter_id={parameter_id}. Всего для параметра: {len(self.active_connections[parameter_id])}")

    def disconnect(self, websocket: WebSocket, parameter_id: int):
        """ Удаляет WebSocket-соединение из списка активных """
        if parameter_id in self.active_connections:
            self.active_connections[parameter_id].discard(websocket)
            if not self.active_connections[parameter_id]:
                del self.active_connections[parameter_id]
            print(f"[WS_Service]  Соединение закрыто для parameter_id={parameter_id}.")
        else:
            print(f"[WS_Service]  Не найдено активных соединений для parameter_id={parameter_id}, чтобы их удалить.")

    async def broadcast_to_parameter_subscribers(self, parameter_id: int, message_json: str):
        """ Отправляет JSON-сообщение всем WebSocket-клиентам, подписанным на данный parameter_id """
        if parameter_id in self.active_connections:
            living_connections: Set[WebSocket] = set()
            for connection in self.active_connections[parameter_id]:
                try:
                    await connection.send_text(message_json)
                    living_connections.add(connection)
                except Exception as e_broadcast_send:  # WebSocketException, ConnectionClosed, etc.
                    print(f"[WS_Service]  !!! ОШИБКА при отправке сообщения клиенту для parameter_id={parameter_id}.")
                    print(f"[WS_Service]  {type(e_broadcast_send).__name__} - {e_broadcast_send}. Соединение будет удалено при разрыве.")
            if living_connections:
                print(f"[WS_Service]  Отправлено {len(living_connections)} клиентам для parameter_id={parameter_id}: {message_json}")


connection_manager = ConnectionManager()