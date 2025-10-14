# Sistema de Mensajería Segura

Aplicación de mensajería con almacenamiento encriptado, persistencia entre sesiones y animaciones fluidas.

## 🔒 Características de Seguridad

### Encriptación de Mensajes
- **AES-256-GCM**: Estándar de encriptación rápido y seguro (recomendado)
- **ChaCha20-Poly1305**: Alternativa moderna con excelente rendimiento
- **RSA-OAEP**: Máxima seguridad para mensajes cortos
- Encriptación autenticada con protección contra manipulación

### Gestión de Claves
- Derivación segura de claves con PBKDF2-HMAC-SHA256 (100,000 iteraciones)
- Salts únicos por mensaje para máxima seguridad
- Nonces aleatorios para prevenir ataques de repetición
- Gestión automática de pares de claves RSA por chat

### Privacidad
- Auto-destrucción configurable de mensajes (1 hora a 30 días)
- Opción de ocultar chats sin eliminarlos
- Contraseñas hasheadas con scrypt
- Contenido encriptado en base de datos

## 📦 Arquitectura del Sistema

### Módulos Principales

#### `crypto_manager.py`
- Clase `CryptoManager`: Gestiona todas las operaciones criptográficas
- Soporte para múltiples algoritmos de encriptación
- Derivación segura de claves y gestión de pares RSA

#### `db_main.py`
- Modelos: `User`, `Chat`, `Message`
- Clase `Database`: Operaciones CRUD completas
- Persistencia de mensajes encriptados y metadatos
- Gestión de configuración por chat

#### `chat_manager.py`
- Clase `ChatManager`: Interfaz de alto nivel para chats
- Caché LRU para optimizar rendimiento
- Sincronización eficiente con base de datos
- Gestión automática de encriptación/desencriptación

#### `animations.py`
- Clase `ChatAnimations`: Transiciones suaves
- Efectos: fade in/out, slide, scale
- Animaciones combinadas para mejor UX

#### `mainui.py`
- Interfaz principal con PyQt6
- Integración completa de persistencia y encriptación
- Diálogos de configuración de seguridad
- Animaciones en cambios de chat

## 🚀 Instalación

```powershell
# Instalar dependencias
pip install -r requirements.txt
```

### Dependencias
- **PyQt6** >= 6.5: Framework de interfaz gráfica
- **SQLAlchemy** >= 2.0: ORM para base de datos
- **cryptography** >= 41.0: Biblioteca criptográfica

## 💻 Uso

### Iniciar la Aplicación
```powershell
python mainui.py
```

### Funcionalidades Principales

#### Enviar Mensajes
1. Selecciona un contacto de la lista
2. Escribe tu mensaje
3. Presiona Enter o haz clic en "Enviar"
4. El mensaje se encripta automáticamente antes de guardarse

#### Configurar Seguridad del Chat
1. Selecciona un chat activo
2. Haz clic en "🔒 Seguridad"
3. Elige el tipo de encriptación
4. Configura auto-destrucción (opcional)
5. Guarda los cambios

#### Ocultar Chats
1. Selecciona un chat
2. Haz clic en "👁 Ocultar"
3. Confirma la acción
4. El chat desaparece de la lista (recuperable desde configuración)

## 🔧 Configuración

### Base de Datos
Por defecto usa SQLite (`mensajeria.db`). Para usar otro motor:

```python
db = Database(db_url="postgresql://user:pass@localhost/dbname")
```

### Caché de Mensajes
Configurable al inicializar `ChatManager`:

```python
chat_manager = ChatManager(database, cache_size=100)  # Mantiene 100 chats en caché
```

### Auto-destrucción
Configurar desde el diálogo de seguridad o programáticamente:

```python
chat_manager.create_or_get_chat(
    user1_id=1,
    user2_id=2,
    auto_delete_hours=24  # Mensajes se eliminan tras 24 horas
)
```

## 🏗️ Arquitectura de Seguridad

### Flujo de Encriptación

```
Mensaje plano → Derivación de clave (PBKDF2)
              → Generación de nonce/salt
              → Encriptación (AES/ChaCha20/RSA)
              → Tag de autenticación
              → Base64 + JSON
              → Almacenamiento en DB
```

