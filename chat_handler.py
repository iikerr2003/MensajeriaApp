"""Modulo base para la gestion de los chats y mensajes de cada usuario.
Tiene en cuenta el usuario loggeado y sus contactos."""

from typing import Optional, List
from datetime import datetime
import db_main as dbmain
import logger_main as logger

class ChatHandler:
    """Clase para gestionar los chats y mensajes de un usuario."""

    def __init__(self, user_uuid: str, database: dbmain.Database):
        self.logger = logger.BaseLogger(name="ChatHandler").logger
        self.user_uuid = user_uuid
        self.database = database
        self.user = self._get_user_by_uuid(user_uuid)
        if not self.user:
            self.logger.error(f"Usuario con UUID {user_uuid} no encontrado.")
            raise ValueError(f"Usuario con UUID {user_uuid} no encontrado.")
        self.logger.info(f"ChatHandler inicializado para el usuario {self.user.username}")

    def _get_user_by_uuid(self, uuid: str) -> Optional[dbmain.User]:
        """Obtiene un usuario por su UUID."""
        session = self.database.get_session()
        try:
            user = session.query(dbmain.User).filter(dbmain.User.uuid == uuid).first()
            return user
        except Exception as e:
            self.logger.error(f"Error al obtener el usuario por UUID: {e}")
            return None
        finally:
            session.close()

    def get_contacts(self) -> List[dbmain.User]:
        """Obtiene la lista de contactos del usuario."""
        # Implementar la lógica para obtener contactos desde la base de datos
        session = self.database.get_session()
        try:
            # Placeholder: retornar todos los usuarios excepto el actual
            contacts = session.query(dbmain.User).filter(dbmain.User.id != self.user.id).all()
            self.logger.debug(f"Obtenidos {len(contacts)} contactos para el usuario {self.user.username}")
            return contacts
        except Exception as e:
            self.logger.error(f"Error al obtener contactos: {e}")
            return []
        finally:
            session.close()