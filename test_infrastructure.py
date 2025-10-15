#!/usr/bin/env python3
"""
Script de validación completa para la infraestructura de Fase 1.
Ejecuta tests para todos los componentes implementados.
"""

import asyncio
import sys
import uuid as uuid_lib
from pathlib import Path

# Añadir directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))


def test_protocol_module():
    """Test del módulo de protocolo."""
    print("\n🧪 Testing Protocol Module...")
    
    from protocol.messages import (
        MessageProtocol,
        AuthRequest,
        AuthResponse,
        ChatMessage,
        StatusEvent,
        ErrorResponse,
    )
    
    # Test 1: MessageProtocol con firma HMAC
    print("  ✓ Testing MessageProtocol...")
    protocol = MessageProtocol(type="test", payload={"data": "hello"})
    protocol.sign("test_secret")
    assert protocol.signature != ""
    assert protocol.verify("test_secret")
    assert not protocol.verify("wrong_secret")
    
    # Test 2: Serialización/Deserialización
    print("  ✓ Testing serialization...")
    data = protocol.to_bytes()
    recovered = MessageProtocol.from_bytes(data)
    assert recovered.type == protocol.type
    assert recovered.payload == protocol.payload
    assert recovered.verify("test_secret")
    
    # Test 3: AuthRequest
    print("  ✓ Testing AuthRequest...")
    auth = AuthRequest(username="testuser", password="testpass123")
    auth.validate()  # Pydantic validation
    auth_protocol = auth.to_protocol("secret")
    assert auth_protocol.verify("secret")
    
    # Test 4: ChatMessage
    print("  ✓ Testing ChatMessage...")
    msg = ChatMessage(
        chat_id=1,
        sender_id=1,
        content=b"encrypted_content",
        nonce=b"nonce12345"
    )
    msg.validate()
    msg_protocol = msg.to_protocol("secret")
    recovered_msg = ChatMessage.from_protocol(msg_protocol)
    assert recovered_msg.content == msg.content
    assert recovered_msg.nonce == msg.nonce
    
    # Test 5: StatusEvent
    print("  ✓ Testing StatusEvent...")
    event = StatusEvent(event_type="typing", user_id=1, chat_id=1)
    event.validate()
    event_protocol = event.to_protocol("secret")
    recovered_event = StatusEvent.from_protocol(event_protocol)
    assert recovered_event.event_type == "typing"
    
    # Test 6: ErrorResponse
    print("  ✓ Testing ErrorResponse...")
    error = ErrorResponse(
        error_code="TEST_ERROR",
        error_message="Test error message",
        details={"reason": "testing"}
    )
    error.validate()
    
    print("✅ Protocol Module: ALL TESTS PASSED\n")


