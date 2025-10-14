"""Gestor de chats con caché en memoria y sincronización eficiente con base de datos.

Proporciona una interfaz de alto nivel para gestionar conversaciones, enviar/recibir
mensajes encriptados y mantener sincronización eficiente con la base de datos.
"""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timedelta
from threading import Lock
from typing import Dict, List, Optional, Tuple

from crypto_manager import CryptoManager, EncryptionType
from db_main import Chat, Database, Message
from logger_main import BaseLogger


class ChatCache:
    """Caché LRU (Least Recently Used) para mensajes de chat."""

    def __init__(self, max_chats: int = 50, max_messages_per_chat: int = 100):
        self.max_chats = max_chats
        self.max_messages_per_chat = max_messages_per_chat
        self._cache: OrderedDict[int, List[Message]] = OrderedDict()
        self._lock = Lock()

    def get(self, chat_id: int) -> Optional[List[Message]]:
        """Obtiene mensajes del caché, moviendo el chat al final (más reciente)."""
        with self._lock:
            if chat_id in self._cache:
                self._cache.move_to_end(chat_id)
                return self._cache[chat_id].copy()
            return None

    def put(self, chat_id: int, messages: List[Message]) -> None:
        """Almacena mensajes en caché, respetando límites."""
        with self._lock:
            if chat_id in self._cache:
                self._cache.move_to_end(chat_id)
            self._cache[chat_id] = messages[-self.max_messages_per_chat :]

            # Eliminar chats menos usados si se excede el límite
            while len(self._cache) > self.max_chats:
                self._cache.popitem(last=False)

    def invalidate(self, chat_id: int) -> None:
        """Invalida el caché de un chat específico."""
        with self._lock:
            if chat_id in self._cache:
                del self._cache[chat_id]

    def clear(self) -> None:
        """Limpia todo el caché."""
        with self._lock:
            self._cache.clear()


