/*
    = = = = = = =
        DROPs
    = = = = = = =
*/

-- ENUMs & DICTs
DROP TYPE IF EXISTS alarm_types CASCADE;
DROP TYPE IF EXISTS line_types CASCADE;
DROP TABLE IF EXISTS aggregate_types CASCADE;
DROP TABLE IF EXISTS actuator_types CASCADE;
DROP TABLE IF EXISTS parameter_types CASCADE;
DROP TABLE IF EXISTS job_titles CASCADE;

-- Tables
DROP TABLE IF EXISTS shops CASCADE;
DROP TABLE IF EXISTS lines CASCADE;
DROP TABLE IF EXISTS aggregates CASCADE;
DROP TABLE IF EXISTS actuators CASCADE;
DROP TABLE IF EXISTS parameters CASCADE;
DROP TABLE IF EXISTS parameter_data CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS user_settings CASCADE;
DROP TABLE IF EXISTS monitoring_rules CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;

-- Indexes
DROP INDEX IF EXISTS ix_actuators_aggregate_id;
DROP INDEX IF EXISTS ix_actuators_actuator_type_id;
DROP INDEX IF EXISTS ix_monitoring_rules_user_id;
DROP INDEX IF EXISTS ix_monitoring_rules_parameter_id;
DROP INDEX IF EXISTS ix_alerts_rule_id;
DROP INDEX IF EXISTS ix_alerts_parameter_data_id;
DROP INDEX IF EXISTS ix_alerts_alert_timestamp;
DROP INDEX IF EXISTS ix_users_job_title_id;

-- Functions
-- DROP FUNCTION IF EXISTS func CASCADE;

-- Triggers
-- DROP TRIGGER IF EXISTS trig ON exam_function;

-- Roles
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_user') THEN
        REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM app_user;
        REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM app_user;
        REVOKE ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public FROM app_user;
        DROP OWNED BY app_user CASCADE;
        DROP ROLE app_user;
    END IF;
END $$;

-- Extensions
DROP EXTENSION IF EXISTS pgcrypto;
DROP EXTENSION IF EXISTS timescaledb;


/*
    = = = = = = = = = =
        Extensions
    = = = = = = = = = =
*/


CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = = = =
        ENUMs & DICTs    
    = = = = = = = = = = =
*/


-- П. alarm_types предназначено для классификации типов уведомлений при возникшей тревоге (4)
CREATE TYPE alarm_types AS ENUM ('SIREN', 'FLASH', 'VIBRATION', 'NOTIFICATION');


-- П. line_types предназначено для хранения номеров линий (4)
CREATE TYPE line_types AS ENUM ('Первая', 'Вторая', 'Третья', 'Четвёртая');


-- Таблица aggregate_types содержит справочник типов агрегатов
CREATE TABLE aggregate_types (
    aggregate_type_id INT GENERATED ALWAYS AS IDENTITY,
    aggregate_type_name VARCHAR(55) NOT NULL,

    CONSTRAINT pk_aggregate_types PRIMARY KEY (aggregate_type_id),
    CONSTRAINT uq_aggregate_types_aggregate_type_name UNIQUE (aggregate_type_name)
);


-- Таблица actuator_types содержит справочник типов исполнительных механизмов
CREATE TABLE actuator_types (
    actuator_type_id INT GENERATED ALWAYS AS IDENTITY,
    actuator_type_name VARCHAR(60) NOT NULL,

    CONSTRAINT pk_actuator_types PRIMARY KEY (actuator_type_id),
    CONSTRAINT uq_actuator_types_actuator_type_name UNIQUE (actuator_type_name)
);


-- Таблица parameter_types содержит справочник типов параметров с единицами измерения (например, электрический ток [A]).
CREATE TABLE parameter_types (
    parameter_type_id INT GENERATED ALWAYS AS IDENTITY,
    parameter_type_name VARCHAR(40) NOT NULL,
    parameter_unit VARCHAR(20),

    CONSTRAINT pk_parameter_types PRIMARY KEY (parameter_type_id),
    CONSTRAINT uq_parameter_types_parameter_type_name UNIQUE (parameter_type_name)
);


-- Таблица job_titles содержит справочник типов должностей
CREATE TABLE job_titles (
    job_title_id INT GENERATED ALWAYS AS IDENTITY,
    job_title_name VARCHAR(65) NOT NULL,

    CONSTRAINT pk_job_titles PRIMARY KEY (job_title_id),
    CONSTRAINT uq_job_titles_job_title_name UNIQUE (job_title_name)
);


/*
    = = = = = = = =
        Tables
    = = = = = = = =
*/


-- Таблица shops определяет цехи предприятия. [Уровень 1]. По факту это тоже справочник :).
CREATE TABLE shops (
    shop_id INT GENERATED ALWAYS AS IDENTITY,
    shop_name VARCHAR(35) NOT NULL,

    CONSTRAINT pk_shops PRIMARY KEY (shop_id),
    CONSTRAINT uq_shops_shop_name UNIQUE (shop_name)
);


