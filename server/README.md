# FastAPI Server - MensajeriaApp

Servidor FastAPI implementando la Fase 2.1 del roadmap de migración cliente-servidor.

## 🎯 Características Implementadas

### ✅ Componentes Principales

- **FastAPI Application**: App configurada con lifespan management
- **Dependencias Asíncronas**: `get_db()` y `get_current_user()`
- **CORS Middleware**: Configurado para cliente PyQt6
- **Logging Estructurado**: Middleware para registrar todas las requests
- **Health Checks**: Endpoint `/health` con verificación de servicios
- **Rate Limiting**: Con Redis (100 req/min por IP)
- **JWT Authentication**: Autenticación con tokens JWT
- **Integración DB Async**: Usa `db_async.py` para operaciones de BD

### 📋 Endpoints Disponibles

#### Sistema
- `GET /` - Información básica de la API
- `GET /health` - Health check con estado de servicios
- `GET /docs` - Documentación interactiva Swagger UI
- `GET /redoc` - Documentación alternativa ReDoc

#### Autenticación
- `POST /auth/login` - Login con username/password, retorna JWT token

#### Usuarios
- `GET /users/me` - Información del usuario autenticado (requiere JWT)

## 🚀 Inicio Rápido

### Requisitos

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores
```

### Iniciar el Servidor

#### Modo Desarrollo (con auto-reload)

```bash
# Desde el directorio raíz del proyecto
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

#### Modo Producción

```bash
# Con múltiples workers
uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Verificar que Funciona

```bash
# Health check
curl http://localhost:8000/health

# Información de la API
curl http://localhost:8000/

# Documentación interactiva
# Abrir en navegador: http://localhost:8000/docs
```

## 🔐 Autenticación

### Login

```bash
# Obtener token JWT
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "tu_usuario",
    "password": "tu_password"
  }'

# Respuesta:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "expires_in": 3600
# }
```

### Usar el Token

```bash
# Obtener información del usuario autenticado
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## ⚙️ Configuración

### Variables de Entorno

Configurar en `.env`:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mensajeria

# Redis (para rate limiting y caché)
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

### Servicios Necesarios

#### PostgreSQL

```bash
# Con Docker
docker run -d \
  --name mensajeria-postgres \
  -e POSTGRES_DB=mensajeria \
  -e POSTGRES_USER=mensajeria_user \
  -e POSTGRES_PASSWORD=mensajeria_password \
  -p 5432:5432 \
  postgres:16

# O usar docker-compose (desde raíz del proyecto)
docker-compose up -d postgres
```

#### Redis

```bash
# Con Docker
docker run -d \
  --name mensajeria-redis \
  -p 6379:6379 \
  redis:7-alpine

# O usar docker-compose
docker-compose up -d redis
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Tests del servidor
python3 test_server.py

# Resultado esperado:
# ✅ PASSED     Imports
# ✅ PASSED     App Structure
# ✅ PASSED     Routes
# ✅ PASSED     JWT Operations
# ✅ PASSED     Password Hashing
# ✅ PASSED     Dependencies
# ✅ PASSED     Pydantic Models
# TOTAL: 7/7 tests passed
```

### Tests Manuales con curl

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Login (ajustar con usuario real)
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' \
  | jq -r .access_token)

# 3. Obtener perfil
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Test rate limiting (ejecutar 110 veces rápidamente)
for i in {1..110}; do
  curl -s http://localhost:8000/ > /dev/null
  echo "Request $i"
done
# Después de 100 requests, debería retornar 429 Too Many Requests
```

## 📊 Middleware Implementado

### 1. CORS Middleware

Permite requests desde orígenes configurados:
- Configurado en `ALLOWED_ORIGINS`
- Permite credenciales
- Permite todos los métodos y headers

### 2. Rate Limiting Middleware

Limita requests por IP:
- Configurable con `RATE_LIMIT_PER_MINUTE`
- Usa Redis para almacenar contadores
- Headers de respuesta: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- Retorna `429 Too Many Requests` cuando se excede

### 3. Logging Middleware

Registra todas las requests:
- Información de request: método, path, IP, user agent
- Información de response: status code, duración
- Formato JSON estructurado

## 🔧 Estructura del Código

```python
server/main.py
├── Configuración (JWT, Redis, CORS, etc.)
├── Password Hashing (bcrypt)
├── JWT Token Management
│   ├── create_access_token()
│   └── decode_access_token()
├── Modelos Pydantic
│   ├── Token
│   ├── TokenData
│   ├── LoginRequest
│   └── HealthResponse
├── Estado Global (AppState)
├── Lifespan Management
│   ├── Startup (DB + Redis)
│   └── Shutdown (cleanup)
├── FastAPI Application
├── Middleware
│   ├── CORS
│   ├── Rate Limiting
│   └── Logging
├── Dependencias
│   ├── get_db()
│   └── get_current_user()
└── Rutas
    ├── / (root)
    ├── /health
    ├── /auth/login
    └── /users/me
```

## 📝 Próximos Pasos (Fase 2.2+)

- [ ] Implementar rutas de chats (`/chats`)
- [ ] Implementar rutas de mensajes (`/chats/{id}/messages`)
- [ ] Implementar WebSocket manager para tiempo real
- [ ] Añadir más endpoints según OpenAPI spec
- [ ] Implementar refresh tokens
- [ ] Añadir registro de usuarios (`/auth/register`)

## 🐛 Troubleshooting

### Error: "Base de datos no disponible"

Verificar que PostgreSQL está corriendo:
```bash
docker ps | grep postgres
# O
pg_isready -h localhost -p 5432
```

### Error: "Redis no disponible"

El servidor funciona sin Redis pero sin rate limiting. Para habilitarlo:
```bash
docker ps | grep redis
# O
redis-cli ping
```

### Error: "Module not found"

Instalar dependencias faltantes:
```bash
pip install -r requirements.txt
```

### Error 401 en /users/me

Verificar que el token JWT es válido:
```bash
# Decodificar token (sin verificar firma)
echo "YOUR_TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | jq
```

## 📚 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT (python-jose)](https://python-jose.readthedocs.io/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Redis](https://redis.io/docs/)

---

**Estado**: ✅ Fase 2.1 Completada  
**Versión**: 1.0.0  
**Fecha**: 2025-10-15
