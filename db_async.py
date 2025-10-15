"""Versión asíncrona de la capa de base de datos para soporte PostgreSQL.

Este módulo proporciona operaciones CRUD asíncronas usando SQLAlchemy async
con soporte para PostgreSQL y asyncpg. Mantiene compatibilidad con los
modelos existentes mientras añade capacidades async/await.
"""

from __future__ import annotations

import base64
import hashlib
import os
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base, relationship

import logger_main as logger

# Reutilizar Base de db_main.py para compatibilidad
from db_main import Base, User, Chat, Message, DatabaseError

# ==================== Clase Database Asíncrona ====================


class AsyncDatabase:
    """Versión asíncrona de la clase Database con soporte para PostgreSQL.
    
    Proporciona todas las operaciones CRUD como métodos async, manteniendo
    compatibilidad con los modelos existentes (User, Chat, Message).
    
    Ejemplo
    -------
    >>> db = AsyncDatabase("postgresql+asyncpg://user:pass@localhost/mensajeria")
    >>> async with db.get_session() as session:
    ...     user = await db.get_user_by_username("test", session)
    """

    def __init__(self, db_url: Optional[str] = None):
        """Inicializa la conexión asíncrona a la base de datos.
        
        Parameters
        ----------
        db_url : Optional[str]
            URL de conexión a la base de datos. Por defecto usa PostgreSQL
            desde variable de entorno DATABASE_URL, o SQLite async como fallback.
        """
        self.logger = logger.BaseLogger(name="AsyncDatabase").logger
        
        # Default a PostgreSQL async, con fallback a SQLite async
        self.db_url = db_url or os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///mensajeria.db"
        )
        
        # Convertir postgresql:// a postgresql+asyncpg:// si es necesario
        if self.db_url.startswith("postgresql://"):
            self.db_url = self.db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif self.db_url.startswith("sqlite:///"):
            self.db_url = self.db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        
        # Configurar engine con pooling
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            pool_size=10,  # Número de conexiones en el pool
            max_overflow=20,  # Conexiones adicionales permitidas
            pool_pre_ping=True,  # Verificar conexiones antes de usar
        )
        
        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        
        self.logger.info(f"AsyncDatabase inicializada con URL: {self.db_url.split('@')[-1]}")

    async def create_tables(self):
        """Crea las tablas en la base de datos si no existen."""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self.logger.info("Tablas de la base de datos creadas o ya existentes.")
        except SQLAlchemyError as e:
            self.logger.error(f"Error al crear las tablas: {e}")
            raise DatabaseError("No se pudieron crear las tablas de la base de datos.") from e

    def get_session(self) -> AsyncSession:
        """Proporciona una nueva sesión asíncrona de base de datos.
        
        Returns
        -------
        AsyncSession
            Sesión asíncrona para operaciones de base de datos
            
        Example
        -------
        >>> async with db.get_session() as session:
        ...     await db.add_user(..., session)
        """
        return self.async_session_maker()

    async def close(self):
        """Cierra todas las conexiones del pool."""
        await self.engine.dispose()
        self.logger.info("Conexiones de base de datos cerradas.")

    # ===== Operaciones de Usuario =====

    async def add_user(
        self,
        username: str,
        email: str,
        hashed_password: str,
        uuid_str: str,
        phone_number: Optional[str] = None,
        profile_picture: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> User:
        """Añade un nuevo usuario a la base de datos de forma asíncrona.
        
        Parameters
        ----------
        username : str
            Nombre de usuario único
        email : str
            Email único del usuario
        hashed_password : str
            Contraseña hasheada
        uuid_str : str
            UUID único del usuario
        phone_number : Optional[str]
            Número de teléfono (opcional)
        profile_picture : Optional[str]
            Ruta a la imagen de perfil (opcional)
        session : Optional[AsyncSession]
            Sesión existente o se creará una nueva
            
        Returns
        -------
        User
            Usuario creado
        """
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                uuid=uuid_str,
                phone_number=phone_number,
                profile_picture=profile_picture,
            )
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            self.logger.info(f"Usuario {username} agregado a la base de datos.")
            return new_user
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al agregar usuario: {e}")
            raise DatabaseError("No se pudo agregar el usuario a la base de datos.") from e
        finally:
            if close_session:
                await session.close()

    async def get_user_by_username(
        self,
        username: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[User]:
        """Obtiene un usuario por su nombre de usuario de forma asíncrona.
        
        Parameters
        ----------
        username : str
            Nombre de usuario a buscar
        session : Optional[AsyncSession]
            Sesión existente o se creará una nueva
            
        Returns
        -------
        Optional[User]
            Usuario encontrado o None
        """
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            if user:
                self.logger.info(f"Usuario {username} encontrado.")
            else:
                self.logger.info(f"Usuario {username} no encontrado.")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener usuario: {e}")
            raise DatabaseError("No se pudo obtener el usuario de la base de datos.") from e
        finally:
            if close_session:
                await session.close()

    async def get_user_by_email(
        self,
        email: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[User]:
        """Obtiene un usuario por su email de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            if user:
                self.logger.info(f"Usuario con email {email} encontrado.")
            else:
                self.logger.info(f"Usuario con email {email} no encontrado.")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener usuario: {e}")
            raise DatabaseError("No se pudo obtener el usuario de la base de datos.") from e
        finally:
            if close_session:
                await session.close()

    async def get_user_by_uuid(
        self,
        uuid_str: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[User]:
        """Obtiene un usuario por su UUID de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            result = await session.execute(
                select(User).where(User.uuid == uuid_str)
            )
            user = result.scalar_one_or_none()
            if user:
                self.logger.info(f"Usuario con UUID {uuid_str} encontrado.")
            else:
                self.logger.info(f"Usuario con UUID {uuid_str} no encontrado.")
            return user
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener usuario: {e}")
            raise DatabaseError("No se pudo obtener el usuario de la base de datos.") from e
        finally:
            if close_session:
                await session.close()

    async def update_last_login(
        self,
        user_id: int,
        session: Optional[AsyncSession] = None,
    ):
        """Actualiza la fecha del último login del usuario de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            user = await session.get(User, user_id)
            if user:
                user.last_login = datetime.utcnow()
                await session.commit()
                self.logger.info(f"Último inicio de sesión de usuario {user.username} actualizado.")
            else:
                self.logger.warning(
                    f"Usuario con ID {user_id} no encontrado para actualizar último inicio de sesión."
                )
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al actualizar último inicio de sesión: {e}")
            raise DatabaseError("No se pudo actualizar el último inicio de sesión del usuario.") from e
        finally:
            if close_session:
                await session.close()

    async def activity_of_user(
        self,
        user_id: int,
        is_active: bool,
        session: Optional[AsyncSession] = None,
    ):
        """Actualiza el estado de actividad de un usuario de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            user = await session.get(User, user_id)
            if user:
                user.is_active = is_active
                await session.commit()
                status = "activado" if is_active else "desactivado"
                self.logger.info(f"Usuario {user.username} {status}.")
            else:
                self.logger.warning(
                    f"Usuario con ID {user_id} no encontrado para actualizar estado de actividad."
                )
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al actualizar estado de actividad de usuario: {e}")
            raise DatabaseError("No se pudo actualizar el estado de actividad del usuario.") from e
        finally:
            if close_session:
                await session.close()

    async def check_password(
        self,
        username: str,
        hashed_password: str,
        session: Optional[AsyncSession] = None,
    ) -> bool:
        """Verifica si la contraseña hasheada coincide con la del usuario."""
        user = await self.get_user_by_username(username, session)
        if user and user.hashed_password == hashed_password:
            self.logger.info(f"Contraseña para usuario {username} verificada correctamente.")
            return True
        self.logger.warning(f"Contraseña para usuario {username} no coincide.")
        return False

    def hash_password(self, username: str, password: str, user: Optional[User] = None) -> str:
        """Genera un hash de la contraseña (método síncrono por naturaleza)."""
        password_bytes = password.encode("utf-8")
        salt = username.encode("utf-8")
        
        if user:
            n = user.created_at.second if user.created_at.second > 0 else 16
            n = 2 ** (n % 15 + 1)
            r = 8
        else:
            n = 2**14
            r = 8
        
        p = 1
        hashed_password = hashlib.scrypt(password_bytes, salt=salt, n=n, r=r, p=p)
        return base64.b64encode(hashed_password).decode()

    # ===== Operaciones de Chat =====

    async def create_chat(
        self,
        user1_id: int,
        user2_id: int,
        encryption_type: str = "AES-256-GCM",
        auto_delete_hours: Optional[int] = None,
        session: Optional[AsyncSession] = None,
    ) -> Chat:
        """Crea un nuevo chat entre dos usuarios de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            # Verificar si ya existe un chat
            result = await session.execute(
                select(Chat).where(
                    ((Chat.user1_id == user1_id) & (Chat.user2_id == user2_id))
                    | ((Chat.user1_id == user2_id) & (Chat.user2_id == user1_id))
                )
            )
            existing_chat = result.scalar_one_or_none()
            
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
            await session.commit()
            await session.refresh(new_chat)
            self.logger.info(f"Chat creado entre usuarios {user1_id} y {user2_id}")
            return new_chat
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al crear chat: {e}")
            raise DatabaseError("No se pudo crear el chat.") from e
        finally:
            if close_session:
                await session.close()

    async def get_chat_by_uuid(
        self,
        chat_uuid: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[Chat]:
        """Obtiene un chat por su UUID de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            result = await session.execute(
                select(Chat).where(Chat.chat_uuid == chat_uuid)
            )
            chat = result.scalar_one_or_none()
            return chat
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener chat: {e}")
            raise DatabaseError("No se pudo obtener el chat.") from e
        finally:
            if close_session:
                await session.close()

    async def get_user_chats(
        self,
        user_id: int,
        include_hidden: bool = False,
        session: Optional[AsyncSession] = None,
    ) -> List[Chat]:
        """Obtiene todos los chats de un usuario de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            query = select(Chat).where(
                (Chat.user1_id == user_id) | (Chat.user2_id == user_id)
            )

            if not include_hidden:
                query = query.where(
                    ((Chat.user1_id == user_id) & (Chat.is_hidden_user1 == False))
                    | ((Chat.user2_id == user_id) & (Chat.is_hidden_user2 == False))
                )

            query = query.order_by(Chat.last_message_at.desc())
            result = await session.execute(query)
            chats = result.scalars().all()
            return list(chats)
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener chats del usuario: {e}")
            raise DatabaseError("No se pudieron obtener los chats del usuario.") from e
        finally:
            if close_session:
                await session.close()

    async def hide_chat(
        self,
        chat_id: int,
        user_id: int,
        hide: bool = True,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Oculta o muestra un chat para un usuario de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            chat = await session.get(Chat, chat_id)
            if not chat:
                raise ValueError(f"Chat con ID {chat_id} no encontrado")

            if chat.user1_id == user_id:
                chat.is_hidden_user1 = hide
            elif chat.user2_id == user_id:
                chat.is_hidden_user2 = hide
            else:
                raise ValueError(f"Usuario {user_id} no pertenece al chat {chat_id}")

            await session.commit()
            action = "ocultado" if hide else "mostrado"
            self.logger.info(f"Chat {chat_id} {action} para usuario {user_id}")
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al ocultar/mostrar chat: {e}")
            raise DatabaseError("No se pudo ocultar/mostrar el chat.") from e
        finally:
            if close_session:
                await session.close()

    async def update_chat_encryption(
        self,
        chat_id: int,
        encryption_type: str,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Actualiza el tipo de encriptación de un chat de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            chat = await session.get(Chat, chat_id)
            if not chat:
                raise ValueError(f"Chat con ID {chat_id} no encontrado")

            chat.encryption_type = encryption_type
            await session.commit()
            self.logger.info(f"Encriptación de chat {chat_id} actualizada a {encryption_type}")
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al actualizar encriptación: {e}")
            raise DatabaseError("No se pudo actualizar la encriptación del chat.") from e
        finally:
            if close_session:
                await session.close()

    async def update_chat_colors(
        self,
        chat_id: int,
        my_color: str,
        their_color: str,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Actualiza los colores personalizados de un chat de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            chat = await session.get(Chat, chat_id)
            if not chat:
                raise ValueError(f"Chat con ID {chat_id} no encontrado")

            chat.my_message_color = my_color
            chat.their_message_color = their_color
            await session.commit()
            self.logger.info(f"Colores de chat {chat_id} actualizados")
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al actualizar colores del chat: {e}")
            raise DatabaseError("No se pudo actualizar los colores del chat.") from e
        finally:
            if close_session:
                await session.close()

    # ===== Operaciones de Mensajes =====

    async def add_message(
        self,
        chat_id: int,
        sender_id: int,
        encrypted_content: str,
        delete_at: Optional[datetime] = None,
        session: Optional[AsyncSession] = None,
    ) -> Message:
        """Añade un nuevo mensaje a un chat de forma asíncrona."""
        close_session = session is None
        if session is None:
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
            chat = await session.get(Chat, chat_id)
            if chat:
                chat.last_message_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(new_message)
            self.logger.info(f"Mensaje añadido al chat {chat_id}")
            return new_message
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al añadir mensaje: {e}")
            raise DatabaseError("No se pudo añadir el mensaje.") from e
        finally:
            if close_session:
                await session.close()

    async def get_chat_messages(
        self,
        chat_id: int,
        limit: Optional[int] = None,
        offset: int = 0,
        session: Optional[AsyncSession] = None,
    ) -> List[Message]:
        """Obtiene mensajes de un chat con paginación de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            query = select(Message).where(Message.chat_id == chat_id)
            query = query.order_by(Message.timestamp.asc())
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            messages = result.scalars().all()
            return list(messages)
        except SQLAlchemyError as e:
            self.logger.error(f"Error al obtener mensajes del chat: {e}")
            raise DatabaseError("No se pudieron obtener los mensajes del chat.") from e
        finally:
            if close_session:
                await session.close()

    async def mark_messages_as_read(
        self,
        chat_id: int,
        user_id: int,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Marca todos los mensajes de un chat como leídos de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            result = await session.execute(
                select(Message).where(
                    (Message.chat_id == chat_id)
                    & (Message.sender_id != user_id)
                    & (Message.is_read == False)
                )
            )
            messages = result.scalars().all()
            
            for message in messages:
                message.is_read = True
            
            await session.commit()
            self.logger.info(f"{len(messages)} mensajes marcados como leídos en chat {chat_id}")
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al marcar mensajes como leídos: {e}")
            raise DatabaseError("No se pudieron marcar los mensajes como leídos.") from e
        finally:
            if close_session:
                await session.close()

    async def delete_expired_messages(
        self,
        session: Optional[AsyncSession] = None,
    ) -> int:
        """Elimina mensajes expirados de forma asíncrona."""
        close_session = session is None
        if session is None:
            session = self.get_session()
        
        try:
            now = datetime.utcnow()
            result = await session.execute(
                select(Message).where(
                    (Message.delete_at.isnot(None)) & (Message.delete_at <= now)
                )
            )
            messages = result.scalars().all()
            
            count = len(messages)
            for message in messages:
                await session.delete(message)
            
            await session.commit()
            self.logger.info(f"{count} mensajes expirados eliminados")
            return count
        except SQLAlchemyError as e:
            await session.rollback()
            self.logger.error(f"Error al eliminar mensajes expirados: {e}")
            raise DatabaseError("No se pudieron eliminar los mensajes expirados.") from e
        finally:
            if close_session:
                await session.close()
