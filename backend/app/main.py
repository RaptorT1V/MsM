import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitQueue

from app.api.routers import alerts, auth, equipment, parameters, rules, settings, users, websockets
from app.core.config import settings as app_settings
from app.services.websocket_service import connection_manager


# --- Инициализация FastStream для потребителя Websocket-данных внутри FastAPI ---
websocket_consumer_broker = RabbitBroker(app_settings.RABBITMQ_URL)

live_data_exchange_fastapi = RabbitExchange(
    name=app_settings.RABBITMQ_LIVE_DATA_EXCHANGE_NAME,
    type=ExchangeType.FANOUT,
    durable=True
)

websocket_consumer_queue = RabbitQueue(
    name="",
    durable=False,
    auto_delete=True,
    exclusive=True,
)


@websocket_consumer_broker.subscriber(queue=websocket_consumer_queue, exchange=live_data_exchange_fastapi)
async def _consume_live_data_for_ws(data: dict):
    """ Получает данные о значениях параметров из RabbitMQ и рассылает их соответствующим WebSocket-подписчикам """
    print(f"[FastAPI]  Получил live data через RabbitMQ: {data}")
    parameter_id_val = data.get("parameter_id")
    if parameter_id_val is not None:
        try:
            parameter_id_int = int(parameter_id_val)
            message_json = json.dumps(data)
            await connection_manager.broadcast_to_parameter_subscribers(parameter_id_int, message_json)
        except ValueError:
            print(f"[FastAPI]  !!! ОШИБКА: Неверный формат parameter_id в сообщении: {parameter_id_val}")
        except Exception as e_broadcast:
             print(f"[FastAPI]  !!! ОШИБКА во время рассылки для parameter_id {parameter_id_val}: {e_broadcast}")
    else:
        print(f"[FastAPI]  Получено сообщение без parameter_id: {data}")


@asynccontextmanager
async def lifespan(_app_instance: FastAPI):
    """ Управляет жизненным циклом WebSocket consumer-брокера в FastAPI.
    При запуске приложения инициализирует и запускает брокер, при остановке - корректно его закрывает. """
    print("[FastAPI]  Lifespan запускается...")
    print("[FastAPI]  Попытка создать WebSocket consumer broker...")
    try:
        await websocket_consumer_broker.connect()
        print(f"[FastAPI]  Объявляю exchange '{live_data_exchange_fastapi.name}' для WebSocket consumer...")
        await websocket_consumer_broker.declare_exchange(live_data_exchange_fastapi)
        print(f"[FastAPI]  Объявляю очередь для WebSocket consumer...")
        await websocket_consumer_broker.declare_queue(websocket_consumer_queue)
        print(f"[FastAPI]  Очередь для WebSocket consumer успешно объявлена.")
        await websocket_consumer_broker.start()
        print("[FastAPI]  WebSocket consumer broker успешно запущен.")
    except Exception as e:
        print(f"[FastAPI]  !!! ОШИБКА при запуске WebSocket consumer broker: {type(e).__name__} - {e}")
    yield
    print("- - - - - -\n[FastAPI]  Приложение FastAPI останавливается...")
    print("[FastAPI]  Попытка закрыть WebSocket consumer broker...")
    try:
        await websocket_consumer_broker.close()
        print("[FastAPI]  WebSocket consumer broker успешно закрыт.")
    except Exception as e:
        print(f"[FastAPI]  !!! ОШИБКА при закрытии WebSocket consumer broker: {type(e).__name__} - {e}")


# --- Описание приложения ---
description = """
    API мобильной системы мониторинга (MsM) помогает пользователям 
    следить за техническими параметрами технологического оборудования! 🚀

    Вы сможете:
        - Аутентифицироваться и управлять своим профилем;
        - Просматривать иерархию оборудования (цехи, линии, агрегаты, актуаторы);
        - Просматривать параметры для актуаторов и их значения;
        - Создавать и управлять правилами мониторинга для параметров;
        - Получать и просматривать тревоги, сработавшие по вашим правилам;
        - Строить графики параметров в оффлайн и онлайн режимах.
"""


# --- Создание экземпляра FastAPI ---
app = FastAPI(
    title="MsM – мобильная система мониторинга (API)",
    description=description,
    version="0.1.0",
    lifespan=lifespan,
    # openapi_url=f"{app_settings.API_V1_STR}/openapi.json"
    # docs_url="/docs",
    # redoc_url="/redoc"
)


# --- Настройка CORS (Cross-Origin Resource Sharing) ---
if app_settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=[str(origin) for origin in app_settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["*"],  # TODO: Для production это небезопасно!
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --- Подключение роутеров ---
api_prefix = ""  # Пока без общего префикса
    # api_prefix = "/api/v1"

app.include_router(auth.router, prefix=f"{api_prefix}", tags=["Authentication"])
app.include_router(users.router, prefix=f"{api_prefix}", tags=["Users"])
app.include_router(settings.router, prefix=f"{api_prefix}", tags=["User Settings"])
app.include_router(equipment.router, prefix=f"{api_prefix}", tags=["Equipment Hierarchy"])
app.include_router(parameters.router, prefix=f"{api_prefix}", tags=["Parameters & Data"])
app.include_router(rules.router, prefix=f"{api_prefix}", tags=["Monitoring Rules"])
app.include_router(alerts.router, prefix=f"{api_prefix}", tags=["Alerts"])
app.include_router(websockets.router, prefix=f"{api_prefix}", tags=["WebSockets"])

print("[FastAPI]  Роутеры подключены.")