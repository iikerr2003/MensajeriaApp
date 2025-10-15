"""FastAPI server principal para MensajeriaApp.

Este módulo implementa el servidor FastAPI con:
- Autenticación JWT
- Endpoints REST
- Logging estructurado
- Health checks
- Rate limiting con Redis
- CORS configurado
"""

from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Annotated, Optional

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db_async import AsyncDatabase, User
from logger_main import BaseLogger

# ==================== Configuración ====================

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Rate Limiting Configuration
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))

# CORS Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

# Server Configuration
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))

# ==================== Logger ====================

logger = BaseLogger(name="FastAPIServer", level=20).logger

# ==================== Password Hashing ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera el hash de una contraseña."""
    return pwd_context.hash(password)


# ==================== JWT Token Management ====================


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea un token JWT de acceso.
    
    Parameters
    ----------
    data : dict
        Datos a codificar en el token
    expires_delta : Optional[timedelta]
        Tiempo de expiración del token
        
    Returns
    -------
    str
        Token JWT codificado
    """
    to_encode = data.copy()
    
    # Asegurar que 'sub' es string (requerido por jose JWT)
    if 'sub' in to_encode and not isinstance(to_encode['sub'], str):
        to_encode['sub'] = str(to_encode['sub'])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un token JWT.
    
    Parameters
    ----------
    token : str
        Token JWT a decodificar
        
    Returns
    -------
    dict
        Payload del token decodificado
        
    Raises
    ------
    JWTError
        Si el token es inválido o ha expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.error(f"Error decodificando token JWT: {e}")
        raise


# ==================== Modelos Pydantic ====================


class Token(BaseModel):
    """Modelo de respuesta para tokens de autenticación."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Modelo de datos extraídos del token."""
    user_id: Optional[int] = None
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Modelo de solicitud de login."""
    username: str
    password: str


class HealthResponse(BaseModel):
    """Modelo de respuesta del health check."""
    status: str
    timestamp: str
    version: str = "1.0.0"
    database: str = "connected"
    redis: str = "connected"


# ==================== Estado Global ====================


class AppState:
    """Estado global de la aplicación."""
    db: Optional[AsyncDatabase] = None
    redis: Optional[aioredis.Redis] = None


app_state = AppState()


# ==================== Lifespan Management ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación.
    
    Inicializa recursos al inicio y los limpia al finalizar.
    """
    # Startup
    logger.info("🚀 Iniciando servidor FastAPI...")
    
    # Inicializar base de datos
    try:
        app_state.db = AsyncDatabase()
        await app_state.db.create_tables()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise
    
    # Inicializar Redis
    try:
        app_state.redis = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await app_state.redis.ping()
        logger.info("✅ Redis conectado")
    except Exception as e:
        logger.warning(f"⚠️  Redis no disponible: {e}")
        app_state.redis = None
    
    logger.info("✅ Servidor iniciado correctamente")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando servidor FastAPI...")
    
    if app_state.db:
        await app_state.db.close()
        logger.info("✅ Base de datos cerrada")
    
    if app_state.redis:
        await app_state.redis.close()
        logger.info("✅ Redis cerrado")
    
    logger.info("✅ Servidor cerrado correctamente")


# ==================== Aplicación FastAPI ====================

app = FastAPI(
    title="MensajeriaApp API",
    description="API REST para aplicación de mensajería segura con encriptación E2E",
    version="1.0.0",
    lifespan=lifespan,
)

