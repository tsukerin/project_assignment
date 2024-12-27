from airflow import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

import pandas as pd
from datetime import datetime
import time

# from src.utils.logging import *
# from src.utils.functions import *

def dummy_load(seconds):
    time.sleep(seconds)

def log_error(table, error_message):
    postgres_hook = PostgresHook('local-postgres')
    engine = postgres_hook.get_sqlalchemy_engine()

    query = f"""
    INSERT INTO "LOGS".LOGGING (log_level, log_date, log_message) 
    VALUES ('ERROR', '{datetime.now()}', 'Произошла ошибка в таблице {table}: {error_message}')
    """
    with engine.connect() as conn:
        conn.execute(query)

def log_notify(type, log_message):
    postgres_hook = PostgresHook('local-postgres')
    engine = postgres_hook.get_sqlalchemy_engine()

    query = f"""
    INSERT INTO "LOGS".LOGGING (log_level, log_date, log_message) 
    VALUES ('{type}', '{datetime.now()}', '{log_message}')
    """
    with engine.connect() as conn:
        conn.execute(query)

def insert_into_ft_balance_f():
    try:
        df = pd.read_csv(f'/src/files/ft_balance_f.csv', sep=';', encoding_errors='replace')

        postgres_hook = PostgresHook('local-postgres')
        engine = postgres_hook.get_sqlalchemy_engine()

        with engine.connect() as conn:
            conn.execute(
                """
                CREATE TEMP TABLE "TEMP_FT_BALANCE_F" AS
                SELECT * FROM "DS"."FT_BALANCE_F";
                """)

            df.to_sql('TEMP_FT_BALANCE_F', conn, if_exists='append', index=False)

            
            conn.execute(
                """
                MERGE INTO "DS"."FT_BALANCE_F" AS target
                USING "TEMP_FT_BALANCE_F" AS source
                ON target."ON_DATE" = source."ON_DATE" AND target."ACCOUNT_RK" = source."ACCOUNT_RK"
                WHEN MATCHED THEN
                    UPDATE SET 
                        "CURRENCY_RK" = source."CURRENCY_RK",
                        "BALANCE_OUT" = source."BALANCE_OUT"
                WHEN NOT MATCHED THEN
                    INSERT VALUES (
                        source."ON_DATE", 
                        source."ACCOUNT_RK", 
                        source."CURRENCY_RK",
                        source."BALANCE_OUT"
                    );
                """)
            
            conn.execute(f'DROP TABLE "TEMP_FT_BALANCE_F";')
    except Exception as e:
        log_error('ft_balance_f', str(e))

def insert_into_ft_posting_f():
    try:
        df = pd.read_csv(f'/src/files/ft_posting_f.csv', sep=';', encoding_errors='replace')

        postgres_hook = PostgresHook('local-postgres')
        engine = postgres_hook.get_sqlalchemy_engine()

        with engine.connect() as conn:
        
            conn.execute(
                """
                TRUNCATE "DS"."FT_POSTING_F";
                """)
            
            df.to_sql('FT_POSTING_F', conn, schema='DS', if_exists='append', index=False)
    except Exception as e:
        log_error('ft_posting_f', str(e))

