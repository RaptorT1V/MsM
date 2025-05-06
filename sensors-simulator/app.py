import asyncio, json, nats, psycopg2, random, signal, sys, threading
from nats.errors import ConnectionClosedError, NoServersError, TimeoutError
from backend.app.core.config import settings
from datetime import datetime, timezone
from typing import List, Tuple


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


'''
===============
    Функции     
===============
'''


def signal_handler(signum, frame):
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
        print(f"ОШИБКА: Не удалось подключиться к БД для чтения параметров: {e}")
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
        print(f"Ошибка при получении параметров из БД: {error}")
    finally:
        if conn:
            conn.close()
    return parameters


def generate_initial_value(param_type):
    """ Генерирует начальное значение на основе типа параметра """
    param_type = param_type.lower()
    if 'температура' in param_type: return random.uniform(20, 100)
    elif 'ток' in param_type: return random.uniform(10, 50)
    elif 'мощность' in param_type: return random.uniform(1000, 5000)
    elif 'скорость' in param_type: return random.uniform(1, 10)
    elif 'вибрация' in param_type: return random.uniform(0, 3)
    elif 'давление' in param_type: return random.uniform(1, 5)
    elif 'разрежение' in param_type: return random.uniform(50, 200)
    elif 'уровень' in param_type or 'высота' in param_type: return random.uniform(10, 100)
    else: return random.uniform(0, 50)


async def generate_data_for_parameter(nats_client, parameter_id, param_type):
    """ Асинхронная задача: генерирует данные и публикует их в NATS """
    print(f"[Поток {parameter_id} ({param_type})]: Запущен.")
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
            payload_json = json.dumps(payload_dict)

            # Публикует сообщение в NATS
            await nats_client.publish(settings.NATS_SUBJECT, payload_json.encode())
            print(f"Published: {payload_json}")

            # Асинхронная пауза
            sleep_duration = random.uniform(DEFAULT_SLEEP_MIN, DEFAULT_SLEEP_MAX)
            await asyncio.sleep(sleep_duration)

        # Обработка ошибок NATS и KeyboardInterrupt
        except KeyboardInterrupt: break
        except ConnectionClosedError:
            print(f"ОШИБКА NATS [Поток {parameter_id}]: Соединение закрыто...")
            await asyncio.sleep(5)
        except TimeoutError:
            print(f"ОШИБКА NATS [Поток {parameter_id}]: Таймаут.")
            await asyncio.sleep(1)
        except NoServersError as e:
            print(f"ОШИБКА NATS [Поток {parameter_id}]: Нет серверов - {e}")
            await asyncio.sleep(5)
        except Exception as error:
            print(f"ОШИБКА в потоке {parameter_id}: {error}")
            await asyncio.sleep(5)

    print(f"[Поток {parameter_id}]: Завершен.")


async def main_async():
    """ Главная асинхронная функция симулятора """
    nats_client = None
    try:
        # 1. Получает список параметров из БД
        print("Получение списка параметров из PostgreSQL...")
        parameters_to_simulate = get_parameters_from_db()
        if not parameters_to_simulate:
            print("В базе данных не найдено параметров для симуляции. Выход.")
            sys.exit(1)
        print(f"Найдено {len(parameters_to_simulate)} параметров.")

        # 2. Подключается к NATS
        print(f"Подключаюсь к NATS: {settings.NATS_URL}...")
        nats_client = await nats.connect(settings.NATS_URL, name="Parameter Simulator")
        print("Успешно подключено к NATS.")

        # 3. Запускает задачи генерации
        print(f"Запускаю {len(parameters_to_simulate)} потоков генерации данных...")
        print("Нажмите Ctrl+C для остановки.")
        tasks = []
        for p_id, p_type in parameters_to_simulate:
            task = asyncio.create_task(generate_data_for_parameter(nats_client, p_id, p_type))
            tasks.append(task)
            await asyncio.sleep(0.01)

        # 4. Ожидает сигнала остановки
        while not stop_event.is_set():
            await asyncio.sleep(1)

        # Если остановка произошла (Ctrl+C), отменяет задачи
        print("Отменяю задачи генерации...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    except NoServersError as e:
         print(f"Критическая ошибка: Не удалось подключиться к NATS - {e}")
    except Exception as e:
         print(f"Критическая ошибка в main_async: {e}")
    finally:
        print("Основная задача: завершение.")
        if nats_client and nats_client.is_connected:
            print("Закрываю соединение с NATS...")
            await nats_client.close()
        print("Симуляция завершена.")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    asyncio.run(main_async())