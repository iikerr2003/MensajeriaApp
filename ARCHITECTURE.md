# Arquitectura Cliente-Servidor - MensajeriaApp

## Arquitectura Actual (Monolítica)

```
┌─────────────────────────────────────────────┐
│          Aplicación PyQt6 Desktop           │
│  ┌──────────────────────────────────────┐   │
│  │           mainui.py (UI)             │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │       chat_manager.py (Logic)        │   │
│  └──────────────┬───────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │    crypto_manager.py (Encryption)    │   │
│  └──────────────────────────────────────┘   │
│                 │                            │
│  ┌──────────────▼───────────────────────┐   │
│  │     db_main.py (SQLite Local)        │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

## Arquitectura Objetivo (Cliente-Servidor) - Fase 1 Completada ✅

```
┌──────────────────────┐                    ┌──────────────────────┐
│   Cliente PyQt6      │                    │  Servidor FastAPI    │
│                      │                    │                      │
│  ┌───────────────┐   │                    │  ┌───────────────┐   │
│  │   mainui.py   │   │                    │  │   main.py     │   │
│  │   (UI Layer)  │   │                    │  │   (FastAPI)   │   │
│  └───────┬───────┘   │                    │  └───────┬───────┘   │
│          │           │                    │          │           │
│  ┌───────▼────────┐  │                    │  ┌───────▼────────┐  │
│  │  api_client.py │  │   HTTP/WebSocket   │  │   auth.py      │  │
│  │  (API Client)  │◄─┼───────────────────►│  │   (JWT Auth)   │  │
│  └───────┬────────┘  │                    │  └───────┬────────┘  │
│          │           │                    │          │           │
│  ┌───────▼────────┐  │                    │  ┌───────▼────────┐  │
│  │crypto_manager  │  │                    │  │  websocket.py  │  │
│  │  (E2E Encrypt) │  │                    │  │  (Real-time)   │  │
│  └────────────────┘  │                    │  └───────┬────────┘  │
│          │           │                    │          │           │
│  ┌───────▼────────┐  │                    │  ┌───────▼────────┐  │
│  │  Offline Cache │  │                    │  │  db_async.py   │  │
│  │  (diskcache)   │  │                    │  │  (Async ORM)   │  │
│  └────────────────┘  │                    │  └───────┬────────┘  │
│                      │                    │          │           │
└──────────────────────┘                    │  ┌───────▼────────┐  │
                                            │  │  PostgreSQL    │  │
                                            │  │  (Database)    │  │
         ┌─────────────┐                    │  └────────────────┘  │
         │  protocol/  │◄───────────────────┤          │           │
         │  messages.py│    Shared Protocol │  ┌───────▼────────┐  │
         │  (msgpack)  │                    │  │     Redis      │  │
         └─────────────┘                    │  │  (Cache/Sess)  │  │
                                            │  └────────────────┘  │
                                            │                      │
                                            └──────────────────────┘
```

## Flujo de Mensajería E2E

```
Cliente A                 Servidor                    Cliente B
   │                         │                           │
   │  1. Encriptar mensaje   │                           │
   │     con clave del chat  │                           │
   ├────────────────────────►│                           │
   │                         │                           │
   │  2. Almacenar          │                           │
   │     (contenido         │                           │
   │      encriptado)       │                           │
   │                         │  3. Reenviar por WebSocket│
   │                         ├──────────────────────────►│
   │                         │                           │
   │                         │                           │  4. Desencriptar
   │                         │                           │     con clave local
   │                         │                           │
   │                         │  5. ACK de lectura        │
   │                         │◄──────────────────────────┤
   │  6. Actualizar estado   │                           │
   │◄────────────────────────┤                           │
