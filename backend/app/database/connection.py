"""
Configuración de base de datos y manejo de sesiones para la aplicación ElSol Challenge.

Maneja creación del motor SQLAlchemy, manejo de sesiones e inicialización de base de datos.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# Crear motor de base de datos
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Crear factoría de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para modelos
Base = declarative_base()


def get_db() -> Session:
    """
    Dependencia para obtener sesión de base de datos.
    
    Yields:
        Sesión de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_database():
    """Crear tablas de base de datos si no existen."""
    from app.database.models import Base
    
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_database():
    """Eliminar todas las tablas de la base de datos (usar con precaución)."""
    from app.database.models import Base
    
    logger.warning("Dropping all database tables")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        True if connection is working, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        return False
