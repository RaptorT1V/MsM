	-- - ! - - - - - - | Блок DROP'ов | - - - - - - ! - --
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Titles CASCADE;
DROP TABLE IF EXISTS SinteringMachine_1 CASCADE;
DROP TABLE IF EXISTS SinteringMachine_2 CASCADE;
DROP TABLE IF EXISTS BlastFurnace_1 CASCADE;
DROP TABLE IF EXISTS BlastFurnace_2 CASCADE;
DROP TABLE IF EXISTS FlexibleModularFurnace_1 CASCADE;
DROP TABLE IF EXISTS FlexibleModularFurnace_2 CASCADE;
DROP TABLE IF EXISTS MediumPressureBoiler_1 CASCADE;
DROP TABLE IF EXISTS MediumPressureBoiler_2 CASCADE;
-- -- -- -- -- -- -- -- -- -- -- -- --
-- DROP TYPE IF EXISTS;
-- -- -- -- -- -- -- -- -- -- -- -- --
-- DROP INDEX IF EXISTS;
-- -- -- -- -- -- -- -- -- -- -- -- --
DROP FUNCTION IF EXISTS Hash_password() CASCADE;
DROP FUNCTION IF EXISTS Add_plus_to_phone() CASCADE;
-- -- -- -- -- -- -- -- -- -- -- -- --
DROP TRIGGER IF EXISTS Hash_password_trigger ON Users;     
DROP TRIGGER IF EXISTS Add_plus_to_phone_trigger ON Users;
-- -- -- -- -- -- -- -- -- -- -- -- --
DROP EXTENSION IF EXISTS pgcrypto;

	-- - - - - - - - - | Подключение расширений | - - - - - - - - --
CREATE EXTENSION IF NOT EXISTS pgcrypto;
	
	-- - - - - - - - - | Создание перечислений | - - - - - - - - --
	
	-- - ! - - - - - - | Создание таблиц (+ Primary Key) | - - - - - - ! - --
CREATE TABLE Users (
    user_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	title_id int NOT NULL,
    first_name varchar(50) NOT NULL,
	middle_name varchar(50),
    last_name varchar(50) NOT NULL,
    e_mail varchar(60),
    phone_number char(12),
	user_password varchar(255) NOT NULL,
	registered timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE Titles (
	title_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	title_name text NOT NULL
);
-- -- --
CREATE TABLE SinteringMachine_1 ( -- Агломерационная машина №1
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    layer_length float8 NOT NULL, -- длина слоя (мм)
    charge_temperature float8 NOT NULL, -- температура шихты (С°)
    speed float8 NOT NULL, -- скорость (м/мин)
    rarefaction float8 NOT NULL, -- разрежение (мм. вод. ст.)
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE SinteringMachine_2 ( -- АМ №2
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- может быть вообще не нужна эта колонка? всё равно по registered_value всегда выборку делаем
    layer_length float8 NOT NULL,
    charge_temperature float8 NOT NULL,
    speed float8 NOT NULL,
    rarefaction float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
-- --
CREATE TABLE BlastFurnace_1 ( -- Доменная печь №1
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    blast_flow_rate float8 NOT NULL, -- объёмный расход дутья (м³/мин)
    blast_pressure float8 NOT NULL, -- давление дутья (кгс/см²)
    natural_gas_flow_rate float8 NOT NULL, -- объёмный расход природного газа (м³/час)
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE BlastFurnace_2 ( -- ДП №2
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- может быть вообще не нужна эта колонка? всё равно по registered_value всегда выборку делаем
    blast_flow_rate float8 NOT NULL,
    blast_pressure float8 NOT NULL,
    natural_gas_flow_rate float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
-- --
CREATE TABLE FlexibleModularFurnace_1 ( -- Гибкая модульная печь №1
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    argon_flow_rate float8 NOT NULL, -- объёмный расход аргона (л/мин)
    oxygen_flow_rate float8 NOT NULL, -- объёмный расход кислорода (м³/ч)
    power float8 NOT NULL, -- мощность (кВт/ч)
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE FlexibleModularFurnace_2 ( -- ГМП №2
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- может быть вообще не нужна эта колонка? всё равно по registered_value всегда выборку делаем
    argon_flow_rate float8 NOT NULL,
    oxygen_flow_rate float8 NOT NULL,
    power float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
-- --
CREATE TABLE MediumPressureBoiler_1 ( -- Паровой котёл среднего давления №1
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    temperature float8 NOT NULL, -- температура (С°)
    pressure float8 NOT NULL, -- давление (МПа)
    steam_output float8 NOT NULL, -- выработка пара (т/ч)
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);
--
CREATE TABLE MediumPressureBoiler_2 ( -- КСД №2
    value_id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- может быть вообще не нужна эта колонка? всё равно по registered_value всегда выборку делаем
    temperature float8 NOT NULL,
    pressure float8 NOT NULL,
    steam_output float8 NOT NULL,
    registered_value timestamp DEFAULT CURRENT_TIMESTAMP
);

	-- - ! - - - - - - | Создание ограничений: Foreign Key, Check | - - - - - - ! - --
ALTER TABLE Users ADD CONSTRAINT FK_Users_Titles FOREIGN KEY (title_id) REFERENCES Titles (title_id);
-- -- -- --
ALTER TABLE Users ADD CONSTRAINT Unique_Email UNIQUE (e_mail);
ALTER TABLE Users ADD CONSTRAINT Unique_Phone UNIQUE (phone_number);
-- -- -- -- -- -- -- --
ALTER TABLE Users
ADD CONSTRAINT Check_email_mask -- Проверка маски e-mail и запрещённых символов
CHECK (e_mail ~ '^[A-Za-z0-9._-]+@[A-Za-z0-9]+\.[A-Z|a-z]{2,}$');
--
ALTER TABLE Users
ADD CONSTRAINT Check_password_english_chars -- Проверка: пароль может быть только на английском
CHECK (user_password ~ '^[a-zA-Z0-9!$^&()-_+=,.{}]+$');
--- ---

	-- - ! - - - - - - | Создание функций и хранимых процедур | - - - - - - ! - --

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
-- Может можно будет совсем убрать этот триггер, если в форму ввода номера телефона в мобильном приложении автоматически заложить первые 2 знака "+7"
CREATE OR REPLACE FUNCTION Add_plus_to_phone()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.phone_number IS NOT NULL AND LEFT(NEW.phone_number, 1) = '7' THEN
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

	-- - ! - ! - - - - | | | Запросы | | | - - - - ! - ! - --
/*
select * from sinteringmachine_1

SELECT ROW_NUMBER() OVER (ORDER BY registered_value) AS row_id, *
FROM blastfurnace_1;
*/