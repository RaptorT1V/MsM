/*
   Что нужно создать:
     - Индексы (какие? куда?)
     - Валидация данных (e-mail; номер телефона | ещё что?)
     - ? ? ? 
     - Триггеры, функции, ограничения
   
   Вопрос: "что делать с массивом в настройках пользователя?"

   Ввести иерархические должности с различными правами:
     - Директор (самый главный дядя; не разбирается ни в чём, кроме как в заработке денег; занимает верхушку пищевой цепи)
     - Главный аналитик (видит все цеха)
     - Начальник аглоцеха (видит только свой *агломерационный* цех)
     - Аналитик 1-ой линии аглоцеха (видит только свою *первую* линию)
*/

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = =
        DROPs
    = = = = = = =
*/

DROP TYPE IF EXISTS node_types CASCADE;
DROP TYPE IF EXISTS alarm_types CASCADE;

DROP TABLE IF EXISTS parameter_types CASCADE;
DROP TABLE IF EXISTS job_titles CASCADE;
DROP TABLE IF EXISTS nodes CASCADE;
DROP TABLE IF EXISTS parameters CASCADE;
DROP TABLE IF EXISTS parameter_data CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS user_settings CASCADE;
DROP TABLE IF EXISTS monitoring_rules CASCADE;
DROP TABLE IF EXISTS alerts CASCADE;

-- DROP FUNCTION EXAM_FUNC IF EXISTS CASCADE;

-- DROP TRIGGER EXAM_TRIG IF EXISTS ON EXAM_FUNC;     

DROP EXTENSION IF EXISTS timescaledb;
DROP EXTENSION IF EXISTS pgcrypto;

/*
    = = = = = = = = = =
        Extensions
    = = = = = = = = = =
*/

CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = = = =
        ENUMs & DICTs    
    = = = = = = = = = = =
*/

-- П. node_types определяет уровни иерархии оборудования комбината: ['цех' → 'линия' → 'агрегат' → 'исполняющий механизм (узел/привод)']
CREATE TYPE node_types AS ENUM ('Shop', 'Line', 'Aggregate', 'Actuator');


-- П. alarm_types предназначено для хранения типов тревог
CREATE TYPE alarm_types AS ENUM ('siren', 'flash', 'vibration', 'notification');


-- Т. parameter_types содержит справочник типов параметров с единицами измерения (например, электрический ток [A]).
CREATE TABLE parameter_types (
    parameter_type_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    parameter_type_name VARCHAR(65) NOT NULL UNIQUE,
    parameter_unit VARCHAR(30)
);


-- Т. job_titles содержит справочник типов должностей
CREATE TABLE job_titles (
    job_title_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    job_title_name VARCHAR(80) NOT NULL UNIQUE
);

/*
    = = = = = = = =
        Tables
    = = = = = = = =
*/

-- Т. nodes содержит иерархическую структуру оборудования (цеха, линии, агрегаты, исполняющие механизмы (узлы/приводы)) с помощью рекурсивной модели
CREATE TABLE nodes (
    node_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    node_parent_id INT,
    node_name VARCHAR(70) NOT NULL,
    node_type node_types NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_nodes_nodes_parent FOREIGN KEY (node_parent_id) REFERENCES Nodes(node_id) ON DELETE SET NULL,
    CONSTRAINT check_parent_self CHECK (node_id <> node_parent_id) -- Запрет самоссылки
);


-- Т. parameters связывает типы параметров с исполняющими механизмами (узлами/приводами).
CREATE TABLE parameters (
    parameter_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    node_id INT NOT NULL,
    parameter_type_id INT NOT NULL,
    
    CONSTRAINT fk_parameters_nodes FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
    CONSTRAINT fk_parameters_parameter_types FOREIGN KEY (parameter_type_id) REFERENCES parameter_types(parameter_type_id) ON DELETE RESTRICT
);