def insert_into_md_account_d():
    try:
        df = pd.read_csv(f'/src/files/md_account_d.csv', sep=';', encoding_errors='replace')

        postgres_hook = PostgresHook('local-postgres')
        engine = postgres_hook.get_sqlalchemy_engine()

        with engine.connect() as conn:
            conn.execute(
                """
                CREATE TEMP TABLE "TEMP_MD_ACCOUNT_D" AS
                SELECT * FROM "DS"."MD_ACCOUNT_D";
                """)

            df.to_sql('TEMP_MD_ACCOUNT_D', conn, if_exists='append', index=False)

            
            conn.execute(
                """
                MERGE INTO "DS"."MD_ACCOUNT_D" AS target
                USING "TEMP_MD_ACCOUNT_D" AS source
                ON target."DATA_ACTUAL_DATE" = source."DATA_ACTUAL_DATE" AND target."ACCOUNT_RK" = source."ACCOUNT_RK"
                WHEN MATCHED THEN
                    UPDATE SET 
                        "DATA_ACTUAL_END_DATE" = source."DATA_ACTUAL_END_DATE",
                        "ACCOUNT_NUMBER" = source."ACCOUNT_NUMBER",
                        "CHAR_TYPE" = source."CHAR_TYPE",
                        "CURRENCY_RK" = source."CURRENCY_RK",
                        "CURRENCY_CODE" = source."CURRENCY_CODE"
                WHEN NOT MATCHED THEN
                    INSERT VALUES (
                        source."DATA_ACTUAL_DATE", 
                        source."DATA_ACTUAL_END_DATE", 
                        source."ACCOUNT_RK", 
                        source."ACCOUNT_NUMBER",
                        source."CHAR_TYPE",
                        source."CURRENCY_RK",
                        source."CURRENCY_CODE"
                    );
                """)
            
            conn.execute(f'DROP TABLE "TEMP_MD_ACCOUNT_D";')
    except Exception as e:
        log_error('ft_balance_f', str(e))

def insert_into_md_currency_d():
    try:
        df = pd.read_csv(f'/src/files/md_currency_d.csv', sep=';', encoding_errors='replace')
        df['CODE_ISO_CHAR'] = df['CODE_ISO_CHAR'].apply(lambda x: 'NaN' if pd.isna(x) or len(x) != 3 else str(x))
        df['CURRENCY_CODE'] = df['CURRENCY_CODE'].fillna(0).astype(int)

        postgres_hook = PostgresHook('local-postgres')
        engine = postgres_hook.get_sqlalchemy_engine()

        with engine.connect() as conn:
            conn.execute(
                """
                CREATE TEMP TABLE "TEMP_MD_CURRENCY_D" AS
                SELECT * FROM "DS"."MD_CURRENCY_D";
                """)

            df.to_sql('TEMP_MD_CURRENCY_D', conn, if_exists='append', index=False)

            conn.execute(
                """
                MERGE INTO "DS"."MD_CURRENCY_D" AS target
                USING "TEMP_MD_CURRENCY_D" AS source
                ON target."DATA_ACTUAL_DATE" = source."DATA_ACTUAL_DATE" AND target."CURRENCY_RK" = source."CURRENCY_RK"
                WHEN MATCHED THEN
                    UPDATE SET 
                        "DATA_ACTUAL_END_DATE" = source."DATA_ACTUAL_END_DATE",
                        "CURRENCY_CODE" = source."CURRENCY_CODE",
                        "CODE_ISO_CHAR" = source."CODE_ISO_CHAR"
                WHEN NOT MATCHED THEN
                    INSERT VALUES (
                        source."CURRENCY_RK", 
                        source."DATA_ACTUAL_DATE", 
                        source."DATA_ACTUAL_END_DATE", 
                        source."CURRENCY_CODE",
                        source."CODE_ISO_CHAR"
                    );
                """)
            
            conn.execute(f'DROP TABLE "TEMP_MD_CURRENCY_D";')
    except Exception as e:
        log_error('md_currency_d', str(e))

