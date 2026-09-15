import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.app.core.config import settings

logger = logging.getLogger("database")

# SQLAlchemy MySQL Engine Configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Session factory for MySQL database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for ORM Models
Base = declarative_base()


def get_db() -> Generator:
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes MySQL database tables if connected."""
    try:
        # Import models so they register with Base.metadata before create_all
        from backend.app.db.models import Company, User, Document, DocumentPermission  # noqa: F401

        Base.metadata.create_all(bind=engine)
        logger.info("MySQL database schema verified and initialized successfully.")
    except Exception as e:
        logger.warning(
            f"MySQL connection/initialization check deferred: {str(e)}. "
            "Ensure MySQL server is running at DATABASE_URL when executing database operations."
        )
