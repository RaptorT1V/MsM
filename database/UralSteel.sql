	-- - ! - - - - - - | Блок DROP'ов | - - - - - - ! - --
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Titles CASCADE;
DROP TABLE IF EXISTS Furnace CASCADE;
DROP TABLE IF EXISTS CastingMachine CASCADE;
DROP TABLE IF EXISTS RollingMill CASCADE;
DROP TABLE IF EXISTS Crane CASCADE;
DROP TABLE IF EXISTS CoolingSystem CASCADE;
DROP TABLE IF EXISTS Alerts CASCADE;
-- -- -- -- -- -- -- -- -- -- -- -- --
DROP TYPE IF EXISTS Equipment_type_enum CASCADE;
-- -- -- -- -- -- -- -- -- -- -- -- --
/*
	DROP INDEX IF EXISTS;
*/
-- -- -- -- -- -- -- -- -- -- -- -- --
DROP FUNCTION IF EXISTS Get_alert_details() CASCADE;
DROP FUNCTION IF EXISTS Get_alert_details_to_json() CASCADE;
--
DROP FUNCTION IF EXISTS Hash_password() CASCADE;
DROP FUNCTION IF EXISTS Add_plus_to_phone() CASCADE;
--
DROP FUNCTION IF EXISTS Check_furnace_alert() CASCADE;
DROP FUNCTION IF EXISTS Check_casting_machine_alert() CASCADE;
DROP FUNCTION IF EXISTS Check_rolling_mill_alert() CASCADE;
DROP FUNCTION IF EXISTS Check_crane_alert() CASCADE;
DROP FUNCTION IF EXISTS Check_cooling_system_alert() CASCADE;
-- -- -- -- -- -- -- -- -- -- -- -- --
DROP TRIGGER IF EXISTS Hash_password_trigger ON Users;     
DROP TRIGGER IF EXISTS Add_plus_to_phone_trigger ON Users;
--
DROP TRIGGER IF EXISTS Furnace_alert_trigger ON Furnace;
DROP TRIGGER IF EXISTS CastingMachine_alert_trigger ON CastingMachine;
DROP TRIGGER IF EXISTS RollingMill_alert_trigger ON RollingMill;
DROP TRIGGER IF EXISTS Crane_alert_trigger ON Crane;
DROP TRIGGER IF EXISTS CoolingSystem_alert_trigger ON CoolingSystem;
-- -- -- -- -- -- -- -- -- -- -- -- --
DROP EXTENSION IF EXISTS pgcrypto;

	-- - - - - - - - - | Подключение расширений | - - - - - - - - --
CREATE EXTENSION IF NOT EXISTS pgcrypto;
	
	-- - - - - - - - - | Создание перечислений | - - - - - - - - --
CREATE TYPE Equipment_type_enum AS ENUM ('Furnace', 'CastingMachine', 'RollingMill', 'Crane', 'CoolingSystem'); -- для т. Alerts
	
	-- - ! - - - - - - | Создание таблиц (+ Primary Key) | - - - - - - ! - --