```

## Componentes Implementados (Fase 1)

### 1. Protocol Module (`protocol/`)
- ✅ `MessageProtocol`: Protocolo base con firma HMAC
- ✅ `AuthRequest/Response`: Autenticación
- ✅ `ChatMessage`: Mensajes E2E encriptados
- ✅ `StatusEvent`: Eventos en tiempo real
- ✅ Serialización msgpack
- ✅ Validación pydantic

### 2. Async Database (`db_async.py`)
- ✅ AsyncDatabase con SQLAlchemy async
- ✅ Soporte PostgreSQL (asyncpg)
- ✅ Soporte SQLite (aiosqlite)
- ✅ Connection pooling
- ✅ Todas las operaciones CRUD async

### 3. Migrations (`alembic/`)
- ✅ Configuración Alembic con soporte async
- ✅ Migración inicial generada
- ✅ Autogenerate de cambios de esquema

### 4. API Specification (`server/api_spec.yaml`)
- ✅ OpenAPI 3.1 completa
- ✅ Endpoints REST documentados
- ✅ WebSocket documentado
- ✅ Schemas con validación
- ✅ Autenticación JWT

### 5. Infrastructure
- ✅ Docker Compose (PostgreSQL + Redis)
- ✅ Variables de entorno (.env.example)
- ✅ Documentación completa (INFRASTRUCTURE.md)
- ✅ .gitignore configurado

## Tecnologías Utilizadas

### Backend (Servidor)
- **FastAPI**: Framework web async (a implementar en Fase 2)
- **SQLAlchemy**: ORM async con PostgreSQL
- **asyncpg**: Driver PostgreSQL async
- **Redis**: Caché y gestión de sesiones
- **Alembic**: Migraciones de BD
- **python-jose**: JWT tokens

### Frontend (Cliente)
- **PyQt6**: Interfaz gráfica de usuario
- **aiohttp**: Cliente HTTP async
- **websockets**: Cliente WebSocket
- **diskcache**: Caché local offline-first

### Protocolo
- **msgpack**: Serialización binaria eficiente
- **pydantic**: Validación de datos
- **cryptography**: Encriptación E2E

### Base de Datos
- **PostgreSQL 16**: Base de datos relacional
- **Redis 7**: Caché en memoria

## Seguridad

### Encriptación End-to-End
```
Cliente A                      Servidor                    Cliente B
   │                              │                            │
   │  Mensaje: "Hola"             │                            │
   │  Clave: derive(password)     │                            │
   │  Encriptado: [bytes]         │                            │
   ├─────────────────────────────►│                            │
   │                              │                            │
   │                              │  Almacena: [bytes]         │
   │                              │  (NO desencripta)          │
   │                              │                            │
   │                              ├───────────────────────────►│
   │                              │  Reenvía: [bytes]          │
   │                              │                            │
   │                              │                            │  Clave: derive(password)
   │                              │                            │  Desencripta: "Hola"
```

### Autenticación JWT
```
Cliente                         Servidor
   │                               │
   │  POST /auth/login             │
   │  {username, password}         │
   ├──────────────────────────────►│
   │                               │
   │                               │  1. Verificar password
   │                               │  2. Generar JWT
   │                               │  3. Guardar refresh en Redis
   │                               │
   │  200 OK                       │
   │  {access_token, refresh}      │
   │◄──────────────────────────────┤
   │                               │
   │  GET /chats                   │
   │  Authorization: Bearer <JWT>  │
   ├──────────────────────────────►│
   │                               │  Verificar JWT
   │  200 OK                       │
   │  {chats: [...]}               │
   │◄──────────────────────────────┤
```

## Métricas de Performance

### Latencia Esperada
- **REST API**: < 50ms (local), < 200ms (producción)
- **WebSocket**: < 10ms para eventos en tiempo real
- **Base de datos**: < 5ms con pool de conexiones
- **Caché Redis**: < 1ms

### Escalabilidad
- **Conexiones simultáneas**: 10,000+ con uvicorn workers
- **Mensajes por segundo**: 1,000+ con WebSocket
- **Usuarios concurrentes**: Limitado por hardware y rate limiting

### Optimizaciones
- Connection pooling (10 + 20 overflow)
- Redis caché para queries frecuentes
- Paginación en todos los listados
- Compresión de mensajes grandes
- Índices en columnas de búsqueda

## Roadmap

### ✅ Fase 1: Preparación de Infraestructura (COMPLETADA)
- ✅ Módulo de protocolo compartido
- ✅ Base de datos async
- ✅ Migraciones Alembic
- ✅ Especificación OpenAPI
- ✅ Docker Compose
- ✅ Documentación

### 🔄 Fase 2: Desarrollo del Servidor (SIGUIENTE)
- [ ] Servidor FastAPI (`server/main.py`)
- [ ] Autenticación JWT (`server/auth.py`)
- [ ] WebSocket manager (`server/websocket.py`)
- [ ] Rutas REST (`server/routes/`)
- [ ] Middleware (rate limiting, CORS)

### 📋 Fase 3: Adaptación del Cliente
- [ ] API Client (`client/api_client.py`)
- [ ] Adaptar mainui.py
- [ ] Message queue offline
- [ ] Actualizar login_window.py

### 🔐 Fase 4: Seguridad y Optimización
- [ ] Mejorar E2E encryption
- [ ] Compresión de mensajes
- [ ] Caché Redis completo
- [ ] Índices y optimización de queries

### 🧪 Fase 5: Testing y Deployment
- [ ] Suite de tests completa
- [ ] CI/CD con GitHub Actions
- [ ] Kubernetes deployment
- [ ] Monitoreo y logging

---

**Estado actual:** Fase 1 completada ✅
**Siguiente paso:** Implementar servidor FastAPI (Fase 2)
