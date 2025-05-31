import asyncio, signal
from typing import Optional

from faststream import FastStream
from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange, RabbitMessage, RabbitQueue
from sqlalchemy.orm import Session

import app.db.base  # noqa F401
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.parameter_repository import parameter_data_repository
from app.services.alert_service import process_new_parameter_data
from app.schemas.parameter import ParameterDataCreate


# --- Инициализация брокера и приложения FastStream ---
broker = RabbitBroker(settings.RABBITMQ_URL)
app = FastStream(broker)  # noqa

worker_alert_queue = RabbitQueue(
    name=settings.RABBITMQ_QUEUE_NAME,
    durable=True,
    auto_delete=False,
)

worker_live_data_exchange = RabbitExchange(
    name=settings.RABBITMQ_LIVE_DATA_EXCHANGE_NAME,
    type=ExchangeType.FANOUT,
    durable=True
)

print(f"[WORKER]  Брокер RabbitMQ '{settings.RABBITMQ_URL}' и очередь '{worker_alert_queue.name}' были сконфигурированы.")


# --- Обработчики жизненного цикла приложения ---
@app.on_startup
async def on_startup():
    """ Выполняется при старте приложения FastStream """
    print("[WORKER]  @app.on_startup - приложение FastStream запускается.")
    try:
        print(f"[WORKER]  Попытка объявить fanout exchange '{worker_live_data_exchange.name}'...")
        await broker.declare_exchange(worker_live_data_exchange)
        print(f"[WORKER]  Fanout exchange '{worker_live_data_exchange.name}' успешно объявлен (или уже существует).")
    except Exception as e_declare_exch:
        print(f"[WORKER]  !!! ОШИБКА при объявлении fanout exchange: '{type(e_declare_exch).__name__}' - '{e_declare_exch}'")
        return

    try:
        print(f"[WORKER]  Попытка объявить очередь '{worker_alert_queue.name}' и привязать ее к exchange '{worker_live_data_exchange.name}'...")
        await broker.declare_queue(worker_alert_queue)
        print(f"[WORKER]  Очередь '{worker_alert_queue.name}' объявлена и привязана к exchange.")
    except Exception as e_declare:
        print(f"[WORKER]  !!! ОШИБКА при объявлении exchange/очереди/привязки: '{type(e_declare).__name__}' - '{e_declare}'")


@app.on_shutdown
async def on_shutdown():
    """ Выполняется при остановке приложения FastStream """
    print("[WORKER]  @app.on_shutdown - приложение FastStream останавливается.")


# --- Подписчик на очередь RabbitMQ ---
@broker.subscriber(queue=worker_alert_queue, exchange=worker_live_data_exchange)
async def handle_data_message(msg_data: dict, message: RabbitMessage):
    """ Асинхронно обрабатывает входящие сообщения с данными параметров из RabbitMQ.
    Сообщение сначала сохраняется в базу данных, затем передается в сервис для проверки правил мониторинга. """
    print(f"[WORKER]  ==> Получено сообщение (ID={message.message_id}): {msg_data}")
    db_for_create: Optional[Session] = None
    created_pd_id: Optional[int] = None
    parameter_id_for_log: Optional[int] = msg_data.get("parameter_id")

    # 1: Сохранение данных параметра в БД
    try:
        print(f"[WORKER]  Начало Этапа 1 для parameter_id = {parameter_id_for_log}")
        pd_create_schema = ParameterDataCreate(**msg_data)
        db_for_create = SessionLocal()
        created_pd_entry = parameter_data_repository.create(db=db_for_create, obj_in=pd_create_schema)
        created_pd_id = created_pd_entry.parameter_data_id
        await message.ack()
        print(f"[WORKER]  ParameterData с ID = {created_pd_id} сохранён в БД. Сообщение подтверждено (acked).")
    except Exception as e_stage1:
        print(f"[WORKER]  !!! ОШИБКА Этапа 1 (сохранение ParameterData) для param_id={parameter_id_for_log}, data={msg_data}: '{type(e_stage1).__name__}' - '{e_stage1}'")
        if db_for_create:
            db_for_create.rollback()
        try:
            await message.reject(requeue=False)
            print(f"[WORKER]  Проблемное сообщение для param_id={parameter_id_for_log} отклонено.")
        except Exception as e_reject:
            print(f"[WORKER]  !!! ОШИБКА при отклонении проблемного сообщения для param_id={parameter_id_for_log}: '{e_reject}'")
        return
    finally:
        if db_for_create:
            db_for_create.close()

    # 2: Запуск обработки правил мониторинга
    if created_pd_id is not None:
        try:
            print(f"[WORKER]  Начало Этапа 2 - запуск обработки правил для ParameterData с ID={created_pd_id}")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, process_new_parameter_data, created_pd_id)
            print(f"[WORKER]  Этап 2 - Обработка правил для ParameterData с ID = {created_pd_id} - успешно завершён.")
        except Exception as e_process_alert:
            print(f"[WORKER]  !!! КРИТИЧЕСКАЯ ОШИБКА Этапа 2 (alert_service) для pd_id={created_pd_id} (param_id={parameter_id_for_log}): '{type(e_process_alert).__name__}' - '{e_process_alert}'")


