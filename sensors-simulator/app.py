import psycopg2
from time import sleep, time
import random
import threading


# Подсоединение к базе данных
def connect_db():
    conn = psycopg2.connect(
        dbname="Ural_Steel",
        user="admin",
        password="admin",
        host="127.0.0.1",
        port="5432"
    )
    return conn


# Агломерационные машины
def generate_first_sint_machine_data(conn):
    cursor = conn.cursor()

    layer_length = 400  # длина слоя постоянна?
    charge_temperature = 40
    speed = 4.6
    rarefaction = 200

    critical_charge_temperature = 200
    critical_speed = 0
    critical_rarefaction = 3000

    while True:
        charge_temperature += random.uniform(1.0, 10.0)
        speed -= random.uniform(0.05, 0.15)
        rarefaction += random.uniform(10, 150)

        cursor.execute("""
            INSERT INTO SinteringMachine_1 (layer_length, charge_temperature, speed, rarefaction)
            VALUES (%s, %s, %s, %s);
        """, (layer_length, charge_temperature, speed, rarefaction))

        conn.commit()
        sleep(1.5)

        if charge_temperature >= critical_charge_temperature:
            print(f"Температура в агломерационной машине №1 достигла критического значения: {charge_temperature}\n")
            break

        if speed <= critical_speed:
            print(f"Скорость агломерационной машины №1 достигла критического значения: {speed}\n")
            break

        if rarefaction >= critical_rarefaction:
            print(f"Разрежение в агломерационной машине №1 достигло критического значения: {rarefaction}\n")
            break


def generate_second_sint_machine_data(conn):
    cursor = conn.cursor()

    layer_length = 400  # длина слоя постоянна?
    charge_temperature = 20
    speed = 5
    rarefaction = 100

    critical_charge_temperature = 200
    critical_speed = 0
    critical_rarefaction = 3000

    while True:
        charge_temperature += random.uniform(1.0, 10.0)
        speed -= random.uniform(0.05, 0.15)
        rarefaction += random.uniform(10, 150)

        cursor.execute("""
            INSERT INTO SinteringMachine_2 (layer_length, charge_temperature, speed, rarefaction)
            VALUES (%s, %s, %s, %s);
        """, (layer_length, charge_temperature, speed, rarefaction))

        conn.commit()
        sleep(1.5)

        if charge_temperature >= critical_charge_temperature:
            print(f"Температура в агломерационной машине №2 достигла критического значения: {charge_temperature}\n")
            break

        if speed <= critical_speed:
            print(f"Скорость агломерационной машины №2 достигла критического значения: {speed}\n")
            break

        if rarefaction >= critical_rarefaction:
            print(f"Разрежение в агломерационной машине №2 достигло критического значения: {rarefaction}\n")
            break


# Доменные печи
def generate_first_blast_furnace_data(conn):
    cursor = conn.cursor()

    blast_flow_rate = 1000
    blast_pressure = 1
    natural_gas_flow_rate = 7000

    critical_blast_flow_rate = 10000
    critical_blast_pressure = 10
    critical_natural_gas_flow_rate = 35000

    while True:
        blast_flow_rate += random.uniform(100, 500)
        blast_pressure += random.uniform(0.1, 0.5)
        natural_gas_flow_rate += random.uniform(300, 1200)

        cursor.execute("""
            INSERT INTO blastfurnace_1 (blast_flow_rate, blast_pressure, natural_gas_flow_rate)
            VALUES (%s, %s, %s);
        """, (blast_flow_rate, blast_pressure, natural_gas_flow_rate))

        conn.commit()
        sleep(1.5)

        if blast_flow_rate >= critical_blast_flow_rate:
            print(f"Объёмный расход дутья в доменной печи №1 достиг критического значения: {blast_flow_rate}\n")
            break

        if blast_pressure >= critical_blast_pressure:
            print(f"Давление дутья в доменной печи №1 достигло критического значения: {blast_pressure}\n")
            break

        if natural_gas_flow_rate >= critical_natural_gas_flow_rate:
            print(f"Объёмный расход природного газа в доменной печи №1 достиг критического значения: {natural_gas_flow_rate}\n")
            break


def generate_second_blast_furnace_data(conn):
    cursor = conn.cursor()

    blast_flow_rate = 1500
    blast_pressure = 1.5
    natural_gas_flow_rate = 6000

    critical_blast_flow_rate = 10000
    critical_blast_pressure = 10
    critical_natural_gas_flow_rate = 35000

    while True:
        blast_flow_rate += random.uniform(100, 500)
        blast_pressure += random.uniform(0.1, 0.5)
        natural_gas_flow_rate += random.uniform(300, 1200)

        cursor.execute("""
            INSERT INTO BlastFurnace_2 (blast_flow_rate, blast_pressure, natural_gas_flow_rate)
            VALUES (%s, %s, %s);
        """, (blast_flow_rate, blast_pressure, natural_gas_flow_rate))

        conn.commit()
        sleep(1.5)

        if blast_flow_rate >= critical_blast_flow_rate:
            print(f"Объёмный расход дутья в доменной печи №2 достиг критического значения: {blast_flow_rate}\n")
            break

        if blast_pressure >= critical_blast_pressure:
            print(f"Давление дутья в доменной печи №2 достигло критического значения: {blast_pressure}\n")
            break

        if natural_gas_flow_rate >= critical_natural_gas_flow_rate:
            print(f"Объёмный расход природного газа в доменной печи №2 достиг критического значения: {natural_gas_flow_rate}\n")
            break