CREATE TABLE Users (
    user_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	title_id int,
    first_name varchar(50) NOT NULL,
    last_name varchar(50) NOT NULL,
    middle_name varchar(50),
    user_password varchar(255) NOT NULL,
    e_mail varchar(60),
    phone_number char(12),
	registered_user timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE Titles (
	title_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	title_name text
);
--
CREATE TABLE Furnace (
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    temperature float8 NOT NULL,
    pressure float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE CastingMachine (
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mold_temperature float8 NOT NULL,
    casting_speed float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE RollingMill (
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    roller_speed float8 NOT NULL,
    sheet_thickness float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE Crane (
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    load_weight float8 NOT NULL,
    crane_speed float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE CoolingSystem (
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    coolant_temperature float8 NOT NULL,
    coolant_flow_rate float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE Alerts (
    alert_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    equipment_type Equipment_type_enum,
    alert_message text,
    registered_alert timestamp DEFAULT CURRENT_TIMESTAMP
);

	-- - ! - - - - - - | Создание ограничений: Foreign Key, Check | - - - - - - ! - --
ALTER TABLE Users ADD CONSTRAINT FK_Users_Titles FOREIGN KEY (title_id) REFERENCES Titles (title_id);
-- -- -- -- -- -- -- -- -- -- -- -- --
ALTER TABLE Users
ADD CONSTRAINT Unique_email_and_phone_constraint -- Пара значений (e-mail, phone_number) должна быть уникальна относительно других строк
UNIQUE (e_mail, phone_number); -- Если не нравится идея, можно удалить это ограничение и поставить UNIQUE и на e-mail, и phone_number
--
ALTER TABLE Users
ADD CONSTRAINT Check_email_mask -- Проверка маски e-mail и запрещённых символов
CHECK (e_mail ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$');
--
ALTER TABLE Users
ADD CONSTRAINT Check_password_english_chars -- Проверка: пароль может быть только на английском
CHECK (user_password ~ '^[a-zA-Z0-9!$^&()-_+=,.{}]+$');
--- ---

	-- - ! - - - - - - | Создание функций и хранимых процедур | - - - - - - ! - --
-- - Хранимая процедура / Функция, которая будет принимать тип оборудования и его ID, а затем возвращать соответствующие данные из нужной таблицы.
CREATE OR REPLACE FUNCTION Get_alert_details(
    equipment_type Equipment_type_enum, 
    start_date timestamp, 
    end_date timestamp
) 
RETURNS TABLE (
    value_id int,
    parameter1 float8,
    parameter2 float8,
    registered_value timestamp
) AS $$
BEGIN
    IF equipment_type = 'Furnace' THEN
        RETURN QUERY EXECUTE '
            SELECT value_id, 
                   temperature AS parameter1, 
                   pressure AS parameter2, 
                   registered_value
            FROM Furnace
            WHERE registered_value BETWEEN $1 AND $2'
            USING start_date, end_date;
    ELSIF equipment_type = 'CastingMachine' THEN
        RETURN QUERY EXECUTE '
            SELECT value_id, 
                   mold_temperature AS parameter1, 
                   casting_speed AS parameter2, 
                   registered_value
            FROM CastingMachine
            WHERE registered_value BETWEEN $1 AND $2'
            USING start_date, end_date;
    ELSIF equipment_type = 'RollingMill' THEN
        RETURN QUERY EXECUTE '
            SELECT value_id, 
                   roller_speed AS parameter1, 
                   sheet_thickness AS parameter2, 
                   registered_value
            FROM RollingMill
            WHERE registered_value BETWEEN $1 AND $2'
            USING start_date, end_date;
    ELSIF equipment_type = 'Crane' THEN
        RETURN QUERY EXECUTE '
            SELECT value_id, 
                   load_weight AS parameter1, 
                   crane_speed AS parameter2, 
                   registered_value
            FROM Crane
            WHERE registered_value BETWEEN $1 AND $2'
            USING start_date, end_date;
    ELSIF equipment_type = 'CoolingSystem' THEN
        RETURN QUERY EXECUTE '
            SELECT value_id, 
                   coolant_temperature AS parameter1, 
                   coolant_flow_rate AS parameter2, 
                   registered_value
            FROM CoolingSystem
            WHERE registered_value BETWEEN $1 AND $2'
            USING start_date, end_date;
    ELSE
        RAISE EXCEPTION 'Unknown equipment type: %', equipment_type;
    END IF;
END;
$$ LANGUAGE plpgsql;
--- ---
CREATE OR REPLACE FUNCTION Get_alert_details_to_json(
    equipment_type Equipment_type_enum, 
    start_date timestamp, 
    end_date timestamp
) 
RETURNS jsonb AS $$
DECLARE
    query text;
    result jsonb;
BEGIN
    IF equipment_type = 'Furnace' THEN
        query := 'SELECT jsonb_agg(jsonb_build_object(
                    ''value_id'', value_id, 
                    ''temperature'', temperature, 
                    ''pressure'', pressure, 
                    ''registered_value'', registered_value
                  )) 
                  FROM Furnace
                  WHERE registered_value BETWEEN $1 AND $2';
    ELSIF equipment_type = 'CastingMachine' THEN
        query := 'SELECT jsonb_agg(jsonb_build_object(
                    ''value_id'', value_id, 
                    ''mold_temperature'', mold_temperature, 
                    ''casting_speed'', casting_speed, 
                    ''registered_value'', registered_value
                  )) 
                  FROM CastingMachine
                  WHERE registered_value BETWEEN $1 AND $2';
    ELSIF equipment_type = 'RollingMill' THEN
        query := 'SELECT jsonb_agg(jsonb_build_object(
                    ''value_id'', value_id, 
                    ''roller_speed'', roller_speed, 
                    ''sheet_thickness'', sheet_thickness, 
                    ''registered_value'', registered_value
                  )) 
                  FROM RollingMill
                  WHERE registered_value BETWEEN $1 AND $2';
    ELSIF equipment_type = 'Crane' THEN
        query := 'SELECT jsonb_agg(jsonb_build_object(
                    ''value_id'', value_id, 
                    ''load_weight'', load_weight, 
                    ''crane_speed'', crane_speed, 
                    ''registered_value'', registered_value
                  )) 
                  FROM Crane
                  WHERE registered_value BETWEEN $1 AND $2';
    ELSIF equipment_type = 'CoolingSystem' THEN
        query := 'SELECT jsonb_agg(jsonb_build_object(
                    ''value_id'', value_id, 
                    ''coolant_temperature'', coolant_temperature, 
                    ''coolant_flow_rate'', coolant_flow_rate, 
                    ''registered_value'', registered_value
                  )) 
                  FROM CoolingSystem
                  WHERE registered_value BETWEEN $1 AND $2';
    ELSE
        RAISE EXCEPTION 'Unknown equipment type: %', equipment_type;
    END IF;

    EXECUTE query INTO result USING start_date, end_date;
    RETURN result;