-- Таблица lines определяет производственные линии внутри цехов. [Уровень 2].
CREATE TABLE lines (
    line_id INT GENERATED ALWAYS AS IDENTITY,
    shop_id INT NOT NULL,
    line_type line_types NOT NULL,

    CONSTRAINT pk_lines PRIMARY KEY (line_id),
    CONSTRAINT uq_lines_shop_id_line_type UNIQUE (shop_id, line_type),
    CONSTRAINT fk_lines_shop_id FOREIGN KEY (shop_id) REFERENCES shops(shop_id) ON DELETE CASCADE
);


-- Таблица aggregates определяет агрегаты на производственных линиях. [Уровень 3].
CREATE TABLE aggregates (
    aggregate_id INT GENERATED ALWAYS AS IDENTITY,
    line_id INT NOT NULL,
    aggregate_type_id INT NOT NULL,

    CONSTRAINT pk_aggregates PRIMARY KEY (aggregate_id),
    CONSTRAINT uq_aggregates_line_id_aggregate_type_id UNIQUE (line_id, aggregate_type_id),
    CONSTRAINT fk_aggregates_line_id FOREIGN KEY (line_id) REFERENCES lines(line_id) ON DELETE CASCADE,
    CONSTRAINT fk_aggregates_aggregate_type_id FOREIGN KEY (aggregate_type_id) REFERENCES aggregate_types(aggregate_type_id) ON DELETE RESTRICT
);


-- Таблица actuators определяет исполнительные механизмы (узлы, приводы) внутри агрегатов. [Уровень 4].
CREATE TABLE actuators (
    actuator_id INT GENERATED ALWAYS AS IDENTITY,
    aggregate_id INT NOT NULL,
    actuator_type_id INT NOT NULL,

    CONSTRAINT pk_actuators PRIMARY KEY (actuator_id),
    -- Здесь нету CONSTRAINT uq_actuators_aggregate_id_actuator_type_id UNIQUE (aggregate_id, actuator_type_id), потому что в редких случаях у агрегата может быть 2 актуатора (2 двигателя, например)
    CONSTRAINT fk_actuators_aggregate_id FOREIGN KEY (aggregate_id) REFERENCES aggregates(aggregate_id) ON DELETE CASCADE,
    CONSTRAINT fk_actuators_actuator_type_id FOREIGN KEY (actuator_type_id) REFERENCES actuator_types(actuator_type_id) ON DELETE RESTRICT
);


-- Таблица parameters связывает типы параметров с исполнительными механизмами (узлами/приводами).
CREATE TABLE parameters (
    parameter_id INT GENERATED ALWAYS AS IDENTITY,
    actuator_id INT NOT NULL,
    parameter_type_id INT NOT NULL,

    CONSTRAINT pk_parameters PRIMARY KEY (parameter_id),
    CONSTRAINT uq_parameters_actuator_id_parameter_type_id UNIQUE (actuator_id, parameter_type_id),
    CONSTRAINT fk_parameters_actuator_id FOREIGN KEY (actuator_id) REFERENCES actuators(actuator_id) ON DELETE CASCADE,
    CONSTRAINT fk_parameters_parameter_type_id FOREIGN KEY (parameter_type_id) REFERENCES parameter_types(parameter_type_id) ON DELETE RESTRICT
);


-- Таблица parameter_data содержит значения параметров, измеренных датчиками в определённое время (временные ряды данных).
CREATE TABLE parameter_data (
    parameter_data_id BIGINT GENERATED ALWAYS AS IDENTITY,
    parameter_id INT NOT NULL,
    parameter_value FLOAT8 NOT NULL,
    data_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- CONSTRAINT pk_parameter_data PRIMARY KEY (parameter_data_id, data_timestamp), -- > PK для оптимизации TimescaleDB создастся позже (после создания гипер-таблицы)
    CONSTRAINT fk_parameter_data_parameter_id FOREIGN KEY (parameter_id) REFERENCES parameters(parameter_id) ON DELETE CASCADE
);


-- Таблица users содержит информацию о пользователях
CREATE TABLE users (
    user_id INT GENERATED ALWAYS AS IDENTITY,
    job_title_id INT NOT NULL,
    first_name VARCHAR(26) NOT NULL,
    last_name VARCHAR(36) NOT NULL,
    middle_name VARCHAR(24),
    email VARCHAR(60) NOT NULL,
    phone CHAR(12) NOT NULL,
    password_hash VARCHAR(228) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_users PRIMARY KEY (user_id),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT uq_users_phone UNIQUE (phone),
    CONSTRAINT ck_users_email_format CHECK (email ~* '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'),
    CONSTRAINT ck_users_phone_format CHECK (phone ~ '^\+7\d{10}$'),
    CONSTRAINT fk_users_job_title_id FOREIGN KEY (job_title_id) REFERENCES job_titles(job_title_id) ON DELETE RESTRICT
);


