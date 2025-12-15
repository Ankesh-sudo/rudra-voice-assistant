import os
from urllib.parse import quote_plus
from contextlib import contextmanager
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

_ENGINE = None
_SessionLocal = None


def _database_url() -> str:
    user = os.getenv("MYSQL_USER", "rudra")
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    db = os.getenv("MYSQL_DATABASE", "rudra")

    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"


def get_engine():
    global _ENGINE, _SessionLocal
    if _ENGINE is None:
        url = _database_url()
        logger.debug("Creating SQLAlchemy engine: {}", url)
        _ENGINE = create_engine(url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False)
    return _ENGINE


@contextmanager
def get_session():
    if _SessionLocal is None:
        get_engine()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def verify_connection():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return True, f"SELECT 1 -> {result}"
    except Exception as e:
        return False, str(e)
