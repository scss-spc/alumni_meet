import os
import logging
import pymysql
from db.connection import get_connection
from config import Config

logger = logging.getLogger(__name__)

def run_sql_file(file_path: str):
    """Execute a multi-statement SQL script file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"SQL file not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split by semicolon while ignoring comments and empty lines
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for statement in statements:
                if statement.startswith("--") or statement.startswith("/*"):
                    # Extract non-comment portion
                    lines = [line for line in statement.split("\n") if not line.strip().startswith("--")]
                    clean_statement = "\n".join(lines).strip()
                    if not clean_statement:
                        continue
                    statement = clean_statement
                try:
                    cursor.execute(statement)
                except pymysql.MySQLError as err:
                    # Index or duplicate errors can be logged as warning if already existing
                    logger.warning(f"Notice executing statement: {err}")
        conn.commit()
        logger.info(f"Successfully executed SQL script: {file_path}")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to execute SQL script {file_path}: {e}")
        raise
    finally:
        conn.close()

def init_database():
    """Initialize TiDB schema, indexes, and seed records."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_file = os.path.join(base_dir, "sql", "schema.sql")
    indexes_file = os.path.join(base_dir, "sql", "indexes.sql")
    seed_file = os.path.join(base_dir, "sql", "seed.sql")

    logger.info("Initializing TiDB database schema...")
    run_sql_file(schema_file)
    logger.info("Applying indexes...")
    run_sql_file(indexes_file)
    logger.info("Seeding initial meet and activities...")
    run_sql_file(seed_file)
    logger.info("Database initialization complete.")
