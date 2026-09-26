"""SQLAlchemy engine, sessions, and database health checks."""

import logging
from collections.abc import Generator

from sqlalchemy import create_engine, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 2},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session and always close it after the request."""

    with SessionLocal() as session:
        yield session


def is_database_connected() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(select(1))
    except SQLAlchemyError as error:
        logger.warning(
            "Database health check failed: %s",
            type(error).__name__,
        )
        return False

    logger.info("Database connection successful")
    return True