async def test_async_database():
    """Test de la base de datos asíncrona."""
    print("\n🧪 Testing Async Database...")
    
    from db_async import AsyncDatabase
    
    # Usar SQLite para tests
    db = AsyncDatabase("sqlite+aiosqlite:///test_validation.db")
    
    # Test 1: Crear tablas
    print("  ✓ Testing table creation...")
    await db.create_tables()
    
    # Test 2: Crear usuarios
    print("  ✓ Testing user creation...")
    async with db.get_session() as session:
        user1 = await db.add_user(
            username="testuser1",
            email="test1@example.com",
            hashed_password="hashed123",
            uuid_str=str(uuid_lib.uuid4()),
            phone_number="+1234567890",
            session=session
        )
        assert user1.id is not None
        assert user1.username == "testuser1"
        
        user2 = await db.add_user(
            username="testuser2",
            email="test2@example.com",
            hashed_password="hashed456",
            uuid_str=str(uuid_lib.uuid4()),
            session=session
        )
        assert user2.id is not None
    
    # Test 3: Buscar usuario
    print("  ✓ Testing user retrieval...")
    async with db.get_session() as session:
        found_user = await db.get_user_by_username("testuser1", session)
        assert found_user is not None
        assert found_user.email == "test1@example.com"
        
        found_by_email = await db.get_user_by_email("test2@example.com", session)
        assert found_by_email is not None
        assert found_by_email.username == "testuser2"
    
    # Test 4: Crear chat
    print("  ✓ Testing chat creation...")
    async with db.get_session() as session:
        chat = await db.create_chat(
            user1_id=user1.id,
            user2_id=user2.id,
            encryption_type="AES-256-GCM",
            auto_delete_hours=24,
            session=session
        )
        assert chat.id is not None
        assert chat.encryption_type == "AES-256-GCM"
        assert chat.auto_delete_hours == 24
    
    # Test 5: Añadir mensajes
    print("  ✓ Testing message creation...")
    async with db.get_session() as session:
        msg1 = await db.add_message(
            chat_id=chat.id,
            sender_id=user1.id,
            encrypted_content="encrypted_message_1",
            session=session
        )
        msg2 = await db.add_message(
            chat_id=chat.id,
            sender_id=user2.id,
            encrypted_content="encrypted_message_2",
            session=session
        )
        assert msg1.id is not None
        assert msg2.id is not None
    
    # Test 6: Obtener mensajes del chat
    print("  ✓ Testing message retrieval...")
    async with db.get_session() as session:
        messages = await db.get_chat_messages(chat.id, session=session)
        assert len(messages) == 2
        assert messages[0].encrypted_content == "encrypted_message_1"
        assert messages[1].encrypted_content == "encrypted_message_2"
    
    # Test 7: Obtener chats del usuario
    print("  ✓ Testing user chats retrieval...")
    async with db.get_session() as session:
        user_chats = await db.get_user_chats(user1.id, session=session)
        assert len(user_chats) == 1
        assert user_chats[0].id == chat.id
    
    # Test 8: Marcar mensajes como leídos
    print("  ✓ Testing mark messages as read...")
    async with db.get_session() as session:
        await db.mark_messages_as_read(chat.id, user2.id, session=session)
        messages = await db.get_chat_messages(chat.id, session=session)
        # El mensaje enviado por user1 debería estar marcado como leído por user2
        assert messages[0].is_read == True
    
    # Test 9: Actualizar configuración del chat
    print("  ✓ Testing chat configuration update...")
    async with db.get_session() as session:
        await db.update_chat_colors(
            chat.id,
            my_color="#FF0000",
            their_color="#00FF00",
            session=session
        )
        updated_chat = await db.get_chat_by_uuid(chat.chat_uuid, session)
        assert updated_chat.my_message_color == "#FF0000"
        assert updated_chat.their_message_color == "#00FF00"
    
    # Test 10: Ocultar chat
    print("  ✓ Testing hide chat...")
    async with db.get_session() as session:
        await db.hide_chat(chat.id, user1.id, hide=True, session=session)
        visible_chats = await db.get_user_chats(user1.id, include_hidden=False, session=session)
        assert len(visible_chats) == 0
        all_chats = await db.get_user_chats(user1.id, include_hidden=True, session=session)
        assert len(all_chats) == 1
    
    # Cerrar conexiones
    await db.close()
    
    # Limpiar archivo de prueba
    import os
    if os.path.exists("test_validation.db"):
        os.remove("test_validation.db")
    
    print("✅ Async Database: ALL TESTS PASSED\n")


