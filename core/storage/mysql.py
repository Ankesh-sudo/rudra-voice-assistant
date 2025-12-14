import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

_ENGINE = None


def get_mysql_url():
    user = os.getenv("MYSQL_USER")
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DATABASE")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        url = get_mysql_url()
        logger.debug("Creating SQLAlchemy engine: {}", url)
        _ENGINE = create_engine(url, pool_pre_ping=True)
    return _ENGINE


def verify_connection():
    """
    Verifies MySQL connection.
    Returns (True, message) or (False, error).
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return True, f"SELECT 1 -> {result}"
    except SQLAlchemyError as e:
        return False, str(e)
