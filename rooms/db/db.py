"""
rooms/db/db.py
──────────────
PostgreSQL database initialisation helper.
Called by build.py before the Flask app starts to ensure the target
database exists.
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

load_dotenv()


def db_create(db_folder=None):
    """
    Connect to the PostgreSQL *server* (using the default 'postgres' database)
    and create the application database if it doesn't already exist.

    Environment variables used:
        DB_HOST     – e.g. localhost
        DB_PORT     – e.g. 5432
        DB_USER     – e.g. postgres
        DB_PASSWORD – your postgres password
        DB_NAME     – e.g. rooms_db
    """
    db_name     = os.getenv("DB_NAME",     "rooms_db")
    db_host     = os.getenv("DB_HOST",     "localhost")
    db_port     = os.getenv("DB_PORT",     "5432")
    db_user     = os.getenv("DB_USER",     "postgres")
    db_password = os.getenv("DB_PASSWORD", "postgres")

    try:
        # Connect to the default 'postgres' database so we can create ours
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            dbname="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Check whether the target database already exists
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()

        if not exists:
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ PostgreSQL database '{db_name}' created successfully!")
        else:
            print(f"ℹ️  PostgreSQL database '{db_name}' already exists.")

        cursor.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"❌ Could not connect to PostgreSQL server: {e}")
        print("   Make sure PostgreSQL is running and your .env credentials are correct.")
        raise
    except Exception as e:
        print(f"❌ Unexpected error during database setup: {e}")
        raise