-- Т. parameter_data содержит значения параметров, измеренных датчиками в определённое время (временные ряды данных). *ОДНА ИЗ КЛЮЧЕВЫХ*
CREATE TABLE parameter_data (
    data_id BIGINT GENERATED ALWAYS AS IDENTITY,
    parameter_id INT NOT NULL,
    parameter_value FLOAT8 NOT NULL,
    data_timestamp TIMESTAMPTZ NOT NULL, -- Добавлять ли "DEFAULT CURRENT_TIMESTAMP" ? Это зависит от того, кто задаёт время при отправке данных: БД или датчики.
    
    CONSTRAINT pk_parameter_data PRIMARY KEY (data_id, data_timestamp),
    CONSTRAINT fk_parameter_data_parameters FOREIGN KEY (parameter_id) REFERENCES parameters(parameter_id) ON DELETE CASCADE
);


-- Т. users содержит информацию о пользователях
CREATE TABLE users (
    user_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    job_titles_id INT,
    first_name VARCHAR(26) NOT NULL,
    last_name VARCHAR(36) NOT NULL,
    middle_name VARCHAR(24),
    email VARCHAR(60) NOT NULL UNIQUE,
    phone CHAR(12) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_users_job_titles FOREIGN KEY (job_titles_id) REFERENCES job_titles(job_title_id) ON DELETE SET NULL
);


-- Т. user_settings содержит настройки пользователей
CREATE TABLE user_settings (
    user_id INT PRIMARY KEY,
    theme VARCHAR(10) CHECK (theme IN ('light', 'dark')) DEFAULT 'light',
    language VARCHAR(5) CHECK (language IN ('ru', 'en')) DEFAULT 'ru',
    alarm_types alarm_types[] DEFAULT '{notification}',
    is_rules_public BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_user_settings_users FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


-- Т. monitoring_rules содержит правила мониторинга (условия для параметров)
CREATE TABLE monitoring_rules (
    rule_id INT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id INT NOT NULL,
    parameter_id INT NOT NULL,
    rule_name VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    comparison_operator VARCHAR(2) CHECK (comparison_operator IN ('>', '<', '=', '>=', '<=')) NOT NULL,
    threshold FLOAT8 NOT NULL, -- Порог срабатывания
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_monitoring_rules_users FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_monitoring_rules_parameters FOREIGN KEY (parameter_id) REFERENCES parameters(parameter_id) ON DELETE CASCADE
);


-- Таблица alerts содержит журнал тревог (срабатывания правил)
CREATE TABLE alerts (
    alert_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    rule_id INT NOT NULL,
    parameter_data_id BIGINT NOT NULL,
    alert_timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    alert_message TEXT,
    is_read BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_alerts_monitoring_rules FOREIGN KEY (rule_id) REFERENCES monitoring_rules(rule_id) ON DELETE CASCADE
    -- CONSTRAINT fk_alerts_parameter_data FOREIGN KEY (parameter_data_id) REFERENCES parameter_data(data_id) ON DELETE CASCADE -- Убрано, т.к. TimeScaleDB не будет работать + можно через запросы "обойти" и "эмулировать" внешний ключ
);

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = = =
        Constraints
    = = = = = = = = = =
*/

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = =
        Functions    
    = = = = = = = = =
*/


/*
    = = = = = = = = =
        Triggers    
    = = = = = = = = =
*/

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = =
        Indexes    
    = = = = = = = =
*/



/*
    = = = = = = = = = =
        TimeScaleDb
    = = = = = = = = = =
*/

  -- Преобразуем parameter_data в гипертаблицу TimescaleDB
SELECT create_hypertable('parameter_data', 'data_timestamp');

  -- Настраиваем сжатие данных старше 1 месяца
ALTER TABLE parameter_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'parameter_id'
);
SELECT add_compression_policy('parameter_data', INTERVAL '1 month');

  -- (Опционально) Настраиваем удаление данных старше 3 месяцев
-- SELECT add_retention_policy('ParameterData', INTERVAL '3 months');

/*  Обход отсутствия FOREIGN KEY в Alerts
SELECT 
    a.alert_id,
    a.alert_timestamp,
    pd.parameter_value,
    pd.data_timestamp,
    p.parameter_type_id,
    pt.parameter_type_name
FROM 
    alerts a
JOIN 
    monitoring_rules mr ON a.rule_id = mr.rule_id
JOIN 
    parameter_data pd ON mr.parameter_id = pd.parameter_id
    AND pd.data_timestamp BETWEEN a.alert_timestamp - INTERVAL '5 seconds' AND a.alert_timestamp + INTERVAL '5 seconds'
JOIN 
    parameters p ON pd.parameter_id = p.parameter_id
JOIN 
    parameter_types pt ON p.parameter_type_id = pt.parameter_type_id;
*/

-- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

/*
    = = = = = = = = = = = =
        INSERT queries
    = = = = = = = = = = = =
*/

-- Заполнение таблицы job_titles
INSERT INTO job_titles (job_title_name) VALUES
-- Производственные должности
('Оператор прокатного стана'),
('Оператор МНЛЗ'),

-- IT и автоматизация
('Инженер-программист АСУ ТП'),
('Специалист по кибербезопасности промышленных систем'),

-- Инженерно-технический персонал
('Инженер-технолог'),
('Специалист по цифровому моделированию процессов'),

-- Управленческие должности
('Начальник аглоцеха'),
('Руководитель проектов по автоматизации'),
('Руководитель службы технического контроля'),

-- Обслуживающий персонал
('Наладчик автоматизированного оборудования'),
('Техник по обслуживанию КИПиА'),
('Специалист по калибровке измерительных систем'),
('Сервисный инженер по промышленному оборудованию'),

-- Вспомогательные службы
('Специалист по промышленной безопасности'),

-- Лаборатория
('Инженер-исследователь');


-- Заполнение таблицы parameter_types
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


--------------------------------------------------------------------------------
-- Скрипт для заполнения таблицы 'nodes' иерархическими данными о структуре металлургического комбината (Цеха -> Линии -> Агрегаты -> Узлы).
-- Используется подход с CTE (Common Table Expressions) и RETURNING для атомарной вставки и получения ID родительских узлов в PostgreSQL.
--------------------------------------------------------------------------------

WITH
-- ==== Уровень 1: Цехи (Shops) ====

  -- Вставка цеха 'Аглоцех' и получение его ID
  shop1 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    VALUES (NULL, 'Аглоцех', 'Shop')
    RETURNING node_id, node_name
  ),

  -- Вставка цеха 'ЭСПЦ' и получение его ID
  shop2 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    VALUES (NULL, 'ЭСПЦ', 'Shop')
    RETURNING node_id, node_name
  ),

-- ==== Уровень 2: Линии (Lines) ====

  -- Вставка линий для 'Аглоцех' (используя ID из shop1)
  lines_shop1 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    SELECT node_id, 'Линия 1', 'Line'::node_types FROM shop1 WHERE node_name = 'Аглоцех'
    UNION ALL
    SELECT node_id, 'Линия 2', 'Line'::node_types FROM shop1 WHERE node_name = 'Аглоцех'
    RETURNING node_id, node_name, node_parent_id
  ),

  -- Вставка линий для 'ЭСПЦ' (используя ID из shop2)
  lines_shop2 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    SELECT node_id, 'Линия 1', 'Line'::node_types FROM shop2 WHERE node_name = 'ЭСПЦ'
    UNION ALL
    SELECT node_id, 'Линия 2', 'Line'::node_types FROM shop2 WHERE node_name = 'ЭСПЦ'
    RETURNING node_id, node_name, node_parent_id
  ),