# ==================== Middleware ====================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Rate Limiting Middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Middleware de rate limiting usando Redis.
    
    Limita el número de requests por minuto por IP o usuario autenticado.
    """
    if app_state.redis is None:
        # Si Redis no está disponible, permitir todas las requests
        return await call_next(request)
    
    # Obtener identificador (IP o user_id si está autenticado)
    client_ip = request.client.host if request.client else "unknown"
    identifier = f"rate_limit:{client_ip}"
    
    # Verificar rate limit
    try:
        current_count = await app_state.redis.get(identifier)
        
        if current_count is None:
            # Primera request en esta ventana de tiempo
            await app_state.redis.setex(identifier, 60, 1)
        else:
            count = int(current_count)
            if count >= RATE_LIMIT_PER_MINUTE:
                # Rate limit excedido
                logger.warning(f"Rate limit excedido para {client_ip}")
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error_code": "RATE_LIMIT_EXCEEDED",
                        "error_message": f"Rate limit excedido. Máximo {RATE_LIMIT_PER_MINUTE} requests por minuto.",
                        "retry_after": 60
                    },
                    headers={
                        "X-RateLimit-Limit": str(RATE_LIMIT_PER_MINUTE),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + 60),
                        "Retry-After": "60"
                    }
                )
            else:
                # Incrementar contador
                await app_state.redis.incr(identifier)
        
        # Añadir headers de rate limit a la respuesta
        response = await call_next(request)
        
        current = int(await app_state.redis.get(identifier) or 0)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_PER_MINUTE - current))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 60)
        
        return response
        
    except Exception as e:
        logger.error(f"Error en rate limiting: {e}")
        # En caso de error, permitir la request
        return await call_next(request)


# Logging Middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware de logging estructurado.
    
    Registra todas las requests con información relevante.
    """
    start_time = time.time()
    
    # Log request
    logger.info(
        f"REQUEST: {request.method} {request.url.path}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    duration = time.time() - start_time
    logger.info(
        f"RESPONSE: {response.status_code} {request.url.path} ({duration:.3f}s)",
        extra={
            "status_code": response.status_code,
            "duration_seconds": duration
        }
    )
    
    return response


# ==================== Dependencias ====================


async def get_db():
    """Dependencia para obtener una sesión de base de datos.
    
    Yields
    ------
    AsyncSession
        Sesión de base de datos asíncrona
    """
    if app_state.db is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible"
        )
    
    async with app_state.db.get_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error en sesión de base de datos: {e}")
            raise


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependencia para obtener el usuario autenticado actual.
    
    Extrae y valida el token JWT del header Authorization.
    
    Parameters
    ----------
    request : Request
        Request HTTP
    db : AsyncSession
        Sesión de base de datos
        
    Returns
    -------
    User
        Usuario autenticado
        
    Raises
    ------
    HTTPException
        Si el token es inválido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extraer token del header Authorization
    authorization: str = request.headers.get("Authorization")
    if not authorization:
        raise credentials_exception
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception
    except ValueError:
        raise credentials_exception
    
    # Decodificar token
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        
        # Convertir a int si es necesario
        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise credentials_exception
            
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    
    # Obtener usuario de la base de datos por ID
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    return user


# ==================== Rutas ====================


@app.get("/", tags=["root"])
async def root():
    """Endpoint raíz de la API."""
    return {
        "message": "MensajeriaApp API",
        "version": "1.0.0",
        "status": "running",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }


@app.get("/health", response_model=HealthResponse, tags=["system"])
async def health_check():
    """Health check endpoint.
    
    Verifica el estado del servidor, base de datos y Redis.
    
    Returns
    -------
    HealthResponse
        Estado del servidor y servicios
    """
    # Verificar base de datos
    db_status = "connected"
    if app_state.db is None:
        db_status = "disconnected"
    else:
        try:
            async with app_state.db.get_session() as session:
                # Verificar conexión
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
        except Exception as e:
            logger.error(f"Error verificando base de datos: {e}")
            db_status = "error"
    
    # Verificar Redis
    redis_status = "disconnected"
    if app_state.redis:
        try:
            await app_state.redis.ping()
            redis_status = "connected"
        except Exception as e:
            logger.error(f"Error verificando Redis: {e}")
            redis_status = "error"
    
    # Determinar estado general
    overall_status = "healthy"
    if db_status != "connected":
        overall_status = "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        database=db_status,
        redis=redis_status
    )


@app.post("/auth/login", response_model=Token, tags=["auth"])
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Endpoint de autenticación.
    
    Autentica un usuario y devuelve un token JWT.
    
    Parameters
    ----------
    login_data : LoginRequest
        Credenciales de login
    db : AsyncSession
        Sesión de base de datos
        
    Returns
    -------
    Token
        Token JWT de acceso
        
    Raises
    ------
    HTTPException
        Si las credenciales son inválidas
    """
    # Buscar usuario
    user = await app_state.db.get_user_by_username(login_data.username, db)
    
    if not user:
        logger.warning(f"Intento de login fallido: usuario {login_data.username} no encontrado")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    # Nota: Usar el método hash_password de db_main para compatibilidad
    from db_main import Database
    db_sync = Database()
    expected_hash = db_sync.hash_password(login_data.username, login_data.password)
    
    if user.hashed_password != expected_hash:
        logger.warning(f"Intento de login fallido: contraseña incorrecta para {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Crear token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    # Actualizar último login
    await app_state.db.update_last_login(user.id, db)
    
    logger.info(f"Login exitoso para usuario {login_data.username}")
    
    return Token(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@app.get("/users/me", tags=["users"])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obtiene información del usuario autenticado actual.
    
    Parameters
    ----------
    current_user : User
        Usuario autenticado obtenido del token
        
    Returns
    -------
    dict
        Información del usuario
    """
    return {
        "id": current_user.id,
        "uuid": current_user.uuid,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Iniciando servidor en {SERVER_HOST}:{SERVER_PORT}")
    
    uvicorn.run(
        "main:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,
        log_level="info"
    )