# Гибкие модульные печи
def generate_first_flexible_modular_furnace_data(conn):
    cursor = conn.cursor()

    argon_flow_rate = 500
    oxygen_flow_rate = 1000
    power = 20000

    critical_argon_flow_rate = 5000
    critical_oxygen_flow_rate = 25000
    critical_power = 110500

    while True:
        argon_flow_rate += random.uniform(50, 250)
        oxygen_flow_rate += random.uniform(200, 1100)
        power += random.uniform(1000, 5000)

        cursor.execute("""
            INSERT INTO FlexibleModularFurnace_1 (argon_flow_rate, oxygen_flow_rate, power)
            VALUES (%s, %s, %s);
        """, (argon_flow_rate, oxygen_flow_rate, power))

        conn.commit()
        sleep(1.5)

        if argon_flow_rate >= critical_argon_flow_rate:
            print(f"Объёмный расход аргона в гибкой модульной печи №1 достиг критического значения: {argon_flow_rate}\n")
            break

        if oxygen_flow_rate >= critical_oxygen_flow_rate:
            print(f"Объёмный расход кислорода в гибкой модульной печи №1 достиг критического значения: {oxygen_flow_rate}\n")
            break

        if power >= critical_power:
            print(f"Мощность гибкой модульной печи №1 достигла критического значения: {power}\n")
            break


def generate_second_flexible_modular_furnace_data(conn):
    cursor = conn.cursor()

    argon_flow_rate = 350
    oxygen_flow_rate = 850
    power = 18000

    critical_argon_flow_rate = 5000
    critical_oxygen_flow_rate = 25000
    critical_power = 110500

    while True:
        argon_flow_rate += random.uniform(50, 250)
        oxygen_flow_rate += random.uniform(200, 1100)
        power += random.uniform(1000, 5000)

        cursor.execute("""
            INSERT INTO FlexibleModularFurnace_2 (argon_flow_rate, oxygen_flow_rate, power)
            VALUES (%s, %s, %s);
        """, (argon_flow_rate, oxygen_flow_rate, power))

        conn.commit()
        sleep(1.5)

        if argon_flow_rate >= critical_argon_flow_rate:
            print(f"Объёмный расход аргона в гибкой модульной печи №2 достиг критического значения: {argon_flow_rate}\n")
            break

        if oxygen_flow_rate >= critical_oxygen_flow_rate:
            print(f"Объёмный расход кислорода в гибкой модульной печи №2 достиг критического значения: {oxygen_flow_rate}\n")
            break

        if power >= critical_power:
            print(f"Мощность гибкой модульной печи №2 достигла критического значения: {power}\n")
            break


# Паровые котлы среднего давления
def generate_first_medium_pressure_boiler_data(conn):
    cursor = conn.cursor()

    temperature = 100
    pressure = 1.0
    steam_output = 50

    critical_temperature = 2000
    critical_pressure = 20
    critical_steam_output = 1000

    while True:
        temperature += random.uniform(20, 100)
        pressure += random.uniform(0.1, 1)
        steam_output += random.uniform(10, 50)

        cursor.execute("""
            INSERT INTO MediumPressureBoiler_1 (temperature, pressure, steam_output)
            VALUES (%s, %s, %s);
        """, (temperature, pressure, steam_output))

        conn.commit()
        sleep(1.5)

        if temperature >= critical_temperature:
            print(f"Температура в паровом котле среднего давления №1 достигла критического значения: {temperature}\n")
            break

        if pressure >= critical_pressure:
            print(f"Давление в паровом котле среднего давления №1 достигло критического значения: {pressure}\n")
            break

        if steam_output >= critical_steam_output:
            print(f"Выработка пара в паровом котле среднего давления №1 достигла критического значения: {steam_output}\n")
            break


def generate_second_medium_pressure_boiler_data(conn):
    cursor = conn.cursor()

    temperature = 150
    pressure = 1.5
    steam_output = 80

    critical_temperature = 2000
    critical_pressure = 20
    critical_steam_output = 1000

    while True:
        temperature += random.uniform(10, 100)
        pressure += random.uniform(0.1, 1)
        steam_output += random.uniform(10, 50)

        cursor.execute("""
            INSERT INTO MediumPressureBoiler_2 (temperature, pressure, steam_output)
            VALUES (%s, %s, %s);
        """, (temperature, pressure, steam_output))

        conn.commit()
        sleep(1.5)

        if temperature >= critical_temperature:
            print(f"Температура в паровом котле среднего давления №2 достигла критического значения: {temperature}\n")
            break

        if pressure >= critical_pressure:
            print(f"Давление в паровом котле среднего давления №2 достигло критического значения: {pressure}\n")
            break

        if steam_output >= critical_steam_output:
            print(f"Выработка пара в паровом котле среднего давления №2 достигла критического значения: {steam_output}\n")
            break


def main():
    conn = connect_db()

    threads = [
        threading.Thread(target=generate_first_sint_machine_data, args=(conn,)),  # --
        threading.Thread(target=generate_second_sint_machine_data, args=(conn,)),
        threading.Thread(target=generate_first_blast_furnace_data, args=(conn,)),  # --
        threading.Thread(target=generate_second_blast_furnace_data, args=(conn,)),
        threading.Thread(target=generate_first_flexible_modular_furnace_data, args=(conn,)),  # --
        threading.Thread(target=generate_second_flexible_modular_furnace_data, args=(conn,)),
        threading.Thread(target=generate_first_medium_pressure_boiler_data, args=(conn,)),  # --
        threading.Thread(target=generate_second_medium_pressure_boiler_data, args=(conn,))
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    start_time = time()  # время начала выполнения программы
    main()
    end_time = time()  # время конца выполнения программы
    print("Время выполнения программы: ", end_time - start_time, "\n Получилось в результате вычитания ", end_time,
          " -", start_time)
