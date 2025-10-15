"""Definiciones de mensajes y protocolos para comunicación cliente-servidor.

Este módulo contiene dataclasses para todos los tipos de mensajes que se
intercambian entre el cliente y el servidor, con serialización eficiente
usando msgpack y validación con pydantic.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import msgpack
from pydantic import BaseModel, Field, field_validator


# ==================== Modelos Pydantic para Validación ====================


class AuthRequestModel(BaseModel):
    """Modelo de validación para solicitudes de autenticación."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    device_id: Optional[str] = Field(None, max_length=100)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username debe contener solo caracteres alfanuméricos, guiones o guiones bajos")
        return v


class AuthResponseModel(BaseModel):
    """Modelo de validación para respuestas de autenticación."""

    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    expires_in: Optional[int] = None  # segundos
    error: Optional[str] = None


class ChatMessageModel(BaseModel):
    """Modelo de validación para mensajes de chat."""

    chat_id: int = Field(..., gt=0)
    sender_id: int = Field(..., gt=0)
    content: bytes  # Contenido encriptado
    nonce: bytes  # Nonce para encriptación
    timestamp: float = Field(default_factory=time.time)
    message_id: Optional[int] = None


class StatusEventModel(BaseModel):
    """Modelo de validación para eventos de estado."""

    event_type: str = Field(..., pattern="^(typing|read|user_online|user_offline)$")
    user_id: int = Field(..., gt=0)
    chat_id: Optional[int] = Field(None, gt=0)
    timestamp: float = Field(default_factory=time.time)


class ErrorResponseModel(BaseModel):
    """Modelo de validación para respuestas de error."""

    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=time.time)


# ==================== Dataclasses para Comunicación ====================