END;
$$ LANGUAGE plpgsql;
--- ---

	-- - ! - - - - - - | Создание триггеров | - - - - - - ! - --
--- - Триггер для хэширования новых паролей 
CREATE OR REPLACE FUNCTION Hash_password() RETURNS TRIGGER AS $$
BEGIN
  NEW.user_password := crypt(NEW.user_password, gen_salt('bf'));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--
CREATE OR REPLACE TRIGGER Hash_password_trigger
BEFORE INSERT ON Users
FOR EACH ROW
EXECUTE FUNCTION Hash_password();
--- - Триггер для помещения знака "+" перед номером телефона 
CREATE OR REPLACE FUNCTION Add_plus_to_phone()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.phone_number IS NOT NULL AND LEFT(NEW.phone_number, 1) != '+' THEN
    NEW.phone_number = '+' || NEW.phone_number;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--
CREATE OR REPLACE TRIGGER Add_plus_to_phone_trigger 
BEFORE INSERT ON Users
FOR EACH ROW
EXECUTE FUNCTION Add_plus_to_phone();
-- -- -- -- -- -- -- -- -- -- -- -- --
--- - Триггер для автоматического создания записи в т. Alerts при достижения критического значения в печке
CREATE OR REPLACE FUNCTION Check_furnace_alert() RETURNS TRIGGER AS $$
DECLARE
    critical_temperature float8 := 300.0;
    critical_pressure float8 := 10.0;
    temperature_percent float8;
    pressure_percent float8;
	temperature_percent_rounded float8;
    pressure_percent_rounded float8;
BEGIN
    temperature_percent := (NEW.temperature / critical_temperature) * 100;
    pressure_percent := (NEW.pressure / critical_pressure) * 100;
	temperature_percent_rounded := ROUND(temperature_percent::numeric, 3);
	pressure_percent_rounded := ROUND(pressure_percent::numeric, 3);
	
    IF temperature_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('Furnace', 'Температура в печке достигла ' || temperature_percent_rounded || '% критического значения: ' || NEW.temperature);
    END IF;

    IF pressure_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('Furnace', 'Давление в печке достигло ' || pressure_percent_rounded || '% критического значения: ' || NEW.pressure);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--
CREATE TRIGGER Furnace_alert_trigger
AFTER INSERT ON Furnace
FOR EACH ROW
EXECUTE FUNCTION Check_furnace_alert();
--- - Триггер для автоматического создания записи в т. Alerts при достижения критического значения в машине литья
CREATE OR REPLACE FUNCTION Check_casting_machine_alert() RETURNS TRIGGER AS $$
DECLARE
    critical_mold_temperature float8 := 300.0;
    critical_casting_speed float8 := 9.0;
    mold_temperature_percent float8;
    casting_speed_percent float8;
    mold_temperature_percent_rounded float8;
    casting_speed_percent_rounded float8;
BEGIN
    mold_temperature_percent := (NEW.mold_temperature / critical_mold_temperature) * 100;
    casting_speed_percent := (NEW.casting_speed / critical_casting_speed) * 100;
	mold_temperature_percent_rounded := ROUND(mold_temperature_percent::numeric, 3);
	casting_speed_percent_rounded := ROUND(casting_speed_percent::numeric, 3);
	
    IF mold_temperature_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('CastingMachine', 'Температура формы в литейной машине достигла ' || mold_temperature_percent_rounded || '% критического значения: ' || NEW.mold_temperature);
    END IF;

    IF casting_speed_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('CastingMachine', 'Скорость литья достигла ' || casting_speed_percent_rounded || '% критического значения: ' || NEW.casting_speed);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--
CREATE TRIGGER CastingMachine_alert_trigger
AFTER INSERT ON CastingMachine
FOR EACH ROW
EXECUTE FUNCTION Check_casting_machine_alert();
--- - Триггер для автоматического создания записи в т. Alerts при достижения критического значения в прокатном стане
CREATE OR REPLACE FUNCTION Check_rolling_mill_alert() RETURNS TRIGGER AS $$
DECLARE
    critical_roller_speed float8 := 14.0;
    critical_sheet_thickness float8 := 6.0;
    roller_speed_percent float8;
    sheet_thickness_percent float8;
    roller_speed_percent_rounded float8;
    sheet_thickness_percent_rounded float8;
