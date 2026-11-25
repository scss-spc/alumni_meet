import pymysql
import pymysql.cursors
from contextlib import contextmanager
import logging
import queue
import time
from config import Config

logger = logging.getLogger(__name__)

# Opening a TLS connection to TiDB costs ~0.7s, while a query on an open connection
# costs ~0.09s. Pages used to open a fresh connection for every query (up to 10 per
# page), so the shared helpers below reuse connections from a small per-process pool.
POOL_SIZE = 8
# Connections idle longer than this are pinged (and transparently reconnected) before reuse.
POOL_PING_AFTER_SECONDS = 30
_pool: "queue.LifoQueue[pymysql.connections.Connection]" = queue.LifoQueue(maxsize=POOL_SIZE)


def _connect_kwargs(autocommit: bool) -> dict:
    connect_kwargs = {
        "host": Config.DB_HOST,
        "port": Config.DB_PORT,
        "user": Config.DB_USER,
        "password": Config.DB_PASSWORD,
        "database": Config.DB_NAME,
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "autocommit": autocommit,
        "connect_timeout": 10,
        "read_timeout": 30,
        "write_timeout": 30
    }
    if Config.DB_SSL_CA:
        connect_kwargs["ssl"] = {"ca": Config.DB_SSL_CA}
    return connect_kwargs


def get_connection():
    """Create and return a raw (unpooled, autocommit off) PyMySQL connection to TiDB."""
    try:
        return pymysql.connect(**_connect_kwargs(autocommit=False))
    except pymysql.MySQLError as e:
        logger.error(f"Database connection error to TiDB ({Config.DB_HOST}:{Config.DB_PORT}): {e}")
        raise


def _new_pooled_connection():
    try:
        conn = pymysql.connect(**_connect_kwargs(autocommit=True))
    except pymysql.MySQLError as e:
        logger.error(f"Database connection error to TiDB ({Config.DB_HOST}:{Config.DB_PORT}): {e}")
        raise
    conn._pool_last_used = time.monotonic()
    return conn


def _acquire():
    """Take a healthy autocommit connection from the pool, or open a new one."""
    while True:
        try:
            conn = _pool.get_nowait()
        except queue.Empty:
            return _new_pooled_connection()
        if not conn.open:
            continue
        if time.monotonic() - getattr(conn, "_pool_last_used", 0) > POOL_PING_AFTER_SECONDS:
            try:
                conn.ping(reconnect=True)
            except Exception:
                _discard(conn)
                continue
        return conn


def _release(conn):
    """Return a connection to the pool (closing it if the pool is full or it is broken)."""
    if not conn.open:
        return
    conn._pool_last_used = time.monotonic()
    try:
        _pool.put_nowait(conn)
    except queue.Full:
        _discard(conn)


def _discard(conn):
    try:
        conn.close()
    except Exception:
        pass


@contextmanager
def get_db_connection():
    """Context manager providing a pooled connection inside a transaction (commit on success, rollback on error)."""
    conn = _acquire()
    try:
        conn.begin()
        yield conn
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        _discard(conn)
        logger.error(f"Transaction failed, rolling back: {e}")
        raise
    else:
        _release(conn)


@contextmanager
def get_db_cursor(commit=False):
    """Context manager providing a cursor on a pooled connection; statements run in one transaction."""
    conn = _acquire()
    try:
        conn.begin()
        with conn.cursor() as cursor:
            yield cursor
        if commit:
            conn.commit()
        else:
            conn.rollback()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        _discard(conn)
        logger.error(f"Database operation failed, rolled back: {e}")
        raise
    else:
        _release(conn)


def execute_query(sql: str, params: tuple | list | dict = None, fetch_one: bool = False, fetch_all: bool = False, commit: bool = False):
    """
    Execute a parameterized SQL query safely.
    Strictly forbids raw unparameterized query concatenation.
    Runs on a pooled autocommit connection, so a single statement commits on its own.
    """
    def run(conn):
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            if fetch_one:
                return cursor.fetchone()
            if fetch_all:
                return cursor.fetchall()
            return cursor.lastrowid or cursor.rowcount

    conn = _acquire()
    try:
        result = run(conn)
    except pymysql.err.OperationalError as e:
        _discard(conn)
        if not (fetch_one or fetch_all):
            # Never replay a write: it may already have been applied before the connection dropped.
            logger.error(f"Query execution failed: {sql} with params {params}. Error: {e}")
            raise
        # A pooled connection may have been dropped by the server; retry the read once on a fresh one.
        logger.warning(f"Retrying query on a fresh connection after: {e}")
        conn = _new_pooled_connection()
        try:
            result = run(conn)
        except Exception as e2:
            _discard(conn)
            logger.error(f"Query execution failed: {sql} with params {params}. Error: {e2}")
            raise
    except Exception as e:
        _discard(conn)
        logger.error(f"Query execution failed: {sql} with params {params}. Error: {e}")
        raise
    _release(conn)
    return result
