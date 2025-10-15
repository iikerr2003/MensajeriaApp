# Infraestructura Cliente-Servidor - Fase 1

Este documento describe la nueva infraestructura implementada en la Fase 1 del roadmap de migración cliente-servidor.

## 📦 Componentes Implementados

### 1. Módulo de Protocolo (`protocol/`)

Define contratos de comunicación entre cliente y servidor usando:
- **msgpack**: Serialización eficiente binaria
- **pydantic**: Validación robusta de datos
- **HMAC**: Firmas para verificación de integridad

#### Clases Principales:

- `MessageProtocol`: Protocolo base para todos los mensajes
- `AuthRequest/AuthResponse`: Autenticación y registro
- `ChatMessage`: Mensajes encriptados E2E
- `StatusEvent`: Eventos de estado (typing, online, etc.)
- `ErrorResponse`: Respuestas de error estandarizadas

#### Ejemplo de Uso:

```python
from protocol.messages import AuthRequest, MessageProtocol

# Crear solicitud de autenticación
auth_request = AuthRequest(
    username="user1",
    password="hashed_password",
    device_id="device_123"
)

# Validar datos
auth_request.validate()

# Convertir a protocolo firmado
protocol_msg = auth_request.to_protocol(secret_key="shared_secret")

# Serializar para transmisión
data = protocol_msg.to_bytes()

# En el receptor: deserializar
received_msg = MessageProtocol.from_bytes(data)

# Verificar firma
if received_msg.verify("shared_secret"):
    print("Mensaje íntegro y auténtico")
```

### 2. Base de Datos Asíncrona (`db_async.py`)

Implementación async de todas las operaciones CRUD usando:
- **SQLAlchemy async**: ORM asíncrono
- **asyncpg**: Driver PostgreSQL async
- **aiosqlite**: Driver SQLite async (para desarrollo)
- **Connection pooling**: Gestión eficiente de conexiones

#### Características:

- ✅ Todas las operaciones son `async/await`
- ✅ Soporte para PostgreSQL y SQLite
- ✅ Pool de conexiones configurable
- ✅ Compatible con modelos existentes (User, Chat, Message)
- ✅ Context managers para gestión automática de sesiones

#### Ejemplo de Uso:

```python
import asyncio
from db_async import AsyncDatabase

async def main():
    # Inicializar con PostgreSQL
    db = AsyncDatabase("postgresql+asyncpg://user:pass@localhost/mensajeria")
    
    # Crear tablas
    await db.create_tables()
    
    # Operaciones CRUD async
    async with db.get_session() as session:
        # Crear usuario
        user = await db.add_user(
            username="john_doe",
            email="john@example.com",
            hashed_password="hashed_pw",
            uuid_str="uuid-123",
            session=session
        )
        
        # Crear chat
        chat = await db.create_chat(
            user1_id=user.id,
            user2_id=2,
            encryption_type="AES-256-GCM",
            session=session
        )
        
        # Añadir mensaje
        message = await db.add_message(
            chat_id=chat.id,
            sender_id=user.id,
            encrypted_content="encrypted_data",
            session=session
        )
    
    # Cerrar conexiones
    await db.close()

asyncio.run(main())
```

### 3. Migraciones con Alembic (`alembic/`)

Sistema de migraciones de base de datos con soporte async:
- Versionado automático de esquema
- Migraciones reversibles
- Detección automática de cambios (autogenerate)

#### Comandos Útiles:

```bash
# Crear nueva migración automáticamente
alembic revision --autogenerate -m "Descripción del cambio"

# Aplicar migraciones
alembic upgrade head

# Revertir última migración
alembic downgrade -1

# Ver historial
alembic history

# Ver SQL sin ejecutar
alembic upgrade head --sql
```

#### Configuración:

El archivo `alembic/env.py` está configurado para:
- Leer `DATABASE_URL` de variables de entorno
- Soporte async con asyncpg/aiosqlite
- Usar modelos de `db_main.py` para autogenerate

### 4. Especificación OpenAPI (`server/api_spec.yaml`)

Especificación completa de la API REST usando OpenAPI 3.1:

#### Endpoints Implementados:

**Autenticación:**
- `POST /auth/login` - Login con JWT
- `POST /auth/register` - Registro de usuario
- `POST /auth/refresh` - Refrescar token

**Chats:**
- `GET /chats` - Listar chats del usuario
- `POST /chats` - Crear nuevo chat
- `GET /chats/{chat_id}` - Detalles del chat
- `PATCH /chats/{chat_id}/config` - Actualizar configuración

**Mensajes:**
- `GET /chats/{chat_id}/messages` - Obtener mensajes (paginado)
- `POST /chats/{chat_id}/messages` - Enviar mensaje

**Usuarios:**
- `GET /users/me` - Perfil del usuario
- `GET /users/search` - Buscar usuarios

**WebSocket:**
- `ws://server/ws/chat/{chat_id}?token=<jwt>` - Mensajería en tiempo real

#### Características de la API:

- ✅ Autenticación JWT Bearer
- ✅ Rate limiting (100 req/min por usuario)
- ✅ Paginación en todos los listados
- ✅ Validación de datos con Pydantic schemas
- ✅ Mensajes E2E encriptados (servidor nunca ve contenido)
- ✅ WebSocket para eventos en tiempo real

#### Ver la Especificación:

```bash
# Usar Swagger UI online
# Copiar el contenido de server/api_spec.yaml en:
# https://editor.swagger.io/

# O instalar herramientas locales:
pip install openapi-spec-validator
openapi-spec-validator server/api_spec.yaml
```

## 🔧 Configuración del Entorno

### Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# Base de datos (elegir uno)
# PostgreSQL (producción)
DATABASE_URL=postgresql://user:password@localhost:5432/mensajeria

# SQLite (desarrollo)
DATABASE_URL=sqlite:///mensajeria.db

# JWT Secrets (generar claves seguras)
JWT_SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria
JWT_REFRESH_SECRET_KEY=otra-clave-diferente-para-refresh

# Redis (para caché y sesiones)
REDIS_URL=redis://localhost:6379

# Servidor
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### Instalación de Dependencias

```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# O instalar grupos específicos:
# Base de datos async
pip install asyncpg aiosqlite sqlalchemy[asyncio] alembic

# Protocolo
pip install msgpack pydantic

# Servidor (Fase 2)
pip install fastapi uvicorn[standard] python-jose[cryptography] redis aiohttp
```

## 🧪 Tests

### Tests del Módulo de Protocolo

```python
python -c "
from protocol.messages import MessageProtocol, AuthRequest, ChatMessage

# Test serialización
protocol = MessageProtocol(type='test', payload={'data': 'hello'})
protocol.sign('secret')
data = protocol.to_bytes()
recovered = MessageProtocol.from_bytes(data)
assert recovered.verify('secret')
print('✅ Protocol tests passed')
"
```

### Tests de Base de Datos Async

```python
python -c "
import asyncio
from db_async import AsyncDatabase
import uuid

async def test():
    db = AsyncDatabase('sqlite+aiosqlite:///test.db')
    await db.create_tables()
    
    async with db.get_session() as session:
        user = await db.add_user(
            username='test',
            email='test@test.com',
            hashed_password='hash',
            uuid_str=str(uuid.uuid4()),
            session=session
        )
        assert user.id is not None
    
    await db.close()
    print('✅ AsyncDatabase tests passed')

asyncio.run(test())
"
```

## 🚀 Deployment

### Con Docker Compose

Crear `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: mensajeria
      POSTGRES_USER: mensajeria_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  # El servidor se agregará en Fase 2
  # server:
  #   build: .
  #   environment:
  #     DATABASE_URL: postgresql://mensajeria_user:secure_password@postgres/mensajeria
  #     REDIS_URL: redis://redis:6379
  #   depends_on:
  #     - postgres
  #     - redis
  #   ports:
  #     - "8000:8000"

volumes:
  postgres_data:
```

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down
```

### Migraciones en Producción

```bash
# Aplicar migraciones
export DATABASE_URL="postgresql://user:pass@host/db"
alembic upgrade head