BEGIN
    roller_speed_percent := (NEW.roller_speed / critical_roller_speed) * 100;
    sheet_thickness_percent := (NEW.sheet_thickness / critical_sheet_thickness) * 100;
	roller_speed_percent_rounded := ROUND(roller_speed_percent::numeric, 3);
	sheet_thickness_percent_rounded := ROUND(sheet_thickness_percent::numeric, 3);
	
    IF roller_speed_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('RollingMill', 'Скорость роликов в прокатном стане достигла ' || roller_speed_percent_rounded || '% критического значения: ' || NEW.roller_speed);
    END IF;

    IF sheet_thickness_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('RollingMill', 'Толщина листа в прокатном стане достигла ' || sheet_thickness_percent_rounded || '% критического значения: ' || NEW.sheet_thickness);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--
CREATE TRIGGER RollingMill_alert_trigger
AFTER INSERT ON RollingMill
FOR EACH ROW
EXECUTE FUNCTION Check_rolling_mill_alert();
--- - Триггер для автоматического создания записи в т. Alerts при достижения критического значения в кране
CREATE OR REPLACE FUNCTION Check_crane_alert() RETURNS TRIGGER AS $$
DECLARE
    critical_load_weight float8 := 2000.0;
    critical_crane_speed float8 := 9.0;
    load_weight_percent float8;
    crane_speed_percent float8;
	load_weight_percent_rounded float8;
    crane_speed_percent_rounded float8;
BEGIN
    load_weight_percent := (NEW.load_weight / critical_load_weight) * 100;
    crane_speed_percent := (NEW.crane_speed / critical_crane_speed) * 100;
	load_weight_percent_rounded := ROUND(load_weight_percent::numeric, 3);
	crane_speed_percent_rounded := ROUND(crane_speed_percent::numeric, 3);
	
    IF load_weight_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('Crane', 'Вес груза в кране достиг ' || load_weight_percent_rounded || '% критического значения: ' || NEW.load_weight);
    END IF;

    IF crane_speed_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('Crane', 'Скорость крана достигла ' || crane_speed_percent_rounded || '% критического значения: ' || NEW.crane_speed);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--
CREATE TRIGGER Crane_alert_trigger
AFTER INSERT ON Crane
FOR EACH ROW
EXECUTE FUNCTION Check_crane_alert();
--- - Триггер для автоматического создания записи в т. Alerts при достижения критического значения в системе охлаждения
CREATE OR REPLACE FUNCTION Check_cooling_system_alert() RETURNS TRIGGER AS $$
DECLARE
    critical_coolant_temperature float8 := 100.0;
    critical_coolant_flow_rate float8 := 70.0;
    coolant_temperature_percent float8;
    coolant_flow_rate_percent float8;
	coolant_temperature_percent_rounded float8;
    coolant_flow_rate_percent_rounded float8;
BEGIN
    coolant_temperature_percent := (NEW.coolant_temperature / critical_coolant_temperature) * 100;
    coolant_flow_rate_percent := (NEW.coolant_flow_rate / critical_coolant_flow_rate) * 100;
	coolant_temperature_percent_rounded := ROUND(coolant_temperature_percent::numeric, 3);
	coolant_flow_rate_percent_rounded := ROUND(coolant_flow_rate_percent::numeric, 3);
	
    IF coolant_temperature_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('CoolingSystem', 'Температура охлаждающей жидкости достигла ' || coolant_temperature_percent_rounded || '% критического значения: ' || NEW.coolant_temperature);
    END IF;

    IF coolant_flow_rate_percent >= 65 THEN
        INSERT INTO Alerts (equipment_type, alert_message)
        VALUES ('CoolingSystem', 'Скорость потока охлаждающей жидкости достигла ' || coolant_flow_rate_percent_rounded || '% критического значения: ' || NEW.coolant_flow_rate);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
--
CREATE TRIGGER CoolingSystem_alert_trigger
AFTER INSERT ON CoolingSystem
FOR EACH ROW
EXECUTE FUNCTION Check_cooling_system_alert();

	-- - ! - ! - - - - | | | Запросы | | | - - - - ! - ! - --
/*
Запросы.

1) Список всех "тревог". Конкретно печки. 
Когда параметры достигают 65% от крит. знач-я.
SELECT *
FROM Alerts
WHERE equipment_type = 'Furnace'

Увидели, когда конкретно начали знач-я повыш-ся.
Запомнили дату. И вводим следующий запрос.

2) Список значений печки близких к критическим в заданный промежуток времени.

SELECT *
FROM Get_alert_details('Furnace', '2024-05-31 14:21:57', '2024-05-31 14:22:05')

ИЛИ

SELECT *
FROM Get_alert_details_to_json('Furnace', '2024-05-31 14:21:57', '2024-05-31 14:22:05')

3) Посмотреть все значения печки
SELECT *
FROM Furnace

можно дописать WHERE registered_value BETWEEN '...' AND '...' , чтобы узнать за конкретный период времени
*/