class ChatManager(BaseLogger):
    """Gestor principal para operaciones de chat con encriptación y caché.

    Ejemplo
    -------
    >>> manager = ChatManager(db)
    >>> chat = manager.create_or_get_chat(user1_id=1, user2_id=2)
    >>> manager.send_message(chat.id, sender_id=1, message="Hola", password="secret")
    >>> messages = manager.get_messages(chat.id, password="secret")
    """

    def __init__(
        self,
        database: Database,
        crypto: Optional[CryptoManager] = None,
        cache_size: int = 50,
    ):
        super().__init__(name="ChatManager", level=20)
        self.db = database
        self.crypto = crypto or CryptoManager()
        self.cache = ChatCache(max_chats=cache_size)
        self._current_user_id: Optional[int] = None
        self._user_passwords: Dict[int, str] = {}  # user_id -> password temporal

    def set_current_user(self, user_id: int, password: str) -> None:
        """Establece el usuario actual y su contraseña para operaciones de encriptación."""
        self._current_user_id = user_id
        self._user_passwords[user_id] = password
        self.logger.info(f"Usuario actual establecido: {user_id}")

    def create_or_get_chat(
        self,
        user1_id: int,
        user2_id: int,
        encryption_type: str = "AES-256-GCM",
        auto_delete_hours: Optional[int] = None,
    ) -> Chat:
        """Crea un nuevo chat o devuelve uno existente entre dos usuarios."""
        try:
            chat = self.db.create_chat(
                user1_id=user1_id,
                user2_id=user2_id,
                encryption_type=encryption_type,
                auto_delete_hours=auto_delete_hours,
            )
            self.logger.info(f"Chat obtenido/creado: {chat.id}")
            return chat
        except Exception as e:
            self.logger.error(f"Error creando/obteniendo chat: {e}")
            raise

    def send_message(
        self,
        chat_id: int,
        sender_id: int,
        message: str,
        password: str,
    ) -> Message:
        """Envía un mensaje encriptado a un chat."""
        try:
            # Obtener configuración del chat
            chat = self.db.get_chat_by_uuid(str(chat_id))
            if not chat:
                # Buscar por ID si UUID no funciona
                session = self.db.get_session()
                chat = session.get(Chat, chat_id)
                session.close()

            if not chat:
                raise ValueError(f"Chat {chat_id} no encontrado")

            # Determinar tipo de encriptación
            enc_type = EncryptionType[chat.encryption_type.replace("-", "_").replace(" ", "_")]

            # Encriptar mensaje
            encrypted = self.crypto.encrypt(
                message=message,
                key=password,
                encryption_type=enc_type,
                chat_id=str(chat_id),
            )

            # Calcular tiempo de auto-destrucción si está configurado
            delete_at = None
            if chat.auto_delete_hours:
                delete_at = datetime.utcnow() + timedelta(hours=chat.auto_delete_hours)

            # Guardar en base de datos
            msg = self.db.add_message(
                chat_id=chat_id,
                sender_id=sender_id,
                encrypted_content=encrypted,
                delete_at=delete_at,
            )

            # Invalidar caché para forzar recarga
            self.cache.invalidate(chat_id)

            self.logger.info(f"Mensaje enviado al chat {chat_id}")
            return msg

        except Exception as e:
            self.logger.error(f"Error enviando mensaje: {e}")
            raise

    def get_messages(
        self,
        chat_id: int,
        password: str,
        force_reload: bool = False,
        limit: Optional[int] = None,
    ) -> List[Tuple[Message, str]]:
        """Obtiene mensajes desencriptados de un chat.

        Returns
        -------
        List[Tuple[Message, str]]
            Lista de tuplas (mensaje, contenido_desencriptado).
        """
        try:
            # Intentar obtener del caché primero
            if not force_reload:
                cached = self.cache.get(chat_id)
                if cached:
                    return self._decrypt_messages(cached, chat_id, password)

            # Cargar desde base de datos
            messages = self.db.get_chat_messages(chat_id=chat_id, limit=limit)

            # Actualizar caché
            self.cache.put(chat_id, messages)

            return self._decrypt_messages(messages, chat_id, password)

        except Exception as e:
            self.logger.error(f"Error obteniendo mensajes: {e}")
            raise

    def _decrypt_messages(
        self, messages: List[Message], chat_id: int, password: str
    ) -> List[Tuple[Message, str]]:
        """Desencripta una lista de mensajes."""
        result = []

        # Obtener tipo de encriptación del chat
        session = self.db.get_session()
        chat = session.get(Chat, chat_id)
        session.close()

        if not chat:
            raise ValueError(f"Chat {chat_id} no encontrado")

        enc_type = EncryptionType[chat.encryption_type.replace("-", "_").replace(" ", "_")]

        for msg in messages:
            try:
                decrypted = self.crypto.decrypt(
                    encrypted_message=msg.encrypted_content,
                    key=password,
                    encryption_type=enc_type,
                    chat_id=str(chat_id),
                )
                result.append((msg, decrypted))
            except Exception as e:
                self.logger.warning(f"Error desencriptando mensaje {msg.id}: {e}")
                result.append((msg, "[Error al desencriptar]"))

        return result

    def get_user_chats(self, user_id: int, include_hidden: bool = False) -> List[Chat]:
        """Obtiene todos los chats de un usuario."""
        try:
            chats = self.db.get_user_chats(user_id=user_id, include_hidden=include_hidden)
            self.logger.info(f"Obtenidos {len(chats)} chats para usuario {user_id}")
            return chats
        except Exception as e:
            self.logger.error(f"Error obteniendo chats del usuario: {e}")
            raise

    def hide_chat(self, chat_id: int, user_id: int, hide: bool = True) -> None:
        """Oculta o muestra un chat para un usuario."""
        try:
            self.db.hide_chat(chat_id=chat_id, user_id=user_id, hide=hide)
            self.cache.invalidate(chat_id)
            action = "ocultado" if hide else "mostrado"
            self.logger.info(f"Chat {chat_id} {action} para usuario {user_id}")
        except Exception as e:
            self.logger.error(f"Error ocultando/mostrando chat: {e}")
            raise

    def update_encryption(
        self, chat_id: int, new_encryption_type: str, password: str, new_password: str
    ) -> None:
        """Cambia el tipo de encriptación de un chat, re-encriptando mensajes existentes.

        ADVERTENCIA: Esta operación puede ser costosa para chats con muchos mensajes.
        """
        try:
            # Obtener mensajes actuales desencriptados
            messages_data = self.get_messages(chat_id, password, force_reload=True)

            # Actualizar tipo de encriptación en DB
            self.db.update_chat_encryption(chat_id, new_encryption_type)

            # Re-encriptar todos los mensajes (esto es una operación pesada)
            session = self.db.get_session()
            for msg, decrypted_text in messages_data:
                new_enc_type = EncryptionType[new_encryption_type.replace("-", "_").replace(" ", "_")]
                new_encrypted = self.crypto.encrypt(
                    message=decrypted_text,
                    key=new_password,
                    encryption_type=new_enc_type,
                    chat_id=str(chat_id),
                )
                db_msg = session.get(Message, msg.id)
                if db_msg:
                    db_msg.encrypted_content = new_encrypted

            session.commit()
            session.close()

            # Invalidar caché
            self.cache.invalidate(chat_id)

            self.logger.info(f"Encriptación actualizada para chat {chat_id}")

        except Exception as e:
            self.logger.error(f"Error actualizando encriptación: {e}")
            raise

    def mark_as_read(self, chat_id: int, user_id: int) -> None:
        """Marca todos los mensajes de un chat como leídos."""
        try:
            self.db.mark_messages_as_read(chat_id=chat_id, user_id=user_id)
            self.logger.info(f"Mensajes del chat {chat_id} marcados como leídos")
        except Exception as e:
            self.logger.error(f"Error marcando mensajes como leídos: {e}")
            raise

    def cleanup_expired_messages(self) -> int:
        """Elimina mensajes que han alcanzado su tiempo de auto-destrucción."""
        try:
            deleted = self.db.delete_expired_messages()
            if deleted > 0:
                self.cache.clear()  # Limpiar caché completo si hubo eliminaciones
            return deleted
        except Exception as e:
            self.logger.error(f"Error limpiando mensajes expirados: {e}")
            raise

    def get_chat_info(self, chat_id: int) -> Optional[Dict]:
        """Obtiene información resumida de un chat."""
        try:
            session = self.db.get_session()
            chat = session.get(Chat, chat_id)
            session.close()

            if not chat:
                return None

            return {
                "id": chat.id,
                "uuid": chat.chat_uuid,
                "encryption_type": chat.encryption_type,
                "auto_delete_hours": chat.auto_delete_hours,
                "my_message_color": chat.my_message_color,
                "their_message_color": chat.their_message_color,
                "created_at": chat.created_at,
                "last_message_at": chat.last_message_at,
            }
        except Exception as e:
            self.logger.error(f"Error obteniendo info del chat: {e}")
            raise
