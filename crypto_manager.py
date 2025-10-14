"""Módulo para gestionar encriptación de mensajes con múltiples algoritmos.

Proporciona encriptación/desencriptación segura usando AES-256-GCM, ChaCha20-Poly1305
y RSA con gestión automática de claves y derivación segura de contraseñas.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from enum import Enum
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from logger_main import BaseLogger


class EncryptionType(Enum):
    """Tipos de encriptación soportados."""

    AES_256_GCM = "AES-256-GCM"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"
    RSA_OAEP = "RSA-OAEP"
    NONE = "Sin encriptación"


class CryptoManager(BaseLogger):
    """Gestor centralizado de operaciones criptográficas para mensajes.

    Ejemplo
    -------
    >>> manager = CryptoManager()
    >>> encrypted = manager.encrypt("Hola", "mi_password", EncryptionType.AES_256_GCM)
    >>> decrypted = manager.decrypt(encrypted, "mi_password", EncryptionType.AES_256_GCM)
    """

    def __init__(self) -> None:
        super().__init__(name="CryptoManager", level=20)  # INFO level
        self._rsa_keys: dict[str, tuple[bytes, bytes]] = {}  # chat_id -> (private, public)

    def encrypt(
        self,
        message: str,
        key: str,
        encryption_type: EncryptionType,
        chat_id: Optional[str] = None,
    ) -> str:
        """Encripta un mensaje usando el tipo de encriptación especificado.

        Parameters
        ----------
        message : str
            Texto plano a encriptar.
        key : str
            Contraseña o clave para derivar la clave de encriptación.
        encryption_type : EncryptionType
            Algoritmo de encriptación a usar.
        chat_id : str, optional
            ID del chat para RSA (genera/recupera par de claves).

        Returns
        -------
        str
            Mensaje encriptado en formato base64 con metadatos JSON.
        """
        if encryption_type == EncryptionType.NONE:
            return message

        try:
            if encryption_type == EncryptionType.AES_256_GCM:
                return self._encrypt_aes_gcm(message, key)
            elif encryption_type == EncryptionType.CHACHA20_POLY1305:
                return self._encrypt_chacha20(message, key)
            elif encryption_type == EncryptionType.RSA_OAEP:
                if not chat_id:
                    raise ValueError("chat_id requerido para encriptación RSA")
                return self._encrypt_rsa(message, chat_id)
            else:
                raise ValueError(f"Tipo de encriptación no soportado: {encryption_type}")
        except Exception as e:
            self.logger.error(f"Error encriptando mensaje: {e}")
            raise

    def decrypt(
        self,
        encrypted_message: str,
        key: str,
        encryption_type: EncryptionType,
        chat_id: Optional[str] = None,
    ) -> str:
        """Desencripta un mensaje previamente encriptado.

        Parameters
        ----------
        encrypted_message : str
            Mensaje encriptado en formato base64 con metadatos JSON.
        key : str
            Contraseña o clave para derivar la clave de desencriptación.
        encryption_type : EncryptionType
            Algoritmo usado para encriptar.
        chat_id : str, optional
            ID del chat para RSA.

        Returns
        -------
        str
            Mensaje desencriptado en texto plano.
        """
        if encryption_type == EncryptionType.NONE:
            return encrypted_message

        try:
            if encryption_type == EncryptionType.AES_256_GCM:
                return self._decrypt_aes_gcm(encrypted_message, key)
            elif encryption_type == EncryptionType.CHACHA20_POLY1305:
                return self._decrypt_chacha20(encrypted_message, key)
            elif encryption_type == EncryptionType.RSA_OAEP:
                if not chat_id:
                    raise ValueError("chat_id requerido para desencriptación RSA")
                return self._decrypt_rsa(encrypted_message, chat_id)
            else:
                raise ValueError(f"Tipo de encriptación no soportado: {encryption_type}")
        except Exception as e:
            self.logger.error(f"Error desencriptando mensaje: {e}")
            raise

    def _derive_key(self, password: str, salt: bytes, length: int = 32) -> bytes:
        """Deriva una clave criptográfica desde una contraseña usando PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=length,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())

    def _encrypt_aes_gcm(self, message: str, key: str) -> str:
        """Encripta con AES-256-GCM (autenticado)."""
        salt = os.urandom(16)
        nonce = os.urandom(12)
        derived_key = self._derive_key(key, salt, 32)

        aesgcm = AESGCM(derived_key)
        ciphertext = aesgcm.encrypt(nonce, message.encode(), None)

        payload = {
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def _decrypt_aes_gcm(self, encrypted_message: str, key: str) -> str:
        """Desencripta mensaje AES-256-GCM."""
        payload = json.loads(base64.b64decode(encrypted_message))
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        ciphertext = base64.b64decode(payload["ciphertext"])

        derived_key = self._derive_key(key, salt, 32)
        aesgcm = AESGCM(derived_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()

    def _encrypt_chacha20(self, message: str, key: str) -> str:
        """Encripta con ChaCha20-Poly1305 (autenticado)."""
        salt = os.urandom(16)
        nonce = os.urandom(12)
        derived_key = self._derive_key(key, salt, 32)

        chacha = ChaCha20Poly1305(derived_key)
        ciphertext = chacha.encrypt(nonce, message.encode(), None)

        payload = {
            "salt": base64.b64encode(salt).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "ciphertext": base64.b64encode(ciphertext).decode(),
        }
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def _decrypt_chacha20(self, encrypted_message: str, key: str) -> str:
        """Desencripta mensaje ChaCha20-Poly1305."""
        payload = json.loads(base64.b64decode(encrypted_message))
        salt = base64.b64decode(payload["salt"])
        nonce = base64.b64decode(payload["nonce"])
        ciphertext = base64.b64decode(payload["ciphertext"])

        derived_key = self._derive_key(key, salt, 32)
        chacha = ChaCha20Poly1305(derived_key)
        plaintext = chacha.decrypt(nonce, ciphertext, None)
        return plaintext.decode()

    def _get_or_create_rsa_keys(self, chat_id: str) -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Obtiene o genera par de claves RSA para un chat específico."""
        if chat_id not in self._rsa_keys:
            private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            public_key = private_key.public_key()

            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            self._rsa_keys[chat_id] = (private_pem, public_pem)
            self.logger.info(f"Par de claves RSA generado para chat {chat_id}")

        private_pem, public_pem = self._rsa_keys[chat_id]
        private_key = serialization.load_pem_private_key(private_pem, password=None)
        public_key = serialization.load_pem_public_key(public_pem)
        return private_key, public_key

    def _encrypt_rsa(self, message: str, chat_id: str) -> str:
        """Encripta con RSA-OAEP (para mensajes pequeños)."""
        _, public_key = self._get_or_create_rsa_keys(chat_id)

        # RSA solo puede encriptar datos pequeños, dividir si es necesario
        ciphertext = public_key.encrypt(
            message.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(ciphertext).decode()

    def _decrypt_rsa(self, encrypted_message: str, chat_id: str) -> str:
        """Desencripta mensaje RSA-OAEP."""
        private_key, _ = self._get_or_create_rsa_keys(chat_id)

        ciphertext = base64.b64decode(encrypted_message)
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return plaintext.decode()

    def generate_chat_key(self, chat_id: str, user_password: str) -> str:
        """Genera una clave derivada única para un chat específico.

        Parameters
        ----------
        chat_id : str
            Identificador único del chat.
        user_password : str
            Contraseña del usuario para derivar la clave.

        Returns
        -------
        str
            Clave derivada en formato base64.
        """
        salt = hashlib.sha256(chat_id.encode()).digest()
        key = self._derive_key(user_password, salt, 32)
        return base64.b64encode(key).decode()