-- Таблица user_settings содержит настройки пользователей
CREATE TABLE user_settings (
    user_id INT,
    theme VARCHAR(10) DEFAULT 'light',
    language VARCHAR(5) DEFAULT 'ru',
    alarm_types alarm_types[] DEFAULT '{NOTIFICATION}',
    is_rules_public BOOLEAN DEFAULT FALSE,

    CONSTRAINT pk_user_settings PRIMARY KEY (user_id),
    CONSTRAINT ck_user_settings_theme_option CHECK (theme IN ('light', 'dark')),
    CONSTRAINT ck_user_settings_language_option CHECK (language IN ('ru', 'en')),
    CONSTRAINT fk_user_settings_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


-- Таблица monitoring_rules содержит правила мониторинга (условия для параметров)
CREATE TABLE monitoring_rules (
    rule_id INT GENERATED ALWAYS AS IDENTITY,
    user_id INT NOT NULL,
    parameter_id INT NOT NULL,
    rule_name VARCHAR(50),
    comparison_operator VARCHAR(2) NOT NULL,
    threshold FLOAT8 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_monitoring_rules PRIMARY KEY (rule_id),
    CONSTRAINT ck_monitoring_rules_comparison_operator CHECK (comparison_operator IN ('>', '<', '=', '>=', '<=')),
    CONSTRAINT fk_monitoring_rules_user_id FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_monitoring_rules_parameter_id FOREIGN KEY (parameter_id) REFERENCES parameters(parameter_id) ON DELETE CASCADE
);


-- Таблица alerts содержит журнал тревог (срабатывания правил)
CREATE TABLE alerts (
    alert_id BIGINT GENERATED ALWAYS AS IDENTITY,
    rule_id INT NOT NULL,
    parameter_data_id BIGINT NOT NULL,
    alert_message VARCHAR(150),
    is_read BOOLEAN DEFAULT FALSE,
    alert_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_alerts PRIMARY KEY (alert_id),
    CONSTRAINT fk_alerts_rule_id FOREIGN KEY (rule_id) REFERENCES monitoring_rules(rule_id) ON DELETE CASCADE
);


/*
    = = = = = = = = = =
        TimeScaleDb
    = = = = = = = = = =
*/


  -- Преобразуем parameter_data в гипертаблицу TimescaleDB
SELECT create_hypertable('parameter_data', 'data_timestamp');

  -- Создаём оптимальный первичный ключ для гипертаблицы (идентификатор + время)
ALTER TABLE parameter_data ADD CONSTRAINT pk_parameter_data PRIMARY KEY (parameter_id, data_timestamp);

  -- Настраиваем сжатие данных старше 1 месяца
ALTER TABLE parameter_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'parameter_id'
);
SELECT add_compression_policy('parameter_data', INTERVAL '1 month');

  -- (Опционально) Настраиваем удаление данных старше 6 месяцев
SELECT add_retention_policy('parameter_data', INTERVAL '6 months');

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = =
        Indexes    
    = = = = = = = =
*/


-- Для иерархии (Foreign Keys)
CREATE INDEX IF NOT EXISTS ix_actuators_aggregate_id ON actuators (aggregate_id);
CREATE INDEX IF NOT EXISTS ix_actuators_actuator_type_id ON actuators (actuator_type_id);

-- Для monitoring_rules (Foreign Keys)
CREATE INDEX IF NOT EXISTS ix_monitoring_rules_user_id ON monitoring_rules (user_id);
CREATE INDEX IF NOT EXISTS ix_monitoring_rules_parameter_id ON monitoring_rules (parameter_id);

-- Для alerts
CREATE INDEX IF NOT EXISTS ix_alerts_rule_id ON alerts (rule_id);
CREATE INDEX IF NOT EXISTS ix_alerts_parameter_data_id ON alerts (parameter_data_id);
CREATE INDEX IF NOT EXISTS ix_alerts_alert_timestamp ON alerts (alert_timestamp);

-- Для users (job_titles)
CREATE INDEX IF NOT EXISTS ix_users_job_title_id ON users (job_title_id);

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = =
        Functions    
    = = = = = = = = =
*/


--


/*
    = = = = = = = = =
        Triggers    
    = = = = = = = = =
*/


--

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = = = = =
        INSERT queries
    = = = = = = = = = = = =
*/


------------------------------------------------
-- Заполнение таблицы job_titles
------------------------------------------------

INSERT INTO job_titles (job_title_name) VALUES
('Директор'), -- (самый главный дядя; не разбирается ни в чём, кроме как в заработке денег; занимает верхушку пищевой цепи)
('Главный аналитик'), -- (видит все цеха)
('Начальник аглофабрики'), -- (видит только свой *агломерационный* цех)
('Начальник ЭСПЦ'), -- (видит только свой *электросталеплавильный* цех)
('Аналитик 1-ой линии аглофабрики'), -- (видит только свою *1-ую* линию *агломерационного* цеха)
('Аналитик 2-ой линии аглофабрики'), -- (видит только свою *2-ую* линию *агломерационного* цеха)
('Аналитик 1-ой линии ЭСПЦ'), -- (видит только свою *1-ую* линию *электросталеплавильного* цеха)
('Аналитик 2-ой линии ЭСПЦ'); -- (видит только свою *2-ую* линию *электросталеплавильного* цеха)

--------------------------------------------
-- Заполнение таблицы users
--------------------------------------------

