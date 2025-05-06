import asyncio, json, nats, signal
from datetime import datetime
from nats.errors import NoServersError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
from app.repositories.parameter_repository import parameter_data_repository
from app.services.alert_service import process_new_parameter_data
from app.schemas.parameter import ParameterDataCreate


# --- Глобальное событие для остановки ---
stop_event = asyncio.Event()


def signal_handler(signum, frame):
    """ Обработчик сигналов для корректного завершения """
    print("\nCtrl+C или SIGTERM! Завершаю работу воркера...")
    stop_event.set()


async def message_handler(msg):
    """ Асинхронный обработчик входящих сообщений из NATS """
    subject = msg.subject
    data_str = msg.data.decode()
    print(f"WORKER: Получено [{subject}]: {data_str}")

    db: Session | None = None
    try:
        payload = json.loads(data_str)
        parameter_id = payload.get("parameter_id")
        parameter_value = payload.get("parameter_value")
        data_timestamp_iso = payload.get("data_timestamp")

        if not all([isinstance(parameter_id, int),
                    isinstance(parameter_value, (int, float)),
                    isinstance(data_timestamp_iso, str)]):
            print(f"WORKER: Некорректный формат данных: {payload}")
            await msg.ack()
            return

        data_timestamp = datetime.fromisoformat(data_timestamp_iso)

        db = SessionLocal()

        pd_create_schema = ParameterDataCreate(
            parameter_id=parameter_id,
            parameter_value=parameter_value,
            data_timestamp=data_timestamp
        )
        created_pd_entry = parameter_data_repository.create(db=db, obj_in=pd_create_schema)

        if not created_pd_entry or not created_pd_entry.parameter_data_id:
            print(f"WORKER: Ошибка сохранения ParameterData: {payload}")
            await msg.ack()
            return

        loop = asyncio.get_event_loop()
        await asyncio.to_thread(
            process_new_parameter_data,
            db,
            created_pd_entry.parameter_data_id
        )

        await msg.ack()
        print(f"WORKER: Сообщение для param_id={parameter_id} (pd_id={created_pd_entry.parameter_data_id}) обработано.")

    except json.JSONDecodeError:
        print(f"WORKER: Ошибка декодирования JSON: {data_str}")
        await msg.ack()
    except Exception as e:
        print(f"WORKER: Ошибка при обработке сообщения: {e}")
        await msg.ack()
    finally:
        if db: db.close()


async def run_worker():
    """ Основная асинхронная функция воркера """
    nc = None
    sub = None
    try:
        print(f"WORKER: Подключаюсь к NATS: {settings.NATS_URL}...")
        nc = await nats.connect(settings.NATS_URL, name="Alert Worker")
        print("WORKER: Успешно подключено к NATS.")
        js = nc.jetstream()
        print("WORKER: Получен контекст JetStream.")

        await js.add_stream(name=settings.NATS_STREAM, subjects=[settings.NATS_SUBJECT])
        print(f"WORKER: Stream '{settings.NATS_STREAM}' для subject '{settings.NATS_SUBJECT}' готов.")

        print(f"WORKER: Подписываюсь на '{settings.NATS_SUBJECT}' (durable: 'alert_proc_durable', queue: '{settings.NATS_QUEUE_GROUP}')...")
        sub = await js.subscribe(
            subject=settings.NATS_SUBJECT,
            durable="alert_processor_durable",
            queue=settings.NATS_QUEUE_GROUP,
            cb=message_handler
        )
        print("WORKER: Успешно подписан. Ожидаю сообщения...")

        while not stop_event.is_set():
            await asyncio.sleep(1)

    except NoServersError:
        print(f"WORKER: Ошибка NATS - нет серверов по {settings.NATS_URL}.")
    except Exception as e:
        print(f"WORKER: Критическая ошибка: {e}")
    finally:
        if sub:
            print("WORKER: Отписываюсь от NATS subject...")
            await sub.unsubscribe()
        if nc and nc.is_connected:
            print("WORKER: Закрываю соединение с NATS...")
            await nc.close()
        print("WORKER: Завершил работу.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("Запуск Alert Worker...")
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("Alert Worker принудительно остановлен (KeyboardInterrupt в main).")
    finally:
        if not stop_event.is_set():
            stop_event.set()