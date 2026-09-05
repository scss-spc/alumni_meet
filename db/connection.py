import pymysql
import pymysql.cursors
from contextlib import contextmanager
import logging
from config import Config

logger = logging.getLogger(__name__)

def get_connection():
    """Create and return a raw PyMySQL connection to TiDB."""
    connect_kwargs = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "database": Config.DB_NAME,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": False
    }

    if Config.DB_SSL_CA:
        connect_kwargs["ssl"] = {"ca": Config.DB_SSL_CA}

    try:
        return pymysql.connect(**connect_kwargs)
    except pymysql.MySQLError as e:
        logger.error(f"Database connection error to TiDB ({Config.DB_HOST}:{Config.DB_PORT}): {e}")
        raise

@contextmanager
def get_db_connection():
    """Context manager providing a database connection with auto-commit/rollback."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction failed, rolling back: {e}")
        raise
    finally:
        conn.close()

@contextmanager
def get_db_cursor(commit=False):
    """Context manager providing a database cursor."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database operation failed, rolled back: {e}")
        raise
    finally:
        conn.close()

def execute_query(sql: str, params: tuple | list | dict = None, fetch_one: bool = False, fetch_all: bool = False, commit: bool = False):
    """
    Execute a parameterized SQL query safely.
    Strictly forbids raw unparameterized query concatenation.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.lastrowid or cursor.rowcount
        if commit:
            conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        logger.error(f"Query execution failed: {sql} with params {params}. Error: {e}")
        raise
    finally:
        conn.close()