# --- Главная асинхронная функция запуска воркера ---
async def run_worker_main_loop():
    """ Основная функция для запуска и управления жизненным циклом FastStream брокера.
    Настраивает обработчики сигналов для корректного завершения. """
    print("[WORKER]  Инициализация run_worker_main_loop...")
    loop = asyncio.get_running_loop()
    stop_event_main_loop = asyncio.Event()

    def _graceful_shutdown_signal_handler(signal_name: str):
        """ Обрабатывает сигнал завершения `signal_name` и инициирует корректное завершение брокера """
        print(f"[WORKER]  Сигнал '{signal_name}' получен. Инициализирую graceful shutdown...")
        if not stop_event_main_loop.is_set():
            stop_event_main_loop.set()
            asyncio.create_task(broker.close())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda s_name=sig.name: _graceful_shutdown_signal_handler(s_name))
        except (NotImplementedError, AttributeError):
            print(f"[WORKER]  Не удалось установить signal handler для {sig} через asyncio loop. Использую signal.signal().")
            signal.signal(sig, lambda s, f: _graceful_shutdown_signal_handler(signal.Signals(s).name))

    try:
        print("[WORKER]  Попытка запустить брокер RabbitMQ и активация подписчиков...")
        await broker.start()
        print("[WORKER]  Брокер успешно стартанул. Воркер активен и слушает сообщения.")
        await stop_event_main_loop.wait()
        print("[WORKER]  Остановка event set, выход из main_loop.")
    except Exception as e:
        print(f"[WORKER]  !!! ОШИБКА при запуске брокера или же в главном цикле работы брокера: '{type(e).__name__}' - '{e}'")
    finally:
        if broker and hasattr(broker, 'close') and callable(broker.close):
            if getattr(broker, '_connection', None) is not None or getattr(broker, '_channel', None) is not None:
                print("[WORKER]  Попытка закрыть брокер FastStream...")
                try:
                    await broker.close()
                    print("[WORKER]  Брокер FastStream успешно закрыт.")
                except Exception as e_close:
                    print(f"[WORKER]  !!! ОШИБКА при закрытии брокера: '{type(e_close).__name__}' - '{e_close}'")
            else:
                print("[WORKER]  Соединение с брокером, кажется, уже закрыто или вообще не было установлено.")
        else:
            print("[WORKER]  Объект брокера недоступен или не может быть закрыт.")
        print("[WORKER]  Главный цикл работы alert_worker завершён.")


if __name__ == "__main__":
    print("[WORKER]  Выполнение скрипта начинается (__main__)")
    asyncio.run(run_worker_main_loop())