INSERT INTO users (job_title_id, last_name, first_name, middle_name, email, phone, password_hash)
VALUES
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Директор'),
    'Первый', 'Директор', 'Директорович', 'rektor1337@yahoo.com', '+79021357901',
    crypt('Директор', gen_salt('bf')) -- пароль 'Директор'
),
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Главный аналитик'),
    'Главко', 'Аналитик', 'Андреевич', 'boss777@gmail.com', '+79159753102',
    crypt('Главко', gen_salt('bf')) -- пароль 'Главко'
),
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Начальник аглофабрики'),
    'Любимов', 'Виктор', 'Аглоцехович', 'aglolove@vivaldi.com', '+79059871234',
    crypt('Аглолюбовь', gen_salt('bf')) -- пароль 'Аглолюбовь'
),
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Начальник ЭСПЦ'),
    'Любимова', 'Александра', 'Эдуардовна', 'efcforever@vivaldi.com', '+79051234987',
    crypt('ЭСПЦсила', gen_salt('bf')) -- пароль 'ЭСПЦсила'
),
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Аналитик 1-ой линии аглофабрики'),
    'Жмышенко', 'Валерий', 'Альбертович', 'valakas1488@mail.ru', '+79862754228',
    crypt('Гладиатор', gen_salt('bf')) -- пароль 'Гладиатор'
),
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Аналитик 2-ой линии аглофабрики'),
    'Цаль', 'Виталий', 'Олегович', 'papich7000first@twitch.tv', '+79874692107',
    crypt('Папич', gen_salt('bf')) -- пароль 'Папич'
),
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Аналитик 1-ой линии ЭСПЦ'),
    'Иванов', 'Иван', 'Иванович', 'ivanov123@list.ru', '+79196384421',
    crypt('Иванов', gen_salt('bf')) -- пароль 'Иванов'
),
(
    (SELECT job_title_id FROM job_titles WHERE job_title_name = 'Аналитик 2-ой линии ЭСПЦ'),
    'Петров', 'Пётр', 'Петрович', 'petrov456@yandex.ru', '+79129876543',
    crypt('Петров', gen_salt('bf')) -- пароль 'Петров'
);

------------------------------------------
-- Заполнение таблицы shops
------------------------------------------

INSERT INTO shops (shop_name) VALUES
('Агломерационный цех'), 
('Доменный цех'), 
('Коксохимический цех'), 
('Кислородно-компрессорный цех'), 
('Листопрокатный цех'), 
('Теплоэлектроцентраль'), 
('Трубопрокатный цех'), 
('Фасонно-литейный цех'), 
('Цех водоснабжения'), 
('Электросталеплавильный цех');

----------------------------------------------------
-- Заполнение таблицы aggregate_types
----------------------------------------------------

INSERT INTO aggregate_types (aggregate_type_name) VALUES
('Агломашина'),
('Конвейер'),
('Окомкователь'),
('Эксгаустер'),
('ДСП'),
('МНЛЗ');

----------------------------------------------------
-- Заполнение таблицы actuator_types
----------------------------------------------------

INSERT INTO actuator_types (actuator_type_name) VALUES
('Кристаллизатор'),
('Лента'),
('Нагнетатель'),
('Редуктор'),
('Система смазки'),
('Трансформатор'),
('Электродвигатель постоянного тока'),
('Электродвигатель переменного тока (3ф)');

--------------------------------------------------
-- Заполнение таблицы parameter_types
--------------------------------------------------

INSERT INTO parameter_types (parameter_type_name, parameter_unit) VALUES
-- Электрические параметры
('Электрический ток', 'А'),
('Мощность', 'кВт'),
-- Температурные параметры
('Температура обмотки', '℃'),
('Температура масла', '℃'), 
('Температура сердечника статора', '℃'),
('Температура сердечника индуктора', '℃'),
('Температура опорного подшипника', '℃'),
('Температура шихты', '℃'),
('Температура входящей воды', '℃'),
('Температура отходящей воды', '℃'),
-- Механические параметры
('Вибрация опорного подшипника', 'мм/с'),
('Скорость ленты', 'м/мин'),
('Высота слоя', 'мм'),
('Уровень масла', 'мм'),
('Уровень металла', 'мм'),
('Разрежение', 'мм. вод. ст.'),
('Давление масла в системе', 'кПа');

-- ==========================================================================================
--     Заполнение уровней иерархии: агрегаты, исполняющие механизмы, параметры
-- ==========================================================================================

