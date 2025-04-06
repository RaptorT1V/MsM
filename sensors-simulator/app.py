import psycopg2
from time import sleep
import random
import threading


def connect_db():
    conn = psycopg2.connect(
        dbname="Ural_Steel",
        user="postgres",
        password="postgres",
        host="127.0.0.1",
        port="5432"
    )
    return conn


def generate_furnace_data(conn):
    cursor = conn.cursor()
    temperature = 100.0
    pressure = 2.0
    critical_temperature = 300.0
    critical_pressure = 10.0

    while True:
        temperature += random.uniform(4.0, 8.0)
        pressure += random.uniform(0.1, 0.5)

        cursor.execute("""
            INSERT INTO Furnace (temperature, pressure)
            VALUES (%s, %s);
        """, (temperature, pressure))

        conn.commit()
        sleep(0.9)
        if temperature >= critical_temperature:
            print(f"Температура в печке достигла критического значения: {temperature}\n Печка сгорела :( ! \n--|--\n")
            break

        if pressure >= critical_pressure:
            print(f"Давление в печке достигло критического значения: {pressure}\n Печка взорвалась :( Бабах! \n--|--\n")
            break


def generate_casting_machine_data(conn):
    cursor = conn.cursor()
    mold_temperature = 190.0
    casting_speed = 1.0
    critical_mold_temperature = 300.0
    critical_casting_speed = 9.0

    while True:
        mold_temperature += random.uniform(0.1, 1.0)
        casting_speed += random.uniform(0.1, 0.5)

        cursor.execute("""
            INSERT INTO CastingMachine (mold_temperature, casting_speed)
            VALUES (%s, %s);
        """, (mold_temperature, casting_speed))

        conn.commit()
        sleep(0.9)
        if mold_temperature >= critical_mold_temperature:
            print(f"Температура формы в машине литья достигла критического значения: {mold_temperature}\n Литейная машина прекратила свою работу! \n--|--\n")
            break

        if casting_speed >= critical_casting_speed:
            print(f"Скорость литья достигла критического значения: {casting_speed}\n Литейная машина остановила свою работу! \n--|--\n")
            break


def generate_rolling_mill_data(conn):
    cursor = conn.cursor()
    roller_speed = 1.0
    sheet_thickness = 0.5
    critical_roller_speed = 14.0
    critical_sheet_thickness = 6.0

    while True:
        roller_speed += random.uniform(0.1, 0.5)
        sheet_thickness += random.uniform(0.01, 0.1)

        cursor.execute("""
            INSERT INTO RollingMill (roller_speed, sheet_thickness)
            VALUES (%s, %s);
        """, (roller_speed, sheet_thickness))

        conn.commit()
        sleep(0.9)
        if roller_speed >= critical_roller_speed:
            print(f"Скорость роликов в прокатном стане достигла критического значения: {roller_speed}\n К сожалению, прокатному стану пришёл кабздец! \n--|--\n")
            break

        if sheet_thickness >= critical_sheet_thickness:
            print(f"Толщина листа в прокатном стане достигла критического значения: {sheet_thickness}\n Всё, кабзда прокатному стану! \n--|--\n")
            break


def generate_crane_data(conn):
    cursor = conn.cursor()
    load_weight = 900.0
    crane_speed = 1.0
    critical_load_weight = 2000.0
    critical_crane_speed = 9.0

    while True:
        load_weight += random.uniform(10.0, 50.0)
        crane_speed += random.uniform(0.1, 0.3)

        cursor.execute("""
            INSERT INTO Crane (load_weight, crane_speed)
            VALUES (%s, %s);
        """, (load_weight, crane_speed))

        conn.commit()
        sleep(0.9)
        if load_weight >= critical_load_weight:
            print(f"Вес груза в кране достиг критического значения: {load_weight}\n Кран перестал работать и больше не двигается! Докрутились, блин! \n--|--\n")
            break

        if crane_speed >= critical_crane_speed:
            print(f"Скорость крана достигла критического значения: {crane_speed}\n Кран перестал работать и больше не двигается! Докрутились, блин! \n--|--\n")
            break


def generate_cooling_system_data(conn):
    cursor = conn.cursor()
    coolant_temperature = 50.0
    coolant_flow_rate = 10.0
    critical_coolant_temperature = 100.0
    critical_coolant_flow_rate = 70.0

    while True:
        coolant_temperature += random.uniform(0.1, 1.0)
        coolant_flow_rate += random.uniform(0.5, 2.0)

        cursor.execute("""
            INSERT INTO CoolingSystem (coolant_temperature, coolant_flow_rate)
            VALUES (%s, %s);
        """, (coolant_temperature, coolant_flow_rate))

        conn.commit()
        sleep(0.9)
        if coolant_temperature >= critical_coolant_temperature:
            print(f"Температура охлаждающей жидкости достигла критического значения: {coolant_temperature}\n Система охлаждения прекратила свою работу! Доигрались! \n--|--\n")
            break

        if coolant_flow_rate >= critical_coolant_flow_rate:
            print(f"Скорость потока охлаждающей жидкости достигла критического значения: {coolant_flow_rate}\n Система охлаждения прекратила свою работу! Доигрались! \n--|--\n")
            break


def main():
    conn = connect_db()

    # Запуск всех функций параллельно
    threading.Thread(target=generate_furnace_data, args=(conn,)).start()
    threading.Thread(target=generate_casting_machine_data, args=(conn,)).start()
    threading.Thread(target=generate_rolling_mill_data, args=(conn,)).start()
    threading.Thread(target=generate_crane_data, args=(conn,)).start()
    threading.Thread(target=generate_cooling_system_data, args=(conn,)).start()


if __name__ == "__main__":
    main()