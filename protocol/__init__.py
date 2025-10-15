"""Módulo de protocolo compartido para comunicación cliente-servidor.

Este módulo define las estructuras de datos y contratos de comunicación
entre cliente y servidor para la aplicación de mensajería.
"""

from .messages import (
    MessageProtocol,
    ChatMessage,
    AuthRequest,
    AuthResponse,
    ChatListResponse,
    MessageListResponse,
    StatusEvent,
    ErrorResponse,
)

__all__ = [
    "MessageProtocol",
    "ChatMessage",
    "AuthRequest",
    "AuthResponse",
    "ChatListResponse",
    "MessageListResponse",
    "StatusEvent",
    "ErrorResponse",
]