# Backup antes de migrar
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Rollback si algo falla
alembic downgrade -1
```

## 📊 Arquitectura de Datos

### Modelo de Base de Datos

```
┌─────────────────┐
│     User        │
├─────────────────┤
│ id (PK)         │
│ uuid (UNIQUE)   │
│ username        │
│ email           │
│ hashed_password │
│ is_active       │
│ created_at      │
│ last_login      │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│      Chat       │
├─────────────────┤
│ id (PK)         │
│ chat_uuid       │
│ user1_id (FK)   │
│ user2_id (FK)   │
│ encryption_type │
│ auto_delete_hrs │
│ created_at      │
└─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│    Message      │
├─────────────────┤
│ id (PK)         │
│ chat_id (FK)    │
│ sender_id (FK)  │
│ encrypted_content│
│ timestamp       │
│ is_read         │
│ delete_at       │
└─────────────────┘
```

### Flujo de Datos

```
Cliente A                     Servidor                    Cliente B
    │                            │                            │
    │   1. Login (JWT)           │                            │
    ├───────────────────────────>│                            │
    │   2. Access Token          │                            │
    │<───────────────────────────┤                            │
    │                            │                            │
    │   3. Send Message          │                            │
    │   (encrypted E2E)          │                            │
    ├───────────────────────────>│                            │
    │                            │   4. Store encrypted       │
    │                            │      (never decrypts)      │
    │                            │                            │
    │                            │   5. Forward via WebSocket │
    │                            ├───────────────────────────>│
    │                            │                            │
    │                            │   6. ACK read              │
    │                            │<───────────────────────────┤
```

## 🔐 Seguridad

### Encriptación E2E

- El servidor **NUNCA** ve el contenido de los mensajes en claro
- Los mensajes se encriptan en el cliente con la clave del chat
- El servidor solo almacena y reenvía datos encriptados
- Claves derivadas con PBKDF2 (100,000 iteraciones)

### Autenticación

- JWT con RS256 (claves asimétricas)
- Access token: 1 hora de validez
- Refresh token: 30 días de validez
- Tokens almacenados en Redis para revocación instantánea

### Rate Limiting

- 100 requests/min por usuario autenticado
- 20 requests/min para endpoints de auth por IP
- Headers de respuesta para tracking: `X-RateLimit-*`

## 📝 Próximos Pasos

### Fase 2: Desarrollo del Servidor

- [ ] Implementar `server/main.py` con FastAPI
- [ ] Sistema de autenticación JWT en `server/auth.py`
- [ ] WebSocket manager en `server/websocket.py`
- [ ] Rutas REST en `server/routes/`
- [ ] Middleware para rate limiting y CORS

### Fase 3: Adaptación del Cliente

- [ ] Crear `client/api_client.py` para comunicación HTTP/WS
- [ ] Adaptar `mainui.py` para usar API client
- [ ] Implementar queue de mensajes offline
- [ ] Actualizar `login_window.py` para auth remota

### Fase 4: Seguridad y Optimización

- [ ] Mejorar E2E encryption con intercambio de claves
- [ ] Implementar compresión de mensajes
- [ ] Caché con Redis
- [ ] Optimización de queries con índices

### Fase 5: Testing y Deployment

- [ ] Suite completa de tests con pytest
- [ ] Docker setup completo
- [ ] CI/CD con GitHub Actions
- [ ] Documentación de deployment

## 🐛 Troubleshooting

### Error: "No module named 'asyncpg'"

```bash
pip install asyncpg aiosqlite
```

### Error: "Alembic migration fails"

```bash
# Verificar DATABASE_URL
echo $DATABASE_URL

# Reiniciar Alembic
rm -rf alembic/versions/*
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Error: "Connection pool timeout"

Aumentar pool size en `db_async.py`:

```python
self.engine = create_async_engine(
    self.db_url,
    pool_size=20,  # Aumentar
    max_overflow=40,  # Aumentar
)
```

## 📚 Referencias

- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [OpenAPI Specification](https://swagger.io/specification/)
- [msgpack](https://msgpack.org/)
- [Pydantic](https://docs.pydantic.dev/)

---

**Fase 1 completada** ✅ | **Próximo: Fase 2 - Desarrollo del Servidor**
