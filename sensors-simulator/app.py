import psycopg2
import threading
import random
import time
from datetime import datetime, timezone
import signal
import sys

# --- Параметры подключения к БД ---
DB_NAME = "Ural_Steel"
DB_USER = "admin"
DB_PASSWORD = "admin"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"

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


def signal_handler(signum, frame):
    """Обработчик Ctrl+C."""
    print("\nCtrl+C! Завершаю потоки...")
    stop_event.set()


# --- Функции ---
def connect_db():
    """Устанавливает НОВОЕ соединение с БД."""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"ОШИБКА: Не удалось подключиться к БД: {e}")
        return None


def get_parameters(conn):
    """Получает ID и типы параметров из БД."""
    parameters = []
    if not conn: return parameters
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.parameter_id, pt.parameter_type_name
            FROM parameters p
            JOIN parameter_types pt ON p.parameter_type_id = pt.parameter_type_id
        """)
        parameters = cursor.fetchall()
        cursor.close()
    except (Exception, psycopg2.Error) as error:
        print(f"Ошибка при получении параметров: {error}")
    return parameters


def generate_initial_value(param_type):
    """Генерирует начальное значение на основе типа параметра."""
    param_type = param_type.lower()
    if 'температура' in param_type:
        return random.uniform(20, 100)
    elif 'ток' in param_type:
        return random.uniform(10, 50)
    elif 'мощность' in param_type:
        return random.uniform(1000, 5000)
    elif 'скорость' in param_type:
        return random.uniform(1, 10)
    elif 'вибрация' in param_type:
        return random.uniform(0, 3)
    elif 'давление' in param_type:
        return random.uniform(1, 5)
    elif 'разрежение' in param_type:
        return random.uniform(50, 200)
    elif 'уровень' in param_type or 'высота' in param_type:
        return random.uniform(10, 100)
    else:
        return random.uniform(0, 50)


def generate_data_for_parameter(parameter_id, param_type):
    """Задача потока: генерирует и вставляет данные для ОДНОГО параметра."""
    print(f"[Поток {parameter_id} ({param_type})]: Запущен.")
    value = generate_initial_value(param_type)
    conn = None

    while not stop_event.is_set():
        try:
            conn = connect_db()
            if not conn:
                print(f"[Поток {parameter_id}]: Ошибка подключения, пауза...")
                time.sleep(5)
                continue

            cursor = conn.cursor()

            # Генерирует новое значение
            delta = random.uniform(STEP_MIN, STEP_MAX)
            value += delta
            value = max(MIN_VALUE_CLAMP, min(MAX_VALUE_CLAMP, value))

            timestamp = datetime.now(timezone.utc)

            # Вставляет данные
            cursor.execute(
                """
                INSERT INTO parameter_data (parameter_id, parameter_value, data_timestamp)
                VALUES (%s, %s, %s);
                """,
                (parameter_id, value, timestamp)
            )
            conn.commit()
            cursor.close()

        except KeyboardInterrupt:
            break
        except (Exception, psycopg2.Error) as error:
            print(f"[Поток {parameter_id}]: Ошибка БД - {error}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
        finally:
            if conn:
                conn.close()

        # Пауза перед следующей итерацией (с проверкой stop_event)
        sleep_duration = random.uniform(DEFAULT_SLEEP_MIN, DEFAULT_SLEEP_MAX)
        if stop_event.wait(timeout=sleep_duration):
            break

    print(f"[Поток {parameter_id}]: Завершен.")


# --- Основная функция ---
def main():
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    initial_conn = connect_db()
    if not initial_conn:
        sys.exit("Выход: Не удалось установить начальное соединение с БД.")

    parameters_to_simulate = get_parameters(initial_conn)
    initial_conn.close()  # Закрываем соединение после получения списка

    if not parameters_to_simulate:
        print("В базе данных не найдено параметров для симуляции. Выход.")
        sys.exit()

    print(f"Найдено {len(parameters_to_simulate)} параметров. Запускаю потоки симуляции...")
    print("Нажмите Ctrl+C для остановки.")

    threads = []
    for p_id, p_type in parameters_to_simulate:
        thread = threading.Thread(
            target=generate_data_for_parameter,
            args=(p_id, p_type),
            daemon=True  # Потоки завершатся, если основной поток завершится
        )
        threads.append(thread)
        thread.start()
        time.sleep(0.01) # Небольшая задержка старта

    # Главный поток просто ждет сигнала остановки
    while not stop_event.is_set():
        try:
            time.sleep(1)  # Можно проверять состояние потоков, если нужно
        except KeyboardInterrupt:
            signal_handler(None, None)  # Обрабатываем Ctrl+C и в главном цикле

    print("Основной поток: получен сигнал остановки.")
    print("Симуляция завершена.")


if __name__ == "__main__":
    main()
