# MensajeriaApp

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