-- ==== Уровень 3: Агрегаты (Aggregates) ====

  -- Вставка агрегатов для 'Аглоцех' -> 'Линия 1'
  aggr_line1_1 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    SELECT node_id, 'Окомкователь', 'Aggregate'::node_types FROM lines_shop1 WHERE node_name = 'Линия 1' AND node_parent_id = (SELECT node_id FROM shop1 WHERE node_name = 'Аглоцех')
    UNION ALL
    SELECT node_id, 'Конвейер', 'Aggregate'::node_types FROM lines_shop1 WHERE node_name = 'Линия 1' AND node_parent_id = (SELECT node_id FROM shop1 WHERE node_name = 'Аглоцех')
    UNION ALL
    SELECT node_id, 'Агломашина', 'Aggregate'::node_types FROM lines_shop1 WHERE node_name = 'Линия 1' AND node_parent_id = (SELECT node_id FROM shop1 WHERE node_name = 'Аглоцех')
    UNION ALL
    SELECT node_id, 'Эксгаустер', 'Aggregate'::node_types FROM lines_shop1 WHERE node_name = 'Линия 1' AND node_parent_id = (SELECT node_id FROM shop1 WHERE node_name = 'Аглоцех')
    RETURNING node_id, node_name, node_parent_id
  ),

  -- Вставка агрегатов для 'Аглоцех' -> 'Линия 2'
  aggr_line1_2 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    SELECT node_id, 'Агломашина', 'Aggregate'::node_types FROM lines_shop1 WHERE node_name = 'Линия 2' AND node_parent_id = (SELECT node_id FROM shop1 WHERE node_name = 'Аглоцех')
    UNION ALL
    SELECT node_id, 'Эксгаустер', 'Aggregate'::node_types FROM lines_shop1 WHERE node_name = 'Линия 2' AND node_parent_id = (SELECT node_id FROM shop1 WHERE node_name = 'Аглоцех')
    RETURNING node_id, node_name, node_parent_id
  ),

  -- Вставка агрегатов для 'ЭСПЦ' -> 'Линия 1'
  aggr_line2_1 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    SELECT node_id, 'МНЛЗ', 'Aggregate'::node_types FROM lines_shop2 WHERE node_name = 'Линия 1' AND node_parent_id = (SELECT node_id FROM shop2 WHERE node_name = 'ЭСПЦ')
    RETURNING node_id, node_name, node_parent_id
  ),

  -- Вставка агрегатов для 'ЭСПЦ' -> 'Линия 2'
  aggr_line2_2 AS (
    INSERT INTO nodes (node_parent_id, node_name, node_type)
    SELECT node_id, 'ДСП', 'Aggregate'::node_types FROM lines_shop2 WHERE node_name = 'Линия 2' AND node_parent_id = (SELECT node_id FROM shop2 WHERE node_name = 'ЭСПЦ')
    RETURNING node_id, node_name, node_parent_id
  )

-- ==== Уровень 4: Исполняющие механизмы (Actuators) ====

-- Финальная вставка актуаторов, ссылаясь на ID агрегатов из всех CTE уровня 3 ('aggr_*')
INSERT INTO nodes (node_parent_id, node_name, node_type)

  -- Актуаторы для 'Окомкователь' (Аглоцех -> Линия 1)
  SELECT node_id, 'Эл.двигатель переменного тока (3ф)', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Окомкователь'
  UNION ALL
  SELECT node_id, 'Редуктор', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Окомкователь'
  UNION ALL

  -- Актуаторы для 'Конвейер' (Аглоцех -> Линия 1)
  SELECT node_id, 'Эл.двигатель постоянного тока', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Конвейер'
  UNION ALL

  -- Актуаторы для 'Агломашина' (Аглоцех -> Линия 1)
  SELECT node_id, 'Эл.двигатель постоянного тока', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Агломашина'
  UNION ALL
  SELECT node_id, 'Редуктор', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Агломашина'
  UNION ALL
  SELECT node_id, 'Лента', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Агломашина'
  UNION ALL

  -- Актуаторы для 'Эксгаустер' (Аглоцех -> Линия 1)
  SELECT node_id, 'Эл.двигатель постоянного тока', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Эксгаустер'
  UNION ALL
  SELECT node_id, 'Нагнетатель', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Эксгаустер'
  UNION ALL
  SELECT node_id, 'Система смазки', 'Actuator'::node_types FROM aggr_line1_1 WHERE node_name = 'Эксгаустер'
  UNION ALL

  -- Актуаторы для 'Агломашина' (Аглоцех -> Линия 2)
  SELECT node_id, 'Эл.двигатель постоянного тока', 'Actuator'::node_types FROM aggr_line1_2 WHERE node_name = 'Агломашина'
  UNION ALL
  SELECT node_id, 'Редуктор', 'Actuator'::node_types FROM aggr_line1_2 WHERE node_name = 'Агломашина'
  UNION ALL
  SELECT node_id, 'Лента', 'Actuator'::node_types FROM aggr_line1_2 WHERE node_name = 'Агломашина'
  UNION ALL

  -- Актуаторы для 'Эксгаустер' (Аглоцех -> Линия 2)
  SELECT node_id, 'Эл.двигатель постоянного тока', 'Actuator'::node_types FROM aggr_line1_2 WHERE node_name = 'Эксгаустер'
  UNION ALL
  SELECT node_id, 'Нагнетатель', 'Actuator'::node_types FROM aggr_line1_2 WHERE node_name = 'Эксгаустер'
  UNION ALL
  SELECT node_id, 'Система смазки', 'Actuator'::node_types FROM aggr_line1_2 WHERE node_name = 'Эксгаустер'
  UNION ALL
  -- - - - - - - - - - - - - - - - - - - - - - -
  -- Актуаторы для 'МНЛЗ' (ЭСПЦ -> Линия 1)
  SELECT node_id, 'Кристаллизатор', 'Actuator'::node_types FROM aggr_line2_1 WHERE node_name = 'МНЛЗ'
  UNION ALL

  -- Актуаторы для 'ДСП' (ЭСПЦ -> Линия 2)
  SELECT node_id, 'Трансформатор', 'Actuator'::node_types FROM aggr_line2_2 WHERE node_name = 'ДСП';

