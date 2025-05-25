import asyncio, json, nats, signal
from datetime import datetime
from typing import Optional
from nats.errors import NoServersError, TimeoutError
from nats.js.errors import APIError as JetStreamAPIError
from nats.js.api import AckPolicy, ConsumerConfig, DeliverPolicy, ReplayPolicy, RetentionPolicy
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
    print(f"WORKER: Получено [{subject}]: '{data_str}'")

    # №1: Валидация, сохранение в БД и немедленное подтверждение сообщения
    db_for_create: Optional[Session] = None
    created_pd_id: Optional[int] = None
    parameter_id_for_log: Optional[int] = None
    try:
        payload = json.loads(data_str)
        parameter_id, parameter_id_for_log = payload.get("parameter_id"), payload.get("parameter_id")
        parameter_value, data_timestamp_iso = payload.get("parameter_value"), payload.get("data_timestamp")

        if not all([isinstance(parameter_id, int),
                    isinstance(parameter_value, (int, float)),
                    isinstance(data_timestamp_iso, str)]):
            print(f"WORKER: Некорректный формат данных, сообщение будет проигнорировано: {payload}")
            await msg.ack()
            return

        data_timestamp = datetime.fromisoformat(data_timestamp_iso)
        pd_create_schema = ParameterDataCreate(
            parameter_id=parameter_id,
            parameter_value=parameter_value,
            data_timestamp=data_timestamp
        )

        db_for_create = SessionLocal()
        created_pd_entry = parameter_data_repository.create(db=db_for_create, obj_in=pd_create_schema)
        created_pd_id = created_pd_entry.parameter_data_id

        await msg.ack()
        print(f"WORKER: ParameterData ID={created_pd_id} успешно сохранен. Сообщение NATS подтверждено.")

    except Exception as e_stage1:
        print(f"WORKER: Ошибка на Этапе 1 (парсинг/сохранение): {type(e_stage1).__name__} - {e_stage1}")
        if db_for_create:
            db_for_create.rollback()
        await msg.ack()
        return
    finally:
        if db_for_create:
            db_for_create.close()

    # №2: Запуск обработки правил (если данные были успешно сохранены)
    if created_pd_id is not None:
        try:
            print(f"WORKER: Запуск обработки правил для ParameterData ID: {created_pd_id}")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                process_new_parameter_data,
                created_pd_id
            )
        except Exception as e_process_alert:
            print(f"WORKER: КРИТИЧЕСКАЯ ОШИБКА в alert_service для pd_id={created_pd_id}: {type(e_process_alert).__name__} - {e_process_alert}")


