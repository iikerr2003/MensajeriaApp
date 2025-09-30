from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
import logger_main as logger
from typing import Optional
import os
import sys

Base = declarative_base()
class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos."""
    pass

class User(Base):
    """Clase para representar a un usuario en la base de datos de la app de mensajería."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    uuid = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    profile_picture = Column(String, nullable=True)  # Ruta a la imagen de perfil
    phone_number = Column(String, nullable=True)


    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
    
class Database:
    """Clase para gestionar la conexión y operaciones con la base de datos."""

    def __init__(self, db_url: Optional[str] = None):
        self.logger = logger.BaseLogger(name="Database").logger
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///mensajeria.db")
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._create_tables()

    def _create_tables(self):
        """Crea las tablas en la base de datos si no existen."""
        try:
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Tablas de la base de datos creadas o ya existentes.")
        except SQLAlchemyError as e:
            self.logger.error(f"Error al crear las tablas: {e}")
            raise DatabaseError("No se pudieron crear las tablas de la base de datos.") from e

    def get_session(self):
        """Proporciona una nueva sesión de base de datos."""
        try:
            session = self.SessionLocal()
            self.logger.debug("Nueva sesión de base de datos creada.")
            return session
        except SQLAlchemyError as e:
            self.logger.error(f"Error al crear una sesión de base de datos: {e}")
            raise DatabaseError("No se pudo crear una sesión de base de datos.") from e