-- Конец скрипта


-----------------------------------------------
 -- Скрипт для заполнения таблицы 'parameters'
-----------------------------------------------
WITH actuator_parameters(shop_name, line_name, aggregate_name, actuator_name, parameter_name) AS (
    VALUES
    -- | Агломерационный цех |
            -- ---------- (Линия 1, Аглоцех) ----------
        -- Окомкователь
        ('Аглоцех', 'Линия 1', 'Окомкователь', 'Эл.двигатель переменного тока (3ф)', 'Электрический ток'),
        ('Аглоцех', 'Линия 1', 'Окомкователь', 'Эл.двигатель переменного тока (3ф)', 'Температура обмотки'),
        ('Аглоцех', 'Линия 1', 'Окомкователь', 'Редуктор', 'Температура масла'),
        ('Аглоцех', 'Линия 1', 'Окомкователь', 'Редуктор', 'Уровень масла'),
        
        -- Конвейер
        ('Аглоцех', 'Линия 1', 'Конвейер', 'Эл.двигатель постоянного тока', 'Электрический ток'),
        ('Аглоцех', 'Линия 1', 'Конвейер', 'Эл.двигатель постоянного тока', 'Температура сердечника статора'),
        
        -- Агломашина
        ('Аглоцех', 'Линия 1', 'Агломашина', 'Эл.двигатель постоянного тока', 'Электрический ток'),
        ('Аглоцех', 'Линия 1', 'Агломашина', 'Эл.двигатель постоянного тока', 'Температура сердечника индуктора'),
        ('Аглоцех', 'Линия 1', 'Агломашина', 'Редуктор', 'Температура масла'),
        ('Аглоцех', 'Линия 1', 'Агломашина', 'Редуктор', 'Уровень масла'),
        ('Аглоцех', 'Линия 1', 'Агломашина', 'Лента', 'Скорость ленты'),
        ('Аглоцех', 'Линия 1', 'Агломашина', 'Лента', 'Высота слоя'),
        ('Аглоцех', 'Линия 1', 'Агломашина', 'Лента', 'Температура шихты'),
        
        -- Эксгаустер
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Электрический ток'),
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Температура обмотки'),
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Температура опорного подшипника'),
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Вибрация опорного подшипника'),
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Нагнетатель', 'Разрежение'),
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Нагнетатель', 'Температура опорного подшипника'),
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Нагнетатель', 'Вибрация опорного подшипника'),
        ('Аглоцех', 'Линия 1', 'Эксгаустер', 'Система смазки', 'Давление масла в системе'),
            -- ---------- (Линия 2, Аглоцех) ----------
        -- Агломашина
        ('Аглоцех', 'Линия 2', 'Агломашина', 'Эл.двигатель постоянного тока', 'Электрический ток'),
        ('Аглоцех', 'Линия 2', 'Агломашина', 'Эл.двигатель постоянного тока', 'Температура сердечника индуктора'),
        ('Аглоцех', 'Линия 2', 'Агломашина', 'Редуктор', 'Температура масла'),
        ('Аглоцех', 'Линия 2', 'Агломашина', 'Редуктор', 'Уровень масла'),
        ('Аглоцех', 'Линия 2', 'Агломашина', 'Лента', 'Скорость ленты'),
        ('Аглоцех', 'Линия 2', 'Агломашина', 'Лента', 'Высота слоя'),
        ('Аглоцех', 'Линия 2', 'Агломашина', 'Лента', 'Температура шихты'),
        
        -- Эксгаустер
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Электрический ток'),
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Температура обмотки'),
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Температура опорного подшипника'),
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Эл.двигатель постоянного тока', 'Вибрация опорного подшипника'),
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Нагнетатель', 'Разрежение'),
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Нагнетатель', 'Температура опорного подшипника'),
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Нагнетатель', 'Вибрация опорного подшипника'),
        ('Аглоцех', 'Линия 2', 'Эксгаустер', 'Система смазки', 'Давление масла в системе'),

    -- | Электросталеплавильный цех |
            -- ---------- (Линия 1, ЭСПЦ) ----------        
        -- МНЛЗ
        ('ЭСПЦ', 'Линия 1', 'МНЛЗ', 'Кристаллизатор', 'Температура входящей воды'),
        ('ЭСПЦ', 'Линия 1', 'МНЛЗ', 'Кристаллизатор', 'Температура отходящей воды'),
        ('ЭСПЦ', 'Линия 1', 'МНЛЗ', 'Кристаллизатор', 'Уровень металла'),
            -- ---------- (Линия 2, ЭСПЦ) ----------        
        -- ДСП
        ('ЭСПЦ', 'Линия 2', 'ДСП', 'Трансформатор', 'Мощность')
),

