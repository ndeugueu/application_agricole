"""
Shared database configuration and utilities
"""
from sqlalchemy import create_engine, Column, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declared_attr
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import os

Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to models"""

    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


def get_database_url(default_db: str = "agricole_db") -> str:
    """Get database URL from environment variables"""
    return os.getenv(
        "DATABASE_URL",
        f"postgresql://agricole_user:agricole_secure_password_2025@localhost:5432/{default_db}"
    )


def create_db_engine(database_url: str = None):
    """Create SQLAlchemy engine with proper configuration"""
    if database_url is None:
        database_url = get_database_url()

    return create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # Verify connections before using
        echo=os.getenv("DEBUG", "false").lower() == "true"
    )


def get_session_factory(engine):
    """Create session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session(session_factory):
    """Context manager for database sessions"""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
