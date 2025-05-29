import asyncio, psycopg2, random, signal, threading
from datetime import datetime, timezone
from typing import List, Tuple
from faststream.rabbit import RabbitBroker
from backend.app.core.config import settings


# --- Параметры симуляции ---
INITIAL_VALUE_MIN = 10.0
INITIAL_VALUE_MAX = 100.0
STEP_MIN = -1.0
STEP_MAX = 1.0
MIN_VALUE_CLAMP = 0.0
MAX_VALUE_CLAMP = 10000.0
DEFAULT_SLEEP_MIN = 1.0
DEFAULT_SLEEP_MAX = 2.0

# --- Управление потоками ---
stop_event = threading.Event()

# --- FastStream RabbitMQ SETUP ---
broker = RabbitBroker(settings.RABBITMQ_URL)


'''
===============
    Функции     
===============
'''


def signal_handler(signum, frame):  # noqa
    """ Обрабатывает Ctrl+C """
    print("\nУвидел 'Ctrl+C'! Завершаю потоки...")
    stop_event.set()


def connect_db():
    """ Устанавливает новое соединение с БД (только для чтения ID) """
    try:
        conn = psycopg2.connect(
            dbname=settings.DB_NAME, user=settings.DB_USER, password=settings.DB_PASSWORD,
            host=settings.DB_HOST, port=settings.DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"ОШИБКА!!! Не удалось подключиться к БД для чтения параметров: {e}")
        return None


def get_parameters_from_db() -> List[Tuple[int, str]]:
    """ Получает ID и типы параметров из БД """
    parameters = []
    conn = connect_db()
    if not conn:
        return parameters
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.parameter_id, pt.parameter_type_name
            FROM parameters p
            JOIN parameter_types pt ON p.parameter_type_id = pt.parameter_type_id;
        """)
        parameters = cursor.fetchall()
        cursor.close()
    except (Exception, psycopg2.Error) as error:
        print(f"ОШИБКА!!! Не удалось получить параметры из БД: {error}")
    finally:
        if conn:
            conn.close()
    return parameters


def generate_initial_value(param_type):
    """ Генерирует начальное значение на основе типа параметра """
    param_type = param_type.lower()
    if 'температура' in param_type: return random.uniform(80, 82)
    elif 'ток' in param_type: return random.uniform(150, 152)
    elif 'мощность' in param_type: return random.uniform(1000, 1002)
    elif 'скорость' in param_type: return random.uniform(30, 32)
    elif 'вибрация' in param_type: return random.uniform(20, 22)
    elif 'давление' in param_type: return random.uniform(100, 102)
    elif 'разрежение' in param_type: return random.uniform(200, 202)
    elif 'уровень' in param_type or 'высота' in param_type: return random.uniform(10, 12)
    else: return random.uniform(0, 50)


async def generate_data_for_parameter(parameter_id: int, param_type: str):
    """ Асинхронная задача: генерирует данные и публикует их в RabbitMQ через FastStream """
    print(f"SIMULATOR  [Поток {parameter_id} ({param_type})] Запущен.")
    value = generate_initial_value(param_type)

    while not stop_event.is_set():
        try:
            # Генерирует новое значение
            delta = random.uniform(STEP_MIN, STEP_MAX)
            value += delta
            value = max(MIN_VALUE_CLAMP, min(MAX_VALUE_CLAMP, value))
            timestamp = datetime.now(timezone.utc)

            # Формирует сообщение JSON
            payload_dict = {
                "parameter_id": parameter_id,
                "parameter_value": round(value, 2),
                "data_timestamp": timestamp.isoformat()
            }

            # Публикует в именованную очередь
            await broker.publish(
                payload_dict,
                queue=settings.RABBITMQ_QUEUE_NAME,
            )
            print(f"SIMULATOR: Опубликовано в очередь RabbitMQ '{settings.RABBITMQ_QUEUE_NAME}': {payload_dict}")

            # Асинхронная пауза
            sleep_duration = random.uniform(DEFAULT_SLEEP_MIN, DEFAULT_SLEEP_MAX)
            await asyncio.sleep(sleep_duration)
        except KeyboardInterrupt:
            break
        except Exception as error:
            print(f"SIMULATOR !!! ОШИБКА в потоке {parameter_id}: {type(error).__name__} - {error}")
            if stop_event.is_set():
                 break
            print(f"SIMULATOR  [Поток {parameter_id}]: Пауза 5 сек после ошибки.")
            await asyncio.sleep(5)

    print(f"[SIMULATOR  Поток {parameter_id}] Завершён.")


async def main_async():
    """ Главная асинхронная функция симулятора """
    try:
        # 1. Получает список параметров из БД
        print("SIMULATOR  Получение списка параметров из PostgreSQL...")
        parameters_to_simulate = get_parameters_from_db()
        if not parameters_to_simulate:
            print("SIMULATOR  В базе данных не найдено параметров для симуляции. Выход.")
            return
        print(f"SIMULATOR  Найдено {len(parameters_to_simulate)} параметров.")

        # 2. Подключается к RabbitMQ
        print(f"SIMULATOR: Подключаюсь к RabbitMQ: {settings.RABBITMQ_URL}...")
        await broker.start()
        print("SIMULATOR: Успешно подключено к RabbitMQ через FastStream.")

        # 3. Запускает задачи генерации
        print(f"SIMULATOR  Запускаю {len(parameters_to_simulate)} потоков генерации данных...")
        print("SIMULATOR  Нажмите Ctrl+C для остановки.")
        tasks = []
        for p_id, p_type in parameters_to_simulate:
            task = asyncio.create_task(generate_data_for_parameter(p_id, p_type))
            tasks.append(task)
            await asyncio.sleep(0.01)

        # 4. Ожидает сигнала остановки
        while not stop_event.is_set():
            await asyncio.sleep(1)

        # Если остановка произошла (Ctrl+C), отменяет задачи
        print("SIMULATOR  Отменяю задачи генерации...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
        print(f"SIMULATOR  !!! Критическая ОШИБКА в main_async: {type(e).__name__} - {e}")
    finally:
        print("SIMULATOR  Основная задача: завершение.")
        if broker:
            print("SIMULATOR  Закрываю соединение с RabbitMQ...")
            try:
                await broker.close()
            except Exception as e_close:
                print(f"SIMULATOR  !!! ОШИБКА при закрытии соединения RabbitMQ: {e_close}")
        print("SIMULATOR  Симуляция завершена.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    asyncio.run(main_async())