async def run_worker():
    """ Основная асинхронная функция воркера """
    nc = None
    sub = None
    print(f"WORKER: Используется NATS_QUEUE_GROUP: '{settings.NATS_QUEUE_GROUP}'")
    while not stop_event.is_set():
        try:
            print(f"WORKER: Попытка подключения к NATS: {settings.NATS_URL}...")
            nc = await nats.connect(settings.NATS_URL, name="Alert Worker", reconnect_time_wait=5, allow_reconnect=True,
                                    max_reconnect_attempts=-1)
            js = nc.jetstream(timeout=10)
            print("WORKER: Успешно подключено к NATS и JetStream.")

            stream_name = settings.NATS_STREAM
            durable_name = "alert_processor_durable"
            queue_group_name = settings.NATS_QUEUE_GROUP
            subscribe_subject = settings.NATS_SUBJECT

            # 1. Проверка/создание стрима
            try:
                await js.stream_info(stream_name)
                print(f"WORKER: Stream '{stream_name}' уже существует.")
            except JetStreamAPIError as e_js_api:
                if e_js_api.err_code == 10059:
                    print(f"WORKER: Stream '{stream_name}' не найден (err_code={e_js_api.err_code}). Создаю новый...")
                    await js.add_stream(name=stream_name, subjects=[subscribe_subject],
                                        retention=RetentionPolicy.WORK_QUEUE)
                    print(f"WORKER: Stream '{stream_name}' успешно создан.")
                else:
                    print(f"WORKER: Неожиданная ошибка API JetStream при проверке стрима: {e_js_api}")
                    raise

            # 2. Удаление существующего консьюмера (для чистоты эксперимента на каждой попытке)
            try:
                print(f"WORKER: Попытка удалить существующий consumer '{durable_name}' для чистоты эксперимента...")
                await js.delete_consumer(stream=stream_name, consumer=durable_name)
                print(f"WORKER: Consumer '{durable_name}' успешно удален.")
            except JetStreamAPIError as e_del_cons:
                if e_del_cons.err_code == 10014:
                    print(f"WORKER: Consumer '{durable_name}' не найден, будет создан новый.")
                else:
                    print(
                        f"WORKER: Ошибка при попытке удалить consumer '{durable_name}': {e_del_cons}. Это может быть не критично.")
            except Exception as e_other_del:
                print(f"WORKER: Непредвиденная ошибка при удалении consumer '{durable_name}': {e_other_del}")

            # 3. Создание PUSH consumer'а с минимально необходимой конфигурацией
            consumer_config = ConsumerConfig(
                durable_name=durable_name,
                deliver_group=queue_group_name,
                ack_policy=AckPolicy.EXPLICIT,
                deliver_policy=DeliverPolicy.ALL,
                filter_subject=subscribe_subject
            )
            print(
                f"WORKER: Попытка ЯВНОГО СОЗДАНИЯ PUSH consumer'а: Stream='{stream_name}', Durable='{durable_name}', Config='{consumer_config.as_dict()}'")
            await js.add_consumer(stream=stream_name, config=consumer_config)
            print(f"WORKER: Consumer '{durable_name}' для очереди '{queue_group_name}' должен быть создан/обновлен.")

            # 4. Немедленная проверка конфигурации созданного консьюмера
            try:
                consumer_info = await js.consumer_info(stream=stream_name, consumer=durable_name)
                print(f"WORKER: ИНФО О СОЗДАННОМ КОНСЬЮМЕРЕ '{durable_name}':")
                print(f"WORKER:   Config: {consumer_info.config.as_dict()}")
                is_pull_mode = not consumer_info.config.deliver_group and not consumer_info.config.deliver_subject
                print(f"WORKER:   Определен как Pull Mode: {is_pull_mode}")
                if is_pull_mode:
                    print(
                        "WORKER: КРИТИЧЕСКАЯ ПРОБЛЕМА: Консьюмер создан как PULL MODE, хотя ожидался PUSH с deliver_group!")
                    raise Exception("Consumer created in Pull Mode unexpectedly")
            except Exception as e_info:
                print(f"WORKER: Ошибка при получении информации о консьюмере '{durable_name}': {e_info}")
                raise

            # 5. Подписка
            print(
                f"WORKER: Попытка подписки: Субъект='{subscribe_subject}', Durable='{durable_name}', Очередь='{queue_group_name}'")
            sub = await js.subscribe(
                subject=subscribe_subject,
                queue=queue_group_name,
                durable=durable_name,
                cb=message_handler,
                manual_ack=True
            )
            print("WORKER: Успешно подписан. Ожидаю сообщения...")

            while nc.is_connected and not stop_event.is_set():
                await asyncio.sleep(1)

            if stop_event.is_set(): break

        except nats.errors.NoServersError:
            print(f"WORKER: Ошибка NATS - нет серверов по {settings.NATS_URL}. Повторная попытка через 5 сек...")
        except nats.errors.TimeoutError:
            print(f"WORKER: Таймаут операции JetStream. Повторная попытка через 5 сек...")
        except Exception as e:
            print(f"WORKER: Ошибка в главном цикле run_worker: {type(e).__name__} - {e}")
            if hasattr(e, 'description'): print(f"WORKER: Описание NATS: {e.description}")
            print("WORKER: Повторная попытка подключения через 5 сек...")
        finally:
            if sub:
                try:
                    print("WORKER: Отписываюсь от NATS...")
                    await sub.unsubscribe()
                    print("WORKER: Успешно отписан.")
                except Exception as e_unsub:
                    print(f"WORKER: Ошибка при отписке: {e_unsub}")
                sub = None
            if nc:
                try:
                    print("WORKER: Закрываю соединение с NATS...")
                    await nc.close()
                    print("WORKER: Соединение NATS закрыто.")
                except Exception as e_close:
                    print(f"WORKER: Ошибка при закрытии соединения NATS: {e_close}")
                nc = None

        if not stop_event.is_set(): await asyncio.sleep(5)

    print("WORKER: Завершил работу.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    print("Запуск Alert Worker...")
    asyncio.run(run_worker())