def test_openapi_spec():
    """Valida la especificación OpenAPI."""
    print("\n🧪 Testing OpenAPI Specification...")
    
    import yaml
    
    # Cargar y parsear el spec
    print("  ✓ Loading OpenAPI spec...")
    with open("server/api_spec.yaml", "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    
    # Validar estructura básica
    print("  ✓ Validating basic structure...")
    assert "openapi" in spec
    assert spec["openapi"] == "3.1.0"
    assert "info" in spec
    assert "paths" in spec
    assert "components" in spec
    
    # Validar endpoints clave
    print("  ✓ Validating key endpoints...")
    required_paths = [
        "/auth/login",
        "/auth/register",
        "/chats",
        "/chats/{chat_id}",
        "/chats/{chat_id}/messages",
        "/users/me",
    ]
    for path in required_paths:
        assert path in spec["paths"], f"Missing path: {path}"
    
    # Validar schemas
    print("  ✓ Validating schemas...")
    required_schemas = [
        "User",
        "Chat",
        "Message",
        "AuthRequest",
        "AuthResponse",
        "ErrorResponse",
    ]
    for schema in required_schemas:
        assert schema in spec["components"]["schemas"], f"Missing schema: {schema}"
    
    # Validar seguridad
    print("  ✓ Validating security schemes...")
    assert "securitySchemes" in spec["components"]
    assert "bearerAuth" in spec["components"]["securitySchemes"]
    
    print("✅ OpenAPI Specification: ALL TESTS PASSED\n")


def test_alembic_setup():
    """Verifica la configuración de Alembic."""
    print("\n🧪 Testing Alembic Setup...")
    
    import os
    from pathlib import Path
    
    # Verificar archivos de Alembic
    print("  ✓ Checking Alembic files...")
    assert os.path.exists("alembic.ini")
    assert os.path.exists("alembic/env.py")
    assert os.path.exists("alembic/script.py.mako")
    assert os.path.exists("alembic/versions")
    
    # Verificar que hay al menos una migración
    print("  ✓ Checking migrations...")
    versions_dir = Path("alembic/versions")
    migrations = list(versions_dir.glob("*.py"))
    migrations = [m for m in migrations if m.name != "__init__.py"]
    assert len(migrations) > 0, "No migrations found"
    
    # Verificar contenido de env.py
    print("  ✓ Validating env.py configuration...")
    with open("alembic/env.py", "r") as f:
        env_content = f.read()
        assert "async" in env_content.lower()
        assert "asyncio" in env_content
        assert "from db_main import Base" in env_content
    
    print("✅ Alembic Setup: ALL TESTS PASSED\n")


def test_docker_compose():
    """Valida la configuración de Docker Compose."""
    print("\n🧪 Testing Docker Compose Configuration...")
    
    import yaml
    
    # Cargar docker-compose.yml
    print("  ✓ Loading docker-compose.yml...")
    with open("docker-compose.yml", "r") as f:
        compose = yaml.safe_load(f)
    
    # Validar servicios requeridos
    print("  ✓ Validating required services...")
    assert "services" in compose
    assert "postgres" in compose["services"]
    assert "redis" in compose["services"]
    
    # Validar configuración de PostgreSQL
    print("  ✓ Validating PostgreSQL configuration...")
    postgres = compose["services"]["postgres"]
    assert "image" in postgres
    assert "postgres" in postgres["image"]
    assert "environment" in postgres
    
    # Validar configuración de Redis
    print("  ✓ Validating Redis configuration...")
    redis = compose["services"]["redis"]
    assert "image" in redis
    assert "redis" in redis["image"]
    
    # Validar volúmenes
    print("  ✓ Validating volumes...")
    assert "volumes" in compose
    assert "postgres_data" in compose["volumes"]
    
    print("✅ Docker Compose: ALL TESTS PASSED\n")


def test_environment_setup():
    """Verifica archivos de configuración del entorno."""
    print("\n🧪 Testing Environment Setup...")
    
    import os
    
    # Verificar .env.example
    print("  ✓ Checking .env.example...")
    assert os.path.exists(".env.example")
    
    with open(".env.example", "r") as f:
        env_content = f.read()
        required_vars = [
            "DATABASE_URL",
            "JWT_SECRET_KEY",
            "JWT_REFRESH_SECRET_KEY",
            "REDIS_URL",
            "SERVER_HOST",
            "SERVER_PORT",
        ]
        for var in required_vars:
            assert var in env_content, f"Missing variable: {var}"
    
    # Verificar .gitignore
    print("  ✓ Checking .gitignore...")
    assert os.path.exists(".gitignore")
    
    with open(".gitignore", "r") as f:
        gitignore = f.read()
        assert ".env" in gitignore
        assert "*.db" in gitignore
        assert "__pycache__" in gitignore
    
    # Verificar requirements.txt
    print("  ✓ Checking requirements.txt...")
    assert os.path.exists("requirements.txt")
    
    with open("requirements.txt", "r") as f:
        requirements = f.read()
        required_packages = [
            "asyncpg",
            "msgpack",
            "pydantic",
            "fastapi",
            "alembic",
        ]
        for package in required_packages:
            assert package in requirements, f"Missing package: {package}"
    
    print("✅ Environment Setup: ALL TESTS PASSED\n")


def main():
    """Ejecuta todos los tests."""
    print("="*60)
    print("🚀 VALIDACIÓN COMPLETA DE INFRAESTRUCTURA - FASE 1")
    print("="*60)
    
    try:
        # Tests síncronos
        test_protocol_module()
        test_openapi_spec()
        test_alembic_setup()
        test_docker_compose()
        test_environment_setup()
        
        # Tests asíncronos
        asyncio.run(test_async_database())
        
        # Resumen final
        print("="*60)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("="*60)
        print("\n📋 Resumen de Componentes Validados:")
        print("  ✅ Protocol Module (msgpack + pydantic)")
        print("  ✅ Async Database (SQLAlchemy async)")
        print("  ✅ OpenAPI Specification")
        print("  ✅ Alembic Migrations")
        print("  ✅ Docker Compose")
        print("  ✅ Environment Configuration")
        print("\n🎉 La infraestructura de Fase 1 está lista!")
        print("📖 Ver INFRASTRUCTURE.md para más detalles")
        print("📐 Ver ARCHITECTURE.md para diagramas")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