def insert_into_md_exchange_rate_d():
    try:
        df = pd.read_csv(f'/src/files/md_exchange_rate_d.csv', sep=';', encoding_errors='replace')

        postgres_hook = PostgresHook('local-postgres')
        engine = postgres_hook.get_sqlalchemy_engine()

        with engine.connect() as conn:
            conn.execute(
                """
                CREATE TEMP TABLE "TEMP_MD_EXCHANGE_RATE_D" AS
                SELECT * FROM "DS"."MD_EXCHANGE_RATE_D";
                """)

            df.to_sql('TEMP_MD_EXCHANGE_RATE_D', conn, if_exists='append', index=False)
    
            conn.execute(
                """
                MERGE INTO "DS"."MD_EXCHANGE_RATE_D" AS target
                USING "TEMP_MD_EXCHANGE_RATE_D" AS source
                ON target."DATA_ACTUAL_DATE" = source."DATA_ACTUAL_DATE" AND target."CURRENCY_RK" = source."CURRENCY_RK"
                WHEN MATCHED THEN
                    UPDATE SET 
                        "DATA_ACTUAL_END_DATE" = source."DATA_ACTUAL_END_DATE",
                        "REDUCED_COURCE" = source."REDUCED_COURCE",
                        "CODE_ISO_NUM" = source."CODE_ISO_NUM"
                WHEN NOT MATCHED THEN
                    INSERT VALUES (
                        source."DATA_ACTUAL_DATE",
                        source."DATA_ACTUAL_END_DATE",
                        source."CURRENCY_RK", 
                        source."REDUCED_COURCE", 
                        source."CODE_ISO_NUM"
                    );
                """)
            
            conn.execute(f'DROP TABLE "TEMP_MD_EXCHANGE_RATE_D";')
    except Exception as e:
        log_error('md_exchange_rate_d', str(e))

def insert_into_md_ledger_account_s():
    try:
        df = pd.read_csv(f'/src/files/md_ledger_account_s.csv', sep=';', encoding_errors='replace')

        postgres_hook = PostgresHook('local-postgres')
        engine = postgres_hook.get_sqlalchemy_engine()

        with engine.connect() as conn:
            conn.execute(
                """
                CREATE TEMP TABLE "TEMP_MD_LEDGER_ACCOUNT_S" AS
                SELECT * FROM "DS"."MD_LEDGER_ACCOUNT_S";
                """)

            df.to_sql('TEMP_MD_LEDGER_ACCOUNT_S', conn, if_exists='append', index=False)
            
            conn.execute(
                """
            MERGE INTO "DS"."MD_LEDGER_ACCOUNT_S" AS target
            USING "TEMP_MD_LEDGER_ACCOUNT_S" AS source
            ON target."LEDGER_ACCOUNT" = source."LEDGER_ACCOUNT" AND target."START_DATE" = source."START_DATE"
            WHEN MATCHED THEN
                UPDATE SET 
                    target."CHAPTER" = source."CHAPTER",
                    target."CHAPTER_NAME" = source."CHAPTER_NAME",
                    target."SECTION_NUMBER" = source."SECTION_NUMBER",
                    target."SECTION_NAME" = source."SECTION_NAME",
                    target."SUBSECTION_NAME" = source."SUBSECTION_NAME",
                    target."LEDGER1_ACCOUNT" = source."LEDGER1_ACCOUNT",
                    target."LEDGER1_ACCOUNT_NAME" = source."LEDGER1_ACCOUNT_NAME",
                    target."LEDGER_ACCOUNT_NAME" = source."LEDGER_ACCOUNT_NAME",
                    target."CHARACTERISTIC" = source."CHARACTERISTIC",
                    target."IS_RESIDENT" = source."IS_RESIDENT",
                    target."IS_RESERVE" = source."IS_RESERVE",
                    target."IS_RESERVED" = source."IS_RESERVED",
                    target."IS_LOAN" = source."IS_LOAN",
                    target."IS_RESERVED_ASSETS" = source."IS_RESERVED_ASSETS",
                    target."IS_OVERDUE" = source."IS_OVERDUE",
                    target."IS_INTEREST" = source."IS_INTEREST",
                    target."PAIR_ACCOUNT" = source."PAIR_ACCOUNT",
                    target."END_DATE" = source."END_DATE",
                    target."IS_RUB_ONLY" = source."IS_RUB_ONLY",
                    target."MIN_TERM" = source."MIN_TERM",
                    target."MIN_TERM_MEASURE" = source."MIN_TERM_MEASURE",
                    target."MAX_TERM" = source."MAX_TERM",
                    target."MAX_TERM_MEASURE" = source."MAX_TERM_MEASURE",
                    target."LEDGER_ACC_FULL_NAME_TRANSLIT" = source."LEDGER_ACC_FULL_NAME_TRANSLIT",
                    target."IS_REVALUATION" = source."IS_REVALUATION",
                    target."IS_CORRECT" = source."IS_CORRECT"
            WHEN NOT MATCHED THEN
                INSERT VALUES (
                    source."CHAPTER", 
                    source."CHAPTER_NAME", 
                    source."SECTION_NUMBER", 
                    source."SECTION_NAME", 
                    source."SUBSECTION_NAME",
                    source."LEDGER1_ACCOUNT", 
                    source."LEDGER1_ACCOUNT_NAME", 
                    source."LEDGER_ACCOUNT", 
                    source."LEDGER_ACCOUNT_NAME", 
                    source."CHARACTERISTIC", 
                    source."IS_RESIDENT", 
                    source."IS_RESERVE", 
                    source."IS_RESERVED", 
                    source."IS_LOAN", 
                    source."IS_RESERVED_ASSETS", 
                    source."IS_OVERDUE", 
                    source."IS_INTEREST", 
                    source."PAIR_ACCOUNT", 
                    source."START_DATE", 
                    source."END_DATE", 
                    source."IS_RUB_ONLY", 
                    source."MIN_TERM", 
                    source."MIN_TERM_MEASURE", 
                    source."MAX_TERM", 
                    source."MAX_TERM_MEASURE", 
                    source."LEDGER_ACC_FULL_NAME_TRANSLIT", 
                    source."IS_REVALUATION", 
                    source."IS_CORRECT"
                );
                """)
            
            conn.execute(f'DROP TABLE "TEMP_MD_LEDGER_ACCOUNT_S";')
    except Exception as e:
        log_error('md_ledger_account_s', str(e))

