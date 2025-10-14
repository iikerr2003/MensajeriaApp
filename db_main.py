from sqlalchemy import create_engine, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String, DateTime, Boolean
import logger_main as logger
from typing import Optional, List
import os
import sys
import hashlib
from datetime import datetime
import uuid

Base = declarative_base()
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


class Chat(Base):
    """Representa una conversación entre dos usuarios."""

    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    chat_uuid = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encryption_type = Column(String, default="AES-256-GCM")  # Tipo de encriptación
    is_hidden_user1 = Column(Boolean, default=False)  # Chat oculto para user1
    is_hidden_user2 = Column(Boolean, default=False)  # Chat oculto para user2
    auto_delete_hours = Column(Integer, nullable=True)  # Auto-destrucción de mensajes (horas)
    my_message_color = Column(String, default="#DCF8C6")  # Color de mensajes propios
    their_message_color = Column(String, default="#FFFFFF")  # Color de mensajes recibidos
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Chat(id={self.id}, uuid={self.chat_uuid}, encryption={self.encryption_type})>"


class Message(Base):
    """Representa un mensaje individual dentro de un chat."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encrypted_content = Column(Text, nullable=False)  # Contenido encriptado
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    delete_at = Column(DateTime, nullable=True)  # Timestamp para auto-destrucción

    # Relaciones
    chat = relationship("Chat", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, chat_id={self.chat_id}, timestamp={self.timestamp})>"
    
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
        
    def add_user(self, username: str, email: str, hashed_password: str, uuid: str, phone_number: Optional[str] = None, profile_picture: Optional[str] = None):
        """Agrega un nuevo usuario a la base de datos."""
        session = self.get_session()
        try:
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                uuid=uuid,
                phone_number=phone_number,
                profile_picture=profile_picture
            )
            session.add(new_user)
            session.commit()
            self.logger.info(f"Usuario {username} agregado a la base de datos.")
            return new_user
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al agregar usuario: {e}")
            raise DatabaseError("No se pudo agregar el usuario a la base de datos.") from e
        finally:
            session.close()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Obtiene un usuario por su nombre de usuario."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            if user:
                self.logger.info(f"Usuario {username} encontrado.")
            else:
                self.logger.info(f"Usuario {username} no encontrado.")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener usuario: {e}")
            raise DatabaseError("No se pudo obtener el usuario de la base de datos.") from e
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Obtiene un usuario por su correo electrónico."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            if user:
                self.logger.info(f"Usuario con email {email} encontrado.")
            else:
                self.logger.info(f"Usuario con email {email} no encontrado.")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener usuario: {e}")
            raise DatabaseError("No se pudo obtener el usuario de la base de datos.") from e
        finally:
            session.close()
            
    def get_user_by_uuid(self, uuid: str) -> Optional[User]:
        """Obtiene un usuario por su UUID."""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.uuid == uuid).first()
            if user:
                self.logger.info(f"Usuario con UUID {uuid} encontrado.")
            else:
                self.logger.info(f"Usuario con UUID {uuid} no encontrado.")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener usuario: {e}")
            raise DatabaseError("No se pudo obtener el usuario de la base de datos.") from e
        finally:
            session.close()
            
    def update_last_login(self, user_id: int):
        """Actualiza la fecha y hora del último inicio de sesión del usuario."""
        session = self.get_session()
        try:
            user = session.get(User, user_id)
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
                self.logger.info(f"Último inicio de sesión de usuario {user.username} actualizado.")
            else:
                self.logger.warning(f"Usuario con ID {user_id} no encontrado para actualizar último inicio de sesión.")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al actualizar último inicio de sesión: {e}")
            raise DatabaseError("No se pudo actualizar el último inicio de sesión del usuario.") from e
        finally:
            session.close()
            
    def activity_of_user(self, user_id: int, is_active: bool):
        """Actualiza el estado de actividad de un usuario en la base de datos."""
        session = self.get_session()
        try:
            user = session.get(User, user_id)
            if user:
                user.is_active = is_active
                session.commit()
                if is_active:
                    self.logger.info(f"Usuario {user.username} activado.")
                else:
                    self.logger.info(f"Usuario {user.username} desactivado.")
            else:
                self.logger.warning(f"Usuario con ID {user_id} no encontrado para actualizar estado de actividad.")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al actualizar estado de actividad de usuario: {e}")
            raise DatabaseError("No se pudo actualizar el estado de actividad del usuario.") from e
        finally:
            session.close()

    def check_password(self, username: str, hashed_password: str) -> bool:
        """Verifica si la contraseña proporcionada coincide con la almacenada para el usuario."""
        user = self.get_user_by_username(username)
        if user and user.hashed_password == hashed_password:
            self.logger.info(f"Contraseña para usuario {username} verificada correctamente.")
            return True
        self.logger.warning(f"Contraseña para usuario {username} no coincide.")
        return False

    def hash_password(self, username: str, password: str) -> str:
        """Genera un hash a partir de la contraseña proporcionada."""
        password = password.encode('utf-8')
        salt = username.encode('utf-8')
        user = self.get_user_by_username(username)
        if user:
            n = user.created_at.second if user.created_at.second > 0 else 16
            n = 2 ** (n % 15 + 1)  # Asegurar que n es potencia de 2
            r = 8
        else:
            n = 2 ** 14
            r = 8
        p = 1
        hashed_password = hashlib.scrypt(password, salt=salt, n=n, r=r, p=p)
        return base64.b64encode(hashed_password).decode()

    # ===== Operaciones de Chat =====

    def create_chat(
        self,
        user1_id: int,
        user2_id: int,
        encryption_type: str = "AES-256-GCM",
        auto_delete_hours: Optional[int] = None,
    ) -> Chat:
        """Crea un nuevo chat entre dos usuarios."""
        session = self.get_session()
        try:
            # Verificar si ya existe un chat entre estos usuarios
            existing_chat = (
                session.query(Chat)
                .filter(
                    ((Chat.user1_id == user1_id) & (Chat.user2_id == user2_id))
                    | ((Chat.user1_id == user2_id) & (Chat.user2_id == user1_id))
                )
                .first()
            )
            if existing_chat:
                self.logger.info(f"Chat ya existe entre usuarios {user1_id} y {user2_id}")
                return existing_chat

            new_chat = Chat(
                user1_id=user1_id,
                user2_id=user2_id,
                encryption_type=encryption_type,
                auto_delete_hours=auto_delete_hours,
            )
            session.add(new_chat)
            session.commit()
            session.refresh(new_chat)
            self.logger.info(f"Chat creado entre usuarios {user1_id} y {user2_id}")
            return new_chat
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al crear chat: {e}")
            raise DatabaseError("No se pudo crear el chat.") from e
        finally:
            session.close()

    def get_chat_by_uuid(self, chat_uuid: str) -> Optional[Chat]:
        """Obtiene un chat por su UUID."""
        session = self.get_session()
        try:
            chat = session.query(Chat).filter(Chat.chat_uuid == chat_uuid).first()
            if chat:
                session.expunge(chat)  # Desacoplar del session
            return chat
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener chat: {e}")
            raise DatabaseError("No se pudo obtener el chat.") from e
        finally:
            session.close()

    def get_user_chats(self, user_id: int, include_hidden: bool = False) -> List[Chat]:
        """Obtiene todos los chats de un usuario."""
        session = self.get_session()
        try:
            query = session.query(Chat).filter(
                (Chat.user1_id == user_id) | (Chat.user2_id == user_id)
            )

            if not include_hidden:
                query = query.filter(
                    ((Chat.user1_id == user_id) & (Chat.is_hidden_user1 == False))
                    | ((Chat.user2_id == user_id) & (Chat.is_hidden_user2 == False))
                )

            chats = query.order_by(Chat.last_message_at.desc()).all()
            # Desacoplar objetos del session
            for chat in chats:
                session.expunge(chat)
            return chats
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener chats del usuario: {e}")
            raise DatabaseError("No se pudieron obtener los chats del usuario.") from e
        finally:
            session.close()

    def hide_chat(self, chat_id: int, user_id: int, hide: bool = True) -> None:
        """Oculta o muestra un chat para un usuario específico."""
        session = self.get_session()
        try:
            chat = session.get(Chat, chat_id)
            if not chat:
                raise ValueError(f"Chat con ID {chat_id} no encontrado")

            if chat.user1_id == user_id:
                chat.is_hidden_user1 = hide
            elif chat.user2_id == user_id:
                chat.is_hidden_user2 = hide
            else:
                raise ValueError(f"Usuario {user_id} no pertenece al chat {chat_id}")

            session.commit()
            action = "ocultado" if hide else "mostrado"
            self.logger.info(f"Chat {chat_id} {action} para usuario {user_id}")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al ocultar/mostrar chat: {e}")
            raise DatabaseError("No se pudo ocultar/mostrar el chat.") from e
        finally:
            session.close()

    def update_chat_encryption(self, chat_id: int, encryption_type: str) -> None:
        """Actualiza el tipo de encriptación de un chat."""
        session = self.get_session()
        try:
            chat = session.get(Chat, chat_id)
            if not chat:
                raise ValueError(f"Chat con ID {chat_id} no encontrado")

            chat.encryption_type = encryption_type
            session.commit()
            self.logger.info(f"Encriptación de chat {chat_id} actualizada a {encryption_type}")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al actualizar encriptación: {e}")
            raise DatabaseError("No se pudo actualizar la encriptación del chat.") from e
        finally:
            session.close()

    def update_chat_colors(self, chat_id: int, my_color: str, their_color: str) -> None:
        """Actualiza los colores personalizados de un chat."""
        session = self.get_session()
        try:
            chat = session.get(Chat, chat_id)
            if not chat:
                raise ValueError(f"Chat con ID {chat_id} no encontrado")

            chat.my_message_color = my_color
            chat.their_message_color = their_color
            session.commit()
            self.logger.info(f"Colores de chat {chat_id} actualizados")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al actualizar colores del chat: {e}")
            raise DatabaseError("No se pudo actualizar los colores del chat.") from e
        finally:
            session.close()

    # ===== Operaciones de Mensajes =====

    def add_message(
        self,
        chat_id: int,
        sender_id: int,
        encrypted_content: str,
        delete_at: Optional[datetime] = None,
    ) -> Message:
        """Añade un nuevo mensaje a un chat."""
        session = self.get_session()
        try:
            new_message = Message(
                chat_id=chat_id,
                sender_id=sender_id,
                encrypted_content=encrypted_content,
                delete_at=delete_at,
            )
            session.add(new_message)

            # Actualizar timestamp del último mensaje del chat
            chat = session.get(Chat, chat_id)
            if chat:
                chat.last_message_at = datetime.utcnow()

            session.commit()
            session.refresh(new_message)
            self.logger.info(f"Mensaje añadido al chat {chat_id}")
            return new_message
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al añadir mensaje: {e}")
            raise DatabaseError("No se pudo añadir el mensaje.") from e
        finally:
            session.close()

    def get_chat_messages(
        self,
        chat_id: int,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Message]:
        """Obtiene los mensajes de un chat con paginación opcional."""
        session = self.get_session()
        try:
            query = (
                session.query(Message)
                .filter(Message.chat_id == chat_id)
                .order_by(Message.timestamp.asc())
            )

            if limit:
                query = query.limit(limit).offset(offset)

            messages = query.all()
            # Desacoplar objetos del session
            for msg in messages:
                session.expunge(msg)
            return messages
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener mensajes: {e}")
            raise DatabaseError("No se pudieron obtener los mensajes del chat.") from e
        finally:
            session.close()

    def mark_messages_as_read(self, chat_id: int, user_id: int) -> None:
        """Marca todos los mensajes de un chat como leídos para un usuario."""
        session = self.get_session()
        try:
            session.query(Message).filter(
                Message.chat_id == chat_id,
                Message.sender_id != user_id,
                Message.is_read == False,
            ).update({Message.is_read: True})
            session.commit()
            self.logger.info(f"Mensajes del chat {chat_id} marcados como leídos")
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al marcar mensajes como leídos: {e}")
            raise DatabaseError("No se pudieron marcar los mensajes como leídos.") from e
        finally:
            session.close()

    def delete_expired_messages(self) -> int:
        """Elimina mensajes que han pasado su fecha de auto-destrucción."""
        session = self.get_session()
        try:
            now = datetime.utcnow()
            result = session.query(Message).filter(
                Message.delete_at.isnot(None), Message.delete_at <= now
            ).delete()
            session.commit()
            self.logger.info(f"{result} mensajes expirados eliminados")
            return result
        except SQLAlchemyError as e:
            session.rollback()
            self.logger.error(f"Error al eliminar mensajes expirados: {e}")
            raise DatabaseError("No se pudieron eliminar los mensajes expirados.") from e
        finally:
            session.close()


class DatabaseError(Exception):
    """Excepción personalizada para errores de base de datos."""

    pass


# Importar base64 para hash_password
import base64