@dataclass
class MessageProtocol:
    """Protocolo base para todos los mensajes cliente-servidor.
    
    Attributes
    ----------
    type : str
        Tipo de mensaje: "auth", "chat", "message", "status", "error"
    payload : dict
        Datos del mensaje
    timestamp : float
        Timestamp Unix del mensaje
    signature : str
        Firma HMAC para verificación de integridad
    """

    type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

    def sign(self, secret_key: str) -> None:
        """Genera firma HMAC del mensaje para verificación de integridad.
        
        Parameters
        ----------
        secret_key : str
            Clave secreta para generar HMAC
        """
        message_data = msgpack.packb({
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp
        })
        self.signature = hmac.new(
            secret_key.encode(),
            message_data,
            hashlib.sha256
        ).hexdigest()

    def verify(self, secret_key: str) -> bool:
        """Verifica la firma HMAC del mensaje.
        
        Parameters
        ----------
        secret_key : str
            Clave secreta para verificar HMAC
            
        Returns
        -------
        bool
            True si la firma es válida, False en caso contrario
        """
        message_data = msgpack.packb({
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp
        })
        expected_signature = hmac.new(
            secret_key.encode(),
            message_data,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(self.signature, expected_signature)

    def to_bytes(self) -> bytes:
        """Serializa el mensaje a bytes usando msgpack.
        
        Returns
        -------
        bytes
            Mensaje serializado
        """
        return msgpack.packb({
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "signature": self.signature
        })

    @classmethod
    def from_bytes(cls, data: bytes) -> MessageProtocol:
        """Deserializa un mensaje desde bytes.
        
        Parameters
        ----------
        data : bytes
            Datos serializados con msgpack
            
        Returns
        -------
        MessageProtocol
            Mensaje deserializado
        """
        unpacked = msgpack.unpackb(data, raw=False)
        return cls(
            type=unpacked["type"],
            payload=unpacked["payload"],
            timestamp=unpacked.get("timestamp", time.time()),
            signature=unpacked.get("signature", "")
        )


@dataclass
class AuthRequest:
    """Solicitud de autenticación del cliente.
    
    Attributes
    ----------
    username : str
        Nombre de usuario
    password : str
        Contraseña (será hasheada antes de enviar)
    device_id : Optional[str]
        Identificador del dispositivo para sesiones multi-dispositivo
    """

    username: str
    password: str
    device_id: Optional[str] = None

    def validate(self) -> None:
        """Valida los datos de la solicitud usando pydantic."""
        AuthRequestModel(
            username=self.username,
            password=self.password,
            device_id=self.device_id
        )

    def to_protocol(self, secret_key: str) -> MessageProtocol:
        """Convierte a MessageProtocol firmado.
        
        Parameters
        ----------
        secret_key : str
            Clave para firmar el mensaje
            
        Returns
        -------
        MessageProtocol
            Mensaje de protocolo firmado
        """
        protocol = MessageProtocol(
            type="auth",
            payload={
                "username": self.username,
                "password": self.password,
                "device_id": self.device_id
            }
        )
        protocol.sign(secret_key)
        return protocol


@dataclass
class AuthResponse:
    """Respuesta de autenticación del servidor.
    
    Attributes
    ----------
    success : bool
        Indica si la autenticación fue exitosa
    access_token : Optional[str]
        Token JWT de acceso
    refresh_token : Optional[str]
        Token JWT para refrescar el access_token
    user_id : Optional[int]
        ID del usuario autenticado
    username : Optional[str]
        Nombre del usuario autenticado
    expires_in : Optional[int]
        Tiempo de expiración del token en segundos
    error : Optional[str]
        Mensaje de error si success=False
    """

    success: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    expires_in: Optional[int] = None
    error: Optional[str] = None

    def validate(self) -> None:
        """Valida los datos de la respuesta usando pydantic."""
        AuthResponseModel(
            success=self.success,
            access_token=self.access_token,
            refresh_token=self.refresh_token,
            user_id=self.user_id,
            username=self.username,
            expires_in=self.expires_in,
            error=self.error
        )

    @classmethod
    def from_protocol(cls, protocol: MessageProtocol) -> AuthResponse:
        """Crea AuthResponse desde MessageProtocol.
        
        Parameters
        ----------
        protocol : MessageProtocol
            Mensaje de protocolo recibido
            
        Returns
        -------
        AuthResponse
            Respuesta de autenticación
        """
        payload = protocol.payload
        return cls(
            success=payload.get("success", False),
            access_token=payload.get("access_token"),
            refresh_token=payload.get("refresh_token"),
            user_id=payload.get("user_id"),
            username=payload.get("username"),
            expires_in=payload.get("expires_in"),
            error=payload.get("error")
        )


@dataclass
class ChatMessage:
    """Mensaje de chat encriptado E2E.
    
    Attributes
    ----------
    chat_id : int
        ID del chat
    sender_id : int
        ID del usuario remitente
    content : bytes
        Contenido encriptado del mensaje
    nonce : bytes
        Nonce usado para encriptación
    timestamp : float
        Timestamp Unix del mensaje
    message_id : Optional[int]
        ID del mensaje (asignado por el servidor)
    """

    chat_id: int
    sender_id: int
    content: bytes
    nonce: bytes
    timestamp: float = field(default_factory=time.time)
    message_id: Optional[int] = None

    def validate(self) -> None:
        """Valida los datos del mensaje usando pydantic."""
        ChatMessageModel(
            chat_id=self.chat_id,
            sender_id=self.sender_id,
            content=self.content,
            nonce=self.nonce,
            timestamp=self.timestamp,
            message_id=self.message_id
        )

    def to_protocol(self, secret_key: str) -> MessageProtocol:
        """Convierte a MessageProtocol firmado.
        
        Parameters
        ----------
        secret_key : str
            Clave para firmar el mensaje
            
        Returns
        -------
        MessageProtocol
            Mensaje de protocolo firmado
        """
        import base64
        
        protocol = MessageProtocol(
            type="message",
            payload={
                "chat_id": self.chat_id,
                "sender_id": self.sender_id,
                "content": base64.b64encode(self.content).decode(),
                "nonce": base64.b64encode(self.nonce).decode(),
                "timestamp": self.timestamp,
                "message_id": self.message_id
            }
        )
        protocol.sign(secret_key)
        return protocol

    @classmethod
    def from_protocol(cls, protocol: MessageProtocol) -> ChatMessage:
        """Crea ChatMessage desde MessageProtocol.
        
        Parameters
        ----------
        protocol : MessageProtocol
            Mensaje de protocolo recibido
            
        Returns
        -------
        ChatMessage
            Mensaje de chat
        """
        import base64
        
        payload = protocol.payload
        return cls(
            chat_id=payload["chat_id"],
            sender_id=payload["sender_id"],
            content=base64.b64decode(payload["content"]),
            nonce=base64.b64decode(payload["nonce"]),
            timestamp=payload.get("timestamp", time.time()),
            message_id=payload.get("message_id")
        )


@dataclass
class StatusEvent:
    """Evento de estado de usuario o chat.
    
    Attributes
    ----------
    event_type : str
        Tipo de evento: "typing", "read", "user_online", "user_offline"
    user_id : int
        ID del usuario relacionado al evento
    chat_id : Optional[int]
        ID del chat (para eventos de chat)
    timestamp : float
        Timestamp Unix del evento
    """

    event_type: str
    user_id: int
    chat_id: Optional[int] = None
    timestamp: float = field(default_factory=time.time)

    def validate(self) -> None:
        """Valida los datos del evento usando pydantic."""
        StatusEventModel(
            event_type=self.event_type,
            user_id=self.user_id,
            chat_id=self.chat_id,
            timestamp=self.timestamp
        )

    def to_protocol(self, secret_key: str) -> MessageProtocol:
        """Convierte a MessageProtocol firmado.
        
        Parameters
        ----------
        secret_key : str
            Clave para firmar el mensaje
            
        Returns
        -------
        MessageProtocol
            Mensaje de protocolo firmado
        """
        protocol = MessageProtocol(
            type="status",
            payload={
                "event_type": self.event_type,
                "user_id": self.user_id,
                "chat_id": self.chat_id,
                "timestamp": self.timestamp
            }
        )
        protocol.sign(secret_key)
        return protocol

    @classmethod
    def from_protocol(cls, protocol: MessageProtocol) -> StatusEvent:
        """Crea StatusEvent desde MessageProtocol.
        
        Parameters
        ----------
        protocol : MessageProtocol
            Mensaje de protocolo recibido
            
        Returns
        -------
        StatusEvent
            Evento de estado
        """
        payload = protocol.payload
        return cls(
            event_type=payload["event_type"],
            user_id=payload["user_id"],
            chat_id=payload.get("chat_id"),
            timestamp=payload.get("timestamp", time.time())
        )


@dataclass
class ChatListResponse:
    """Respuesta con lista de chats del usuario.
    
    Attributes
    ----------
    chats : List[Dict[str, Any]]
        Lista de chats con sus metadatos
    total : int
        Total de chats disponibles
    page : int
        Página actual (para paginación)
    """

    chats: List[Dict[str, Any]]
    total: int
    page: int = 1

    @classmethod
    def from_protocol(cls, protocol: MessageProtocol) -> ChatListResponse:
        """Crea ChatListResponse desde MessageProtocol.
        
        Parameters
        ----------
        protocol : MessageProtocol
            Mensaje de protocolo recibido
            
        Returns
        -------
        ChatListResponse
            Lista de chats
        """
        payload = protocol.payload
        return cls(
            chats=payload.get("chats", []),
            total=payload.get("total", 0),
            page=payload.get("page", 1)
        )


@dataclass
class MessageListResponse:
    """Respuesta con lista de mensajes de un chat.
    
    Attributes
    ----------
    messages : List[ChatMessage]
        Lista de mensajes del chat
    total : int
        Total de mensajes en el chat
    has_more : bool
        Indica si hay más mensajes disponibles
    """

    messages: List[ChatMessage]
    total: int
    has_more: bool = False

    @classmethod
    def from_protocol(cls, protocol: MessageProtocol) -> MessageListResponse:
        """Crea MessageListResponse desde MessageProtocol.
        
        Parameters
        ----------
        protocol : MessageProtocol
            Mensaje de protocolo recibido
            
        Returns
        -------
        MessageListResponse
            Lista de mensajes
        """
        payload = protocol.payload
        messages_data = payload.get("messages", [])
        
        # Convertir cada mensaje a ChatMessage
        messages = []
        for msg_data in messages_data:
            import base64
            messages.append(ChatMessage(
                chat_id=msg_data["chat_id"],
                sender_id=msg_data["sender_id"],
                content=base64.b64decode(msg_data["content"]),
                nonce=base64.b64decode(msg_data["nonce"]),
                timestamp=msg_data.get("timestamp", time.time()),
                message_id=msg_data.get("message_id")
            ))
        
        return cls(
            messages=messages,
            total=payload.get("total", 0),
            has_more=payload.get("has_more", False)
        )


@dataclass
class ErrorResponse:
    """Respuesta de error del servidor.
    
    Attributes
    ----------
    error_code : str
        Código de error (ej: "AUTH_FAILED", "INVALID_REQUEST")
    error_message : str
        Mensaje descriptivo del error
    details : Optional[Dict[str, Any]]
        Detalles adicionales del error
    timestamp : float
        Timestamp Unix del error
    """

    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)

    def validate(self) -> None:
        """Valida los datos del error usando pydantic."""
        ErrorResponseModel(
            error_code=self.error_code,
            error_message=self.error_message,
            details=self.details,
            timestamp=self.timestamp
        )

    @classmethod
    def from_protocol(cls, protocol: MessageProtocol) -> ErrorResponse:
        """Crea ErrorResponse desde MessageProtocol.
        
        Parameters
        ----------
        protocol : MessageProtocol
            Mensaje de protocolo recibido
            
        Returns
        -------
        ErrorResponse
            Respuesta de error
        """
        payload = protocol.payload
        return cls(
            error_code=payload["error_code"],
            error_message=payload["error_message"],
            details=payload.get("details"),
            timestamp=payload.get("timestamp", time.time())
        )