### Flujo de Desencriptación

```
DB → Base64 decode
   → Extracción de metadata (salt, nonce)
   → Derivación de clave
   → Verificación de tag
   → Desencriptación
   → Mensaje plano
```

## 📊 Optimizaciones de Rendimiento

### Caché LRU
- Mantiene en memoria los chats más recientes
- Límite configurable de chats y mensajes
- Invalidación automática tras cambios

### Carga Perezosa
- Los mensajes se cargan bajo demanda
- Paginación opcional para chats grandes
- Consultas optimizadas con índices

### Limpieza Automática
```python
# Eliminar mensajes expirados
deleted_count = chat_manager.cleanup_expired_messages()
```

## 🛡️ Mejores Prácticas de Seguridad

1. **Contraseñas Fuertes**: Usa contraseñas complejas de al menos 12 caracteres
2. **Cambio Regular**: Considera cambiar el tipo de encriptación periódicamente
3. **Auto-destrucción**: Activa para mensajes sensibles
4. **Actualizaciones**: Mantén las dependencias criptográficas actualizadas
5. **Backups**: Respalda la base de datos de forma encriptada

## 📝 Ejemplo de Uso Completo

```python
from db_main import Database
from chat_manager import ChatManager
from crypto_manager import EncryptionType

# Inicializar
db = Database()
chat_manager = ChatManager(db)

# Configurar usuario
chat_manager.set_current_user(user_id=1, password="mi_password_seguro")

# Crear chat con encriptación AES
chat = chat_manager.create_or_get_chat(
    user1_id=1,
    user2_id=2,
    encryption_type="AES-256-GCM",
    auto_delete_hours=48
)

# Enviar mensaje encriptado
chat_manager.send_message(
    chat_id=chat.id,
    sender_id=1,
    message="Hola, este mensaje está encriptado",
    password="mi_password_seguro"
)

# Leer mensajes desencriptados
messages = chat_manager.get_messages(
    chat_id=chat.id,
    password="mi_password_seguro"
)

for msg, decrypted_text in messages:
    print(f"{msg.timestamp}: {decrypted_text}")
```

## 🐛 Resolución de Problemas

### Error: "No se pudo desencriptar el mensaje"
- Verifica que la contraseña sea correcta
- Comprueba que el tipo de encriptación coincida
- Revisa que la base de datos no esté corrupta

### Performance lenta con muchos mensajes
- Aumenta el tamaño de caché
- Usa paginación en consultas grandes
- Considera limpiar mensajes antiguos

### Mensajes no persisten entre sesiones
- Verifica que la base de datos se guarde correctamente
- Comprueba permisos de escritura en el directorio
- Revisa logs en `logger_main.py`

## 📄 Licencia

Este proyecto es un ejemplo educativo de sistemas de mensajería seguros.

## 🤝 Contribuciones

Mejoras sugeridas:
- Implementar intercambio de claves Diffie-Hellman
- Añadir soporte para mensajes multimedia encriptados
- Implementar verificación de identidad (Perfect Forward Secrecy)
- Añadir auditoría de seguridad completa

---

**Nota de Seguridad**: Este es un proyecto educativo. Para producción, considera auditorías de seguridad profesionales y pruebas de penetración.


Interfaz de chat en PyQt6 con panel de amigos, diálogo para agregar amigos por UUID, configuración básica (tema claro/oscuro, nombre a mostrar y notificaciones) y barra de menús.

## Requisitos

- Python 3.8+
- PyQt6

Instalación de dependencias:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ejecutar

```powershell
python .\mainui.py
```

## Atajos

- Ctrl+N: Nuevo chat (foco en la caja de mensaje)
- Ctrl+Shift+A: Agregar amigo…
- Ctrl+Q: Salir
- Ctrl+C / Ctrl+V: Copiar / Pegar en la caja de mensaje

## Notas

- El diálogo "Agregar amigo" devuelve el texto del UUID introducido y actualmente lo añade como un item nuevo a la lista de amigos. Puedes interceptarlo en `_open_add_friend`.
- La configuración aplica un tema claro/oscuro mediante estilos; amplía `_apply_theme` si necesitas más personalización.
