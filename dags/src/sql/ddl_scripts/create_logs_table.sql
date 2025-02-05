-- Создание схемы logs и таблиц для логирования слоев

CREATE SCHEMA IF NOT EXISTS logs;

CREATE TABLE IF NOT EXISTS logs.logs_ds (
    log_level VARCHAR(10) DEFAULT 'INFO' NOT NULL,
    log_date TIMESTAMP DEFAULT NOW() NOT NULL,
    log_message TEXT
);

CREATE TABLE IF NOT EXISTS logs.logs_dm (
    log_level VARCHAR(10) DEFAULT 'INFO' NOT NULL,
    log_date TIMESTAMP DEFAULT NOW() NOT NULL,
    log_message TEXT
);

CREATE TABLE IF NOT EXISTS logs.logs_export (
    log_level VARCHAR(10) DEFAULT 'INFO' NOT NULL,
    log_date TIMESTAMP DEFAULT NOW() NOT NULL,
    log_message TEXT
);