WITH shop_ids AS (
    SELECT shop_id, shop_name FROM shops
), agg_type_ids AS (
    SELECT aggregate_type_id, aggregate_type_name FROM aggregate_types
), act_type_ids AS (
    SELECT actuator_type_id, actuator_type_name FROM actuator_types
), param_type_ids AS (
    SELECT parameter_type_id, parameter_type_name FROM parameter_types
),
-- №1: Вставить Линии
inserted_lines AS (
    INSERT INTO lines (shop_id, line_type)
    SELECT s.shop_id, lt.line_enum
    FROM (VALUES
        ('Агломерационный цех', 'Первая'::line_types),
        ('Агломерационный цех', 'Вторая'::line_types),
        ('Электросталеплавильный цех', 'Первая'::line_types),
        ('Электросталеплавильный цех', 'Вторая'::line_types)
    ) AS lt (shop_name, line_enum)
    JOIN shop_ids s ON s.shop_name = lt.shop_name
    ON CONFLICT (shop_id, line_type) DO UPDATE SET line_type = EXCLUDED.line_type -- Обновить в случае повторного запуска
    RETURNING line_id, shop_id, line_type
),
-- №2: Вставить Агрегаты
inserted_aggregates AS (
    INSERT INTO aggregates (line_id, aggregate_type_id)
    SELECT il.line_id, agt.aggregate_type_id
    FROM (VALUES
        ('Агломерационный цех', 'Первая'::line_types, 'Окомкователь'),
        ('Агломерационный цех', 'Первая'::line_types, 'Конвейер'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер'),
        ('Электросталеплавильный цех', 'Первая'::line_types, 'МНЛЗ'),
        ('Электросталеплавильный цех', 'Вторая'::line_types, 'ДСП')
    ) AS src (shop_name, line_enum, agg_type_name)
    JOIN shop_ids ish ON ish.shop_name = src.shop_name
    JOIN inserted_lines il ON il.shop_id = ish.shop_id AND il.line_type = src.line_enum
    JOIN agg_type_ids agt ON agt.aggregate_type_name = src.agg_type_name
    ON CONFLICT (line_id, aggregate_type_id) DO UPDATE SET aggregate_type_id = EXCLUDED.aggregate_type_id
    RETURNING aggregate_id, line_id, aggregate_type_id
),
-- №3: Вставить Актуаторы
inserted_actuators AS (
    INSERT INTO actuators (aggregate_id, actuator_type_id)
    SELECT ia.aggregate_id, actt.actuator_type_id
    FROM (VALUES
        ('Агломерационный цех', 'Первая'::line_types, 'Окомкователь', 'Электродвигатель переменного тока (3ф)'),
        ('Агломерационный цех', 'Первая'::line_types, 'Окомкователь', 'Редуктор'),
        ('Агломерационный цех', 'Первая'::line_types, 'Конвейер', 'Электродвигатель постоянного тока'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Электродвигатель постоянного тока'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Редуктор'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Лента'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Нагнетатель'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Система смазки'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Электродвигатель постоянного тока'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Редуктор'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Лента'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Нагнетатель'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Система смазки'),
        ('Электросталеплавильный цех', 'Первая'::line_types, 'МНЛЗ', 'Кристаллизатор'),
        ('Электросталеплавильный цех', 'Вторая'::line_types, 'ДСП', 'Трансформатор')
    ) AS src (shop_name, line_enum, agg_type_name, act_type_name)
    JOIN shop_ids ish ON ish.shop_name = src.shop_name
    JOIN inserted_lines il ON il.shop_id = ish.shop_id AND il.line_type = src.line_enum
    JOIN agg_type_ids agt ON agt.aggregate_type_name = src.agg_type_name
    JOIN inserted_aggregates ia ON ia.line_id = il.line_id AND ia.aggregate_type_id = agt.aggregate_type_id
    JOIN act_type_ids actt ON actt.actuator_type_name = src.act_type_name
    RETURNING actuator_id, aggregate_id, actuator_type_id
),
-- №4: Определить данные для вставки параметров
actuator_parameters_data(shop_name, line_enum, agg_type_name, act_type_name, param_type_name) AS (
   VALUES
        -- Аглоцех | 1-ая линия 
        ('Агломерационный цех', 'Первая'::line_types, 'Окомкователь', 'Электродвигатель переменного тока (3ф)', 'Электрический ток'),
        ('Агломерационный цех', 'Первая'::line_types, 'Окомкователь', 'Электродвигатель переменного тока (3ф)', 'Температура обмотки'),
        ('Агломерационный цех', 'Первая'::line_types, 'Окомкователь', 'Редуктор', 'Температура масла'),
        ('Агломерационный цех', 'Первая'::line_types, 'Окомкователь', 'Редуктор', 'Уровень масла'),
        ('Агломерационный цех', 'Первая'::line_types, 'Конвейер', 'Электродвигатель постоянного тока', 'Электрический ток'),
        ('Агломерационный цех', 'Первая'::line_types, 'Конвейер', 'Электродвигатель постоянного тока', 'Температура сердечника статора'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Электродвигатель постоянного тока', 'Электрический ток'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Электродвигатель постоянного тока', 'Температура сердечника индуктора'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Редуктор', 'Температура масла'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Редуктор', 'Уровень масла'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Лента', 'Скорость ленты'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Лента', 'Высота слоя'),
        ('Агломерационный цех', 'Первая'::line_types, 'Агломашина', 'Лента', 'Температура шихты'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Электрический ток'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Температура обмотки'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Температура опорного подшипника'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Вибрация опорного подшипника'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Нагнетатель', 'Разрежение'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Нагнетатель', 'Температура опорного подшипника'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Нагнетатель', 'Вибрация опорного подшипника'),
        ('Агломерационный цех', 'Первая'::line_types, 'Эксгаустер', 'Система смазки', 'Давление масла в системе'),
        -- Аглоцех | 2-ая линия 
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Электродвигатель постоянного тока', 'Электрический ток'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Электродвигатель постоянного тока', 'Температура сердечника индуктора'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Редуктор', 'Температура масла'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Редуктор', 'Уровень масла'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Лента', 'Скорость ленты'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Лента', 'Высота слоя'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Агломашина', 'Лента', 'Температура шихты'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Электрический ток'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Температура обмотки'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Температура опорного подшипника'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Электродвигатель постоянного тока', 'Вибрация опорного подшипника'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Нагнетатель', 'Разрежение'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Нагнетатель', 'Температура опорного подшипника'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Нагнетатель', 'Вибрация опорного подшипника'),
        ('Агломерационный цех', 'Вторая'::line_types, 'Эксгаустер', 'Система смазки', 'Давление масла в системе'),
        -- ЭСПЦ
        ('Электросталеплавильный цех', 'Первая'::line_types, 'МНЛЗ', 'Кристаллизатор', 'Температура входящей воды'),
        ('Электросталеплавильный цех', 'Первая'::line_types, 'МНЛЗ', 'Кристаллизатор', 'Температура отходящей воды'),
        ('Электросталеплавильный цех', 'Первая'::line_types, 'МНЛЗ', 'Кристаллизатор', 'Уровень металла'),
        ('Электросталеплавильный цех', 'Вторая'::line_types, 'ДСП', 'Трансформатор', 'Мощность')
),
-- №5: Вставить Параметры
resolved_parameter_links AS (
    SELECT DISTINCT
        iact.actuator_id,
        pt.parameter_type_id
    FROM actuator_parameters_data apd
    JOIN shop_ids s ON s.shop_name = apd.shop_name
    JOIN inserted_lines il ON il.shop_id = s.shop_id AND il.line_type = apd.line_enum
    JOIN agg_type_ids agt ON agt.aggregate_type_name = apd.agg_type_name
    JOIN inserted_aggregates iagg ON iagg.line_id = il.line_id AND iagg.aggregate_type_id = agt.aggregate_type_id
    JOIN act_type_ids actt ON actt.actuator_type_name = apd.act_type_name
    JOIN inserted_actuators iact ON iact.aggregate_id = iagg.aggregate_id AND iact.actuator_type_id = actt.actuator_type_id
    JOIN param_type_ids pt ON pt.parameter_type_name = apd.param_type_name
)
-- Финальная вставка в таблицу parameters
INSERT INTO parameters (actuator_id, parameter_type_id)
SELECT actuator_id, parameter_type_id FROM resolved_parameter_links
ON CONFLICT (actuator_id, parameter_type_id) DO NOTHING;

-- ======================== КОНЕЦ СКРИПТА =================================

/*
    = = = = = = = = = = = =
        Roles & Grants       
    = = = = = = = = = = = =
*/


CREATE ROLE app_user WITH LOGIN PASSWORD 'very_strong_password';
GRANT CONNECT ON DATABASE "Ural_Steel" TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user;
GRANT SELECT ON TABLE
    shops, aggregate_types, actuator_types, parameter_types, job_titles,
    lines, aggregates, actuators, parameters,
    parameter_data
TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE
    users, user_settings, monitoring_rules, alerts
TO app_user;

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = = = = = = = = = =
        Comments on Schema Objects
    = = = = = = = = = = = = = = = = =
*/


-- Типы данных (перечисления / ENUM)
COMMENT ON TYPE alarm_types IS 'Перечисление возможных типов оповещений для пользователя.';
COMMENT ON TYPE line_types IS 'Перечисление типов (или номеров) производственных линий.';


-- Таблицы-справочники
COMMENT ON TABLE aggregate_types IS 'Справочник типов агрегатов (например, "Агломашина", "Окомкователь").';
    COMMENT ON COLUMN aggregate_types.aggregate_type_id IS 'Уникальный идентификатор типа агрегата.';
    COMMENT ON COLUMN aggregate_types.aggregate_type_name IS 'Наименование типа агрегата.';

COMMENT ON TABLE actuator_types IS 'Справочник типов исполнительных механизмов (например, "Эл.двигатель", "Редуктор").';
    COMMENT ON COLUMN actuator_types.actuator_type_id IS 'Уникальный идентификатор типа актуатора.';
    COMMENT ON COLUMN actuator_types.actuator_type_name IS 'Наименование типа актуатора.';

COMMENT ON TABLE parameter_types IS 'Справочник типов измеряемых параметров оборудования с их единицами измерения.';
    COMMENT ON COLUMN parameter_types.parameter_type_id IS 'Уникальный идентификатор типа параметра.';
    COMMENT ON COLUMN parameter_types.parameter_type_name IS 'Наименование типа параметра (например, "Электрический ток").';
    COMMENT ON COLUMN parameter_types.parameter_unit IS 'Единица измерения параметра (например, "А", "℃").';

COMMENT ON TABLE job_titles IS 'Справочник должностей пользователей системы.';
    COMMENT ON COLUMN job_titles.job_title_id IS 'Уникальный идентификатор должности.';
    COMMENT ON COLUMN job_titles.job_title_name IS 'Наименование должности.';


-- Таблицы иерархии оборудования
COMMENT ON TABLE shops IS 'Таблица цехов предприятия. Выступает как справочник цехов. [Уровень 1 иерархии].';
    COMMENT ON COLUMN shops.shop_id IS 'Уникальный идентификатор цеха.';
    COMMENT ON COLUMN shops.shop_name IS 'Наименование цеха (уникальное).';

COMMENT ON TABLE lines IS 'Таблица производственных линий внутри цехов. [Уровень 2 иерархии].';
    COMMENT ON COLUMN lines.line_id IS 'Уникальный идентификатор линии.';
    COMMENT ON COLUMN lines.shop_id IS 'Внешний ключ на цех (shops.shop_id).';
    COMMENT ON COLUMN lines.line_type IS 'Тип (номер) линии из перечисления line_types.';
    COMMENT ON CONSTRAINT uq_lines_shop_id_line_type ON lines IS 'Гарантирует уникальность типа линии в пределах одного цеха.';

COMMENT ON TABLE aggregates IS 'Таблица агрегатов (экземпляров оборудования) на производственных линиях. [Уровень 3 иерархии].';
    COMMENT ON COLUMN aggregates.aggregate_id IS 'Уникальный идентификатор агрегата.';
    COMMENT ON COLUMN aggregates.line_id IS 'Внешний ключ на линию (lines.line_id).';
    COMMENT ON COLUMN aggregates.aggregate_type_id IS 'Внешний ключ на тип агрегата (aggregate_types.aggregate_type_id).';
    COMMENT ON CONSTRAINT uq_aggregates_line_id_aggregate_type_id ON aggregates IS 'Гарантирует уникальность типа агрегата в пределах одной линии.';

COMMENT ON TABLE actuators IS 'Таблица актуаторов (экземпляров исполнительных механизмов) внутри агрегатов. [Уровень 4 иерархии].';
    COMMENT ON COLUMN actuators.actuator_id IS 'Уникальный идентификатор актуатора.';
    COMMENT ON COLUMN actuators.aggregate_id IS 'Внешний ключ на агрегат (aggregates.aggregate_id).';
    COMMENT ON COLUMN actuators.actuator_type_id IS 'Внешний ключ на тип актуатора (actuator_types.actuator_type_id).';


-- Таблица параметров
COMMENT ON TABLE parameters IS 'Таблица, определяющая, какие типы параметров релевантны для каких актуаторов. Связь М:М.';
    COMMENT ON COLUMN parameters.parameter_id IS 'Уникальный идентификатор конкретной связки "актуатор-тип параметра".';
    COMMENT ON COLUMN parameters.actuator_id IS 'Внешний ключ на актуатор (actuators.actuator_id).';
    COMMENT ON COLUMN parameters.parameter_type_id IS 'Внешний ключ на тип параметра (parameter_types.parameter_type_id).';
    COMMENT ON CONSTRAINT uq_parameters_actuator_id_parameter_type_id ON parameters IS 'Гарантирует, что один тип параметра может быть связан с одним актуатором только один раз.';


-- Таблица данных параметров
COMMENT ON TABLE parameter_data IS 'Гипертаблица (TimescaleDB) для хранения временных рядов: значений параметров в определённое время.';
    COMMENT ON COLUMN parameter_data.parameter_data_id IS 'Уникальный идентификатор записи данных (генерируется автоматически).';
    COMMENT ON COLUMN parameter_data.parameter_id IS 'Внешний ключ на parameters.parameter_id. Часть первичного ключа гипертаблицы.';
    COMMENT ON COLUMN parameter_data.parameter_value IS 'Измеренное значение параметра.';
    COMMENT ON COLUMN parameter_data.data_timestamp IS 'Временная метка измерения. Часть первичного ключа гипертаблицы и ключ партиционирования.';


-- Таблица пользователей
COMMENT ON TABLE users IS 'Таблица пользователей системы мониторинга.';
    COMMENT ON COLUMN users.user_id IS 'Уникальный идентификатор пользователя.';
    COMMENT ON COLUMN users.job_title_id IS 'Внешний ключ на должность пользователя (job_titles.job_title_id). Может быть NULL.';
    COMMENT ON COLUMN users.first_name IS 'Имя пользователя.';
    COMMENT ON COLUMN users.last_name IS 'Фамилия пользователя.';
    COMMENT ON COLUMN users.middle_name IS 'Отчество пользователя (может отсутствовать).';
    COMMENT ON COLUMN users.email IS 'Электронная почта пользователя (уникальная).';
    COMMENT ON COLUMN users.phone IS 'Номер телефона пользователя (уникальный, формат +XXXXXXXXXXX).';
    COMMENT ON COLUMN users.password_hash IS 'Хеш пароля пользователя (используется pgcrypto).';
    COMMENT ON COLUMN users.created_at IS 'Временная метка создания учетной записи пользователя.';


-- Таблица настроек пользователей
COMMENT ON TABLE user_settings IS 'Таблица персональных настроек пользователя.';
    COMMENT ON COLUMN user_settings.user_id IS 'Уникальный идентификатор пользователя (одновременно первичный и внешний ключ на users.user_id).';
    COMMENT ON COLUMN user_settings.theme IS 'Выбранная тема интерфейса ("light" или "dark").';
    COMMENT ON COLUMN user_settings.language IS 'Выбранный язык интерфейса ("ru" или "en").';
    COMMENT ON COLUMN user_settings.alarm_types IS 'Массив выбранных пользователем типов оповещений (из ENUM alarm_types).';
    COMMENT ON COLUMN user_settings.is_rules_public IS 'Флаг, указывающий, являются ли правила пользователя публичными.';


-- Таблица правил
COMMENT ON TABLE monitoring_rules IS 'Таблица правил мониторинга, созданных пользователями для параметров.';
    COMMENT ON COLUMN monitoring_rules.rule_id IS 'Уникальный идентификатор правила.';
    COMMENT ON COLUMN monitoring_rules.user_id IS 'Внешний ключ на пользователя, создавшего правило (users.user_id).';
    COMMENT ON COLUMN monitoring_rules.parameter_id IS 'Внешний ключ на параметр (связку "актуатор-тип параметра"), для которого создано правило (parameters.parameter_id).';
    COMMENT ON COLUMN monitoring_rules.rule_name IS 'Необязательное пользовательское название правила.';
    COMMENT ON COLUMN monitoring_rules.comparison_operator IS 'Оператор сравнения (">", "<", "=", ">=", "<=").';
    COMMENT ON COLUMN monitoring_rules.threshold IS 'Пороговое значение для срабатывания правила.';
    COMMENT ON COLUMN monitoring_rules.is_active IS 'Флаг активности правила (включено/выключено).';
    COMMENT ON COLUMN monitoring_rules.created_at IS 'Временная метка создания правила.';


-- Таблица тревог
COMMENT ON TABLE alerts IS 'Таблица журнала тревог (сработавших правил мониторинга).';
    COMMENT ON COLUMN alerts.alert_id IS 'Уникальный идентификатор тревоги.';
    COMMENT ON COLUMN alerts.rule_id IS 'Внешний ключ на правило, которое сработало (monitoring_rules.rule_id).';
    COMMENT ON COLUMN alerts.parameter_data_id IS 'Идентификатор строки в таблице parameter_data (parameter_data.data_id), которая (предположительно) вызвала срабатывание правила.';
    COMMENT ON COLUMN alerts.alert_message IS 'Текстовое сообщение тревоги (может генерироваться автоматически или быть частью правила).';
    COMMENT ON COLUMN alerts.is_read IS 'Флаг, указывающий, прочитана ли тревога пользователем.';
    COMMENT ON COLUMN alerts.alert_timestamp IS 'Временная метка срабатывания тревоги (генерации записи).';

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = = = = =
        SELECT queries
    = = = = = = = = = = = =
*/


-- Полный список всех сущностей конкретного цеха с путями
SELECT
    s.shop_name AS "Цех",
    l.line_type AS "Линия (Тип)",
    agt.aggregate_type_name AS "Агрегат (Тип)",
    actt.actuator_type_name AS "Актуатор (Тип)",
    p.parameter_id AS "ID Параметра",
    pt.parameter_type_name AS "Параметр (Тип)",
    pt.parameter_unit AS "Ед. изм."
FROM shops s
LEFT JOIN lines l ON s.shop_id = l.shop_id
LEFT JOIN aggregates agg ON l.line_id = agg.line_id
LEFT JOIN aggregate_types agt ON agg.aggregate_type_id = agt.aggregate_type_id
LEFT JOIN actuators act ON agg.aggregate_id = act.aggregate_id
LEFT JOIN actuator_types actt ON act.actuator_type_id = actt.actuator_type_id
LEFT JOIN parameters p ON act.actuator_id = p.actuator_id
LEFT JOIN parameter_types pt ON p.parameter_type_id = pt.parameter_type_id
WHERE s.shop_name = 'Агломерационный цех' -- Нужный цех
ORDER BY
    s.shop_name,
    l.line_type,
    agt.aggregate_type_name,
    actt.actuator_type_name,
    pt.parameter_type_name;


-- Иерархия с количеством объектов
SELECT
    s.shop_name AS "Цех",
    l.line_type::text AS "Линия",
    COUNT(DISTINCT agg.aggregate_id) AS "Кол-во агрегатов",
    COUNT(DISTINCT act.actuator_id) AS "Кол-во актуаторов",
    COUNT(DISTINCT p.parameter_id) AS "Кол-во параметров"
FROM
    shops s
JOIN
    lines l ON s.shop_id = l.shop_id
JOIN
    aggregates agg ON l.line_id = agg.line_id
JOIN
    actuators act ON agg.aggregate_id = act.aggregate_id
JOIN
    parameters p ON act.actuator_id = p.actuator_id
GROUP BY
    s.shop_name, l.line_type
ORDER BY
    s.shop_name, l.line_type;


-- Конец файла
SELECT 'Формирование базы данных окончено.'