default_args = {
    'owner': 'tsukerin',
    'start_date': datetime.now(),
    'retries': 2
}

with DAG(dag_id='insert_data',
        default_args=default_args,
        description='Создание необходимых таблиц и загрузка в них данных',
        template_searchpath='/src/',
        schedule_interval='0 0 * * *',
        catchup=False
) as dag:

    start_task = PythonOperator(
        task_id='start_task',
        python_callable=log_notify,
        op_args=['INFO', 'Началось импортирование данных. Создание таблиц...']
    )

    create_tables = SQLExecuteQueryOperator(
        task_id='create_tables',
        conn_id='local-postgres',
        sql='sql/create_tables.sql',
    )

    loading = PythonOperator(
        task_id='loading',
        python_callable=dummy_load,
        op_args=[5]
    )

    tables_created = PythonOperator(
        task_id='tables_created',
        python_callable=log_notify,
        op_args=['INFO', 'Таблицы созданы успешно. Импортирование данных...']
    )

    loading2 = PythonOperator(
        task_id='loading2',
        python_callable=dummy_load,
        op_args=[5]
    )

    ft_balance_f = PythonOperator(
        task_id="ft_balance_f",
        python_callable=insert_into_ft_balance_f
    )

    ft_posting_f = PythonOperator(
        task_id="ft_posting_f",
        python_callable=insert_into_ft_posting_f
    )

    md_account_d = PythonOperator(
        task_id="md_account_d",
        python_callable=insert_into_md_account_d
    )

    md_currency_d = PythonOperator(
        task_id="md_currency_d",
        python_callable=insert_into_md_currency_d
    )

    md_exchange_rate_d = PythonOperator(
        task_id="md_exchange_rate_d",
        python_callable=insert_into_md_exchange_rate_d
    )

    md_ledger_account_s = PythonOperator(
        task_id="md_ledger_account_s",
        python_callable=insert_into_md_ledger_account_s
    )

    end_task = PythonOperator(
        task_id='end_task',
        python_callable=log_notify,
        op_args=['SUCCESS', 'Загрузка данных успешно завершена!']
    )

    start_task >> tables_created >> [ft_balance_f, ft_posting_f, md_account_d, md_currency_d, md_exchange_rate_d, md_ledger_account_s] >> end_task