resolved_ids AS (
    SELECT 
        a.node_id AS actuator_id,
        pt.parameter_type_id
    FROM actuator_parameters ap
    JOIN nodes shop ON shop.node_name = ap.shop_name AND shop.node_type = 'Shop'
    JOIN nodes line ON line.node_name = ap.line_name AND line.node_type = 'Line' AND line.node_parent_id = shop.node_id
    JOIN nodes agg ON agg.node_name = ap.aggregate_name AND agg.node_type = 'Aggregate' AND agg.node_parent_id = line.node_id
    JOIN nodes a ON a.node_name = ap.actuator_name AND a.node_type = 'Actuator' AND a.node_parent_id = agg.node_id
    JOIN parameter_types pt ON pt.parameter_type_name = ap.parameter_name
)

INSERT INTO parameters (node_id, parameter_type_id)
SELECT actuator_id, parameter_type_id FROM resolved_ids;

/*
    = = = = = = = = = = = =
        SELECT queries       
    = = = = = = = = = = = =
*/

-- Иерархия (каждый параметр в отдельной строке)
SELECT 
    s.node_name AS "Цех",
    l.node_name AS "Линия",
    a.node_name AS "Агрегат",
    act.node_name AS "Исполняющий механизм",
    pt.parameter_type_name AS "Параметр",
    pt.parameter_unit AS "Ед. измерения"
FROM 
    nodes act
JOIN 
    nodes a ON act.node_parent_id = a.node_id
JOIN 
    nodes l ON a.node_parent_id = l.node_id
JOIN 
    nodes s ON l.node_parent_id = s.node_id
JOIN 
    parameters p ON act.node_id = p.node_id
JOIN 
    parameter_types pt ON p.parameter_type_id = pt.parameter_type_id
WHERE 
    act.node_type = 'Actuator'
ORDER BY 
    s.node_name, 
    l.node_name, 
    a.node_name, 
    act.node_name,
    pt.parameter_type_name;


-- Иерархия (все параметры в одну строку)
SELECT 
    s.node_name AS "Цех",
    l.node_name AS "Линия",
    a.node_name AS "Агрегат",
    act.node_name AS "Исполняющий механизм",
    STRING_AGG(pt.parameter_type_name || ' (' || pt.parameter_unit || ')', ', ' ORDER BY pt.parameter_type_name) AS "Параметры"
FROM 
    nodes act
JOIN 
    nodes a ON act.node_parent_id = a.node_id
JOIN 
    nodes l ON a.node_parent_id = l.node_id
JOIN 
    nodes s ON l.node_parent_id = s.node_id
JOIN 
    parameters p ON act.node_id = p.node_id
JOIN 
    parameter_types pt ON p.parameter_type_id = pt.parameter_type_id
WHERE 
    act.node_type = 'Actuator'
GROUP BY
    s.node_name, 
    l.node_name, 
    a.node_name, 
    act.node_name
ORDER BY 
    s.node_name, 
    l.node_name, 
    a.node_name, 
    act.node_name;