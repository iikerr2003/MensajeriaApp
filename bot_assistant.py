"""Bot conversacional obligatorio para todos los usuarios.

Este bot es un usuario especial que está automáticamente disponible para todos
los usuarios del sistema. Responde a mensajes básicos y sirve como futuro punto
de integración para IA avanzada.
"""

import re
import uuid as uuid_lib
from datetime import datetime
from typing import Optional

from db_main import Database
from logger_main import BaseLogger


class ConversationalBot(BaseLogger):
    """Bot conversacional que responde a mensajes de usuarios.
    
    Este bot es obligatorio para todos los usuarios y responde automáticamente
    a saludos y preguntas básicas. En el futuro se integrará con IA avanzada.
    """
    
    BOT_USERNAME = "AssistantBot"
    BOT_EMAIL = "bot@mensajeria.app"
    BOT_UUID = "00000000-0000-0000-0000-000000000001"  # UUID fijo para el bot
    
    # Patrones de respuesta
    RESPONSES = {
        r"(hola|hi|hey|buenos días|buenas tardes|buenas noches)": [
            "¡Hola! 👋 Soy el asistente de Mensajería Segura. ¿En qué puedo ayudarte?",
            "¡Hola! Bienvenido/a. Estoy aquí para asistirte con tus conversaciones.",
            "¡Hey! 😊 ¿Cómo estás? Estoy para ayudarte en lo que necesites.",
        ],
        r"(adiós|adios|chao|hasta luego|nos vemos|bye)": [
            "¡Hasta luego! 👋 Que tengas un excelente día.",
            "¡Adiós! Vuelve pronto. Aquí estaré cuando me necesites.",
            "¡Nos vemos! 😊 Cuídate mucho.",
        ],
        r"(cómo estás|como estas|qué tal|que tal)": [
            "¡Estoy muy bien, gracias! 🤖 Funcionando perfectamente para ayudarte.",
            "¡Excelente! Listo para asistirte en tus conversaciones seguras.",
            "¡Genial! Siempre operativo para servirte.",
        ],
        r"(gracias|thanks|thank you)": [
            "¡De nada! 😊 Es un placer ayudarte.",
            "¡No hay de qué! Estoy para servirte.",
            "¡Con gusto! Para eso estoy aquí.",
        ],
        r"(ayuda|help|qué puedes hacer|que puedes hacer)": [
            "Puedo ayudarte con:\n"
            "• Responder preguntas básicas\n"
            "• Guiarte en el uso de la aplicación\n"
            "• Información sobre encriptación\n"
            "• En el futuro: IA avanzada y más! 🚀",
            "Estoy aquí para:\n"
            "✓ Conversar contigo\n"
            "✓ Responder dudas\n"
            "✓ Asistirte con la app\n"
            "¡Pregúntame lo que necesites!",
        ],
        r"(encriptación|encriptacion|seguridad|privacidad)": [
            "🔒 Tus mensajes están protegidos con:\n"
            "• AES-256-GCM (recomendado)\n"
            "• ChaCha20-Poly1305\n"
            "• RSA-OAEP\n"
            "Puedes configurar la encriptación desde el botón '🔒 Seguridad'.",
            "Tu privacidad es nuestra prioridad. Usamos encriptación de grado militar "
            "con derivación segura de claves (PBKDF2 100K iteraciones). "
            "Tus mensajes están seguros. 🛡️",
        ],
    }
    
    DEFAULT_RESPONSE = (
        "Interesante mensaje. 🤔 Aún estoy aprendiendo a responder mejor.\n"
        "Escribe 'ayuda' para ver qué puedo hacer por ti.\n"
        "En el futuro tendré IA más avanzada. ¡Mantente atento! 🚀"
    )
    
    def __init__(self, database: Database):
        super().__init__(name="ConversationalBot", level=20)
        self.db = database
        self._bot_user = None
        self._response_counter = {}  # user_id -> counter para variar respuestas
        
    def ensure_bot_exists(self) -> int:
        """Asegura que el bot existe en la base de datos y devuelve su ID.
        
        Returns
        -------
        int
            ID del usuario bot en la base de datos.
        """
        try:
            # Buscar por username
            bot_user = self.db.get_user_by_username(self.BOT_USERNAME)
            
            if not bot_user:
                # Buscar por UUID fijo
                bot_user = self.db.get_user_by_uuid(self.BOT_UUID)
            
            if not bot_user:
                # Crear bot si no existe
                self.logger.info("Creando bot conversacional en base de datos")
                hashed_pw = self.db.hash_password(self.BOT_USERNAME, "bot_internal_password")
                bot_user = self.db.add_user(
                    username=self.BOT_USERNAME,
                    email=self.BOT_EMAIL,
                    hashed_password=hashed_pw,
                    uuid=self.BOT_UUID,
                    phone_number="+00 000 000 000",
                )
                self.logger.info(f"Bot creado con ID: {bot_user.id}")
            
            self._bot_user = bot_user
            return bot_user.id
            
        except Exception as e:
            self.logger.error(f"Error asegurando existencia del bot: {e}")
            raise
    
    def get_bot_user_id(self) -> int:
        """Obtiene el ID del bot (crea el bot si no existe).
        
        Returns
        -------
        int
            ID del usuario bot.
        """
        if not self._bot_user:
            return self.ensure_bot_exists()
        return self._bot_user.id
    
    def ensure_chat_with_user(self, user_id: int, chat_manager) -> int:
        """Asegura que existe un chat entre el usuario y el bot.
        
        Parameters
        ----------
        user_id : int
            ID del usuario.
        chat_manager : ChatManager
            Gestor de chats para crear/obtener el chat.
            
        Returns
        -------
        int
            ID del chat entre el usuario y el bot.
        """
        try:
            bot_id = self.get_bot_user_id()
            
            # Crear o obtener chat
            chat = chat_manager.create_or_get_chat(
                user1_id=user_id,
                user2_id=bot_id,
                encryption_type="AES-256-GCM",
                auto_delete_hours=None,  # Los mensajes del bot no se auto-destruyen
            )
            
            self.logger.info(f"Chat con bot asegurado para usuario {user_id}: chat_id={chat.id}")
            return chat.id
            
        except Exception as e:
            self.logger.error(f"Error asegurando chat con bot: {e}")
            raise
    
    def generate_response(self, message: str, user_id: int) -> str:
        """Genera una respuesta basada en el mensaje del usuario.
        
        Parameters
        ----------
        message : str
            Mensaje del usuario.
        user_id : int
            ID del usuario que envió el mensaje.
            
        Returns
        -------
        str
            Respuesta del bot.
        """
        message_lower = message.lower().strip()
        
        # Buscar patrón que coincida
        for pattern, responses in self.RESPONSES.items():
            if re.search(pattern, message_lower):
                # Variar respuestas usando contador
                if user_id not in self._response_counter:
                    self._response_counter[user_id] = {}
                
                if pattern not in self._response_counter[user_id]:
                    self._response_counter[user_id][pattern] = 0
                
                idx = self._response_counter[user_id][pattern] % len(responses)
                self._response_counter[user_id][pattern] += 1
                
                self.logger.info(f"Bot respondiendo a '{message}' con patrón '{pattern}'")
                return responses[idx]
        
        # Respuesta por defecto
        self.logger.info(f"Bot usando respuesta por defecto para '{message}'")
        return self.DEFAULT_RESPONSE
    
    def send_welcome_message(self, user_id: int, chat_manager, username: str) -> None:
        """Envía un mensaje de bienvenida automático al nuevo usuario.
        
        Parameters
        ----------
        user_id : int
            ID del nuevo usuario.
        chat_manager : ChatManager
            Gestor de chats.
        username : str
            Nombre del usuario para personalizar el mensaje.
        """
        try:
            bot_id = self.get_bot_user_id()
            chat_id = self.ensure_chat_with_user(user_id, chat_manager)
            
            welcome_message = (
                f"¡Hola {username}! 👋\n\n"
                "Soy el Asistente de Mensajería Segura. Estoy aquí para ayudarte.\n\n"
                "🔒 Tus conversaciones están protegidas con encriptación de alto nivel.\n"
                "💬 Puedes hablar conmigo cuando quieras.\n"
                "❓ Escribe 'ayuda' para ver qué puedo hacer.\n\n"
                "¡Disfruta de tus conversaciones seguras! 😊"
            )
            
            # Enviar mensaje usando el gestor de chats
            # Nota: El bot usa una contraseña interna fija
            chat_manager.send_message(
                chat_id=chat_id,
                sender_id=bot_id,
                message=welcome_message,
                password="bot_internal_password",
            )
            
            self.logger.info(f"Mensaje de bienvenida enviado a usuario {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error enviando mensaje de bienvenida: {e}")
            # No lanzar excepción para no interrumpir el flujo de registro
    
    def handle_user_message(
        self,
        message: str,
        user_id: int,
        chat_id: int,
        chat_manager,
    ) -> Optional[str]:
        """Procesa un mensaje del usuario y genera una respuesta automática.
        
        Parameters
        ----------
        message : str
            Mensaje del usuario.
        user_id : int
            ID del usuario.
        chat_id : int
            ID del chat donde ocurre la conversación.
        chat_manager : ChatManager
            Gestor de chats para enviar la respuesta.
            
        Returns
        -------
        str or None
            Respuesta generada, o None si hubo error.
        """
        try:
            bot_id = self.get_bot_user_id()
            
            # Generar respuesta
            response = self.generate_response(message, user_id)
            
            # Enviar respuesta
            chat_manager.send_message(
                chat_id=chat_id,
                sender_id=bot_id,
                message=response,
                password="bot_internal_password",
            )
            
            self.logger.info(f"Bot respondió en chat {chat_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error manejando mensaje del usuario: {e}")
            return None


# Para pruebas independientes
if __name__ == "__main__":
    from chat_manager import ChatManager
    
    db = Database()
    bot = ConversationalBot(db)
    chat_manager = ChatManager(db)
    
    # Asegurar que el bot existe
    bot_id = bot.ensure_bot_exists()
    print(f"Bot ID: {bot_id}")
    
    # Crear usuario de prueba
    import uuid
    test_user = db.get_user_by_username("test_chat_user")
    if not test_user:
        hashed_pw = db.hash_password("test_chat_user", "test123")
        test_user = db.add_user(
            username="test_chat_user",
            email="testchat@example.com",
            hashed_password=hashed_pw,
            uuid=str(uuid.uuid4()),
        )
    
    # Enviar mensaje de bienvenida
    bot.send_welcome_message(test_user.id, chat_manager, test_user.username)
    
    # Simular conversación
    chat_id = bot.ensure_chat_with_user(test_user.id, chat_manager)
    
    test_messages = [
        "Hola",
        "¿Cómo estás?",
        "Ayuda",
        "Háblame de encriptación",
        "Gracias",
        "Adiós",
    ]
    
    for msg in test_messages:
        print(f"\nUsuario: {msg}")
        response = bot.handle_user_message(msg, test_user.id, chat_id, chat_manager)
        print(f"Bot: {response}")
