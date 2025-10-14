import sys
from typing import Literal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence, QColor
from PyQt6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,
                             QHBoxLayout,QSplitter,QListWidget,QListWidgetItem,
                             QLineEdit,QPushButton,QLabel,QMenuBar,QMessageBox,
                             QDialog,QDialogButtonBox,QFormLayout,QComboBox,QCheckBox,
                             QFileDialog, QSpinBox, QColorDialog)


class ChatConfigDialog(QDialog):
    """Diálogo para configurar opciones de seguridad de un chat individual."""

    def __init__(self, current_config: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Seguridad del Chat")
        self.setMinimumWidth(500)
        self._result_config = {}

        # Tipo de encriptación
        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems([
            "AES-256-GCM",
            "ChaCha20-Poly1305",
            "RSA-OAEP",
            "Sin encriptación"
        ])

        # Auto-destrucción de mensajes
        self.auto_delete_enabled = QCheckBox("Activar auto-destrucción")
        self.auto_delete_hours = QSpinBox()
        self.auto_delete_hours.setRange(1, 720)  # 1 hora a 30 días
        self.auto_delete_hours.setValue(24)
        self.auto_delete_hours.setSuffix(" horas")
        self.auto_delete_hours.setEnabled(False)

        self.auto_delete_enabled.toggled.connect(self.auto_delete_hours.setEnabled)

        # Colores personalizables
        self.my_message_color = QColor("#DCF8C6")  # Verde WhatsApp por defecto
        self.their_message_color = QColor("#FFFFFF")  # Blanco por defecto
        
        self.my_color_button = QPushButton("Seleccionar color")
        self.my_color_button.clicked.connect(self._select_my_color)
        self._update_color_button(self.my_color_button, self.my_message_color)
        
        self.their_color_button = QPushButton("Seleccionar color")
        self.their_color_button.clicked.connect(self._select_their_color)
        self._update_color_button(self.their_color_button, self.their_message_color)

        # Cargar configuración actual si existe
        if current_config:
            enc_type = current_config.get("encryption_type", "AES-256-GCM")
            idx = self.encryption_combo.findText(enc_type)
            if idx >= 0:
                self.encryption_combo.setCurrentIndex(idx)

            auto_hours = current_config.get("auto_delete_hours")
            if auto_hours:
                self.auto_delete_enabled.setChecked(True)
                self.auto_delete_hours.setValue(auto_hours)
            
            # Cargar colores si existen
            my_color = current_config.get("my_message_color", "#DCF8C6")
            their_color = current_config.get("their_message_color", "#FFFFFF")
            self.my_message_color = QColor(my_color)
            self.their_message_color = QColor(their_color)
            self._update_color_button(self.my_color_button, self.my_message_color)
            self._update_color_button(self.their_color_button, self.their_message_color)

        # Descripción de seguridad
        self.security_info = QLabel(
            "<b>Información de Seguridad:</b><br>"
            "• <b>AES-256-GCM:</b> Estándar de encriptación rápido y seguro (recomendado)<br>"
            "• <b>ChaCha20-Poly1305:</b> Alternativa moderna, excelente rendimiento<br>"
            "• <b>RSA-OAEP:</b> Máxima seguridad para mensajes cortos<br>"
            "• <b>Sin encriptación:</b> Solo para pruebas (NO recomendado)"
        )
        self.security_info.setWordWrap(True)
        self.security_info.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")

        form = QFormLayout()
        form.addRow("Tipo de encriptación:", self.encryption_combo)
        form.addRow("", self.auto_delete_enabled)
        form.addRow("Tiempo de auto-destrucción:", self.auto_delete_hours)
        form.addRow("", QLabel("<br><b>Personalización de Colores:</b>"))
        form.addRow("Color de tus mensajes:", self.my_color_button)
        form.addRow("Color de mensajes recibidos:", self.their_color_button)
        form.addRow("", self.security_info)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _update_color_button(self, button: QPushButton, color: QColor):
        """Actualiza el estilo del botón para mostrar el color seleccionado."""
        button.setStyleSheet(
            f"QPushButton {{ background-color: {color.name()}; "
            f"color: {'black' if color.lightness() > 128 else 'white'}; "
            f"border: 2px solid #888; padding: 5px; }}"
        )
        button.setText(f"  {color.name()}  ")
    
    def _select_my_color(self):
        """Abre el diálogo de selección de color para los mensajes propios."""
        color = QColorDialog.getColor(self.my_message_color, self, "Selecciona el color de tus mensajes")
        if color.isValid():
            self.my_message_color = color
            self._update_color_button(self.my_color_button, color)
    
    def _select_their_color(self):
        """Abre el diálogo de selección de color para los mensajes recibidos."""
        color = QColorDialog.getColor(self.their_message_color, self, "Selecciona el color de los mensajes recibidos")
        if color.isValid():
            self.their_message_color = color
            self._update_color_button(self.their_color_button, color)

    def _on_accept(self):
        self._result_config = {
            "encryption_type": self.encryption_combo.currentText(),
            "auto_delete_hours": self.auto_delete_hours.value()
            if self.auto_delete_enabled.isChecked()
            else None,
            "my_message_color": self.my_message_color.name(),
            "their_message_color": self.their_message_color.name(),
        }
        self.accept()

    def get_config(self) -> dict:
        return self._result_config


class AddFriendDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar amigo por UUID")
        self.uuid_input = QLineEdit()
        self.uuid_input.setPlaceholderText("Introduce el UUID del amigo")
        self.search_button = QPushButton("Buscar")
        self.search_button.clicked.connect(self.get_uuid)

        form = QFormLayout()
        form.addRow("UUID:", self.uuid_input)
        form.addRow("", self.search_button)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_uuid(self) -> str:
        return self.uuid_input.text().strip()


class SettingsDialog(QDialog):
    def __init__(self, current_settings: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self._result_settings = {}

        self.display_name = QLineEdit()
        self.theme = QComboBox()
        self.theme.addItems(["Claro", "Oscuro"])
        self.notifications = QCheckBox("Habilitar notificaciones")

        if current_settings:
            self.display_name.setText(current_settings.get("display_name", ""))
            theme = current_settings.get("theme", "Claro")
            idx = self.theme.findText(theme)
            if idx >= 0:
                self.theme.setCurrentIndex(idx)
            self.notifications.setChecked(bool(current_settings.get("notifications", True)))

        form = QFormLayout()
        form.addRow("Nombre a mostrar:", self.display_name)
        form.addRow("Tema:", self.theme)
        form.addRow("", self.notifications)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Apply | QDialogButtonBox.StandardButton.RestoreDefaults)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_accept)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._restore_defaults)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def _on_accept(self):
        self._result_settings = {
            "display_name": self.display_name.text().strip(),
            "theme": self.theme.currentText(),
            "notifications": self.notifications.isChecked(),
        }
        self.accept()
        
    def _restore_defaults(self):
        self.display_name.setText("")
        self.theme.setCurrentIndex(0)  # Claro
        self.notifications.setChecked(True)

    def get_settings(self) -> dict:
        return self._result_settings

class RegisterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registro de nuevo usuario")
        self.username_input = QLineEdit()
        self.email_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.profile_picture_input = QWidget()
        picture_layout = QHBoxLayout(self.profile_picture_input)
        picture_layout.setContentsMargins(0, 0, 0, 0)
        picture_layout.setSpacing(6)
        self.profile_picture_path = QLineEdit()
        self.profile_picture_path.setPlaceholderText("Selecciona una imagen de perfil…")
        self.profile_picture_path.setReadOnly(True)
        self.profile_picture_button = QPushButton("Examinar…")
        self.profile_picture_button.clicked.connect(self._select_profile_picture)
        picture_layout.addWidget(self.profile_picture_path, 1)
        picture_layout.addWidget(self.profile_picture_button)
        self.phone_number_input = QLineEdit()

        form = QFormLayout()
        form.addRow("Nombre de usuario:", self.username_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Contraseña:", self.password_input)
        form.addRow("Foto de perfil:", self.profile_picture_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_user_data(self) -> dict:
        return {
            "username": self.username_input.text().strip(),
            "email": self.email_input.text().strip(),
            "password": self.password_input.text(),
            "profile_picture": self.profile_picture_path.text().strip(),
        }

    def _select_profile_picture(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen de perfil",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif)",
        )
        if file_path:
            self.profile_picture_path.setText(file_path)

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Iniciar sesión")
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form = QFormLayout()
        form.addRow("Nombre de usuario:", self.username_input)
        form.addRow("Contraseña:", self.password_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_credentials(self) -> dict:
        return {
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
        }
        
    def accept(self) -> None:
        if not self.username_input.text().strip() or not self.password_input.text():
            QMessageBox.warning(self, "Error", "Por favor, introduce nombre de usuario y contraseña.")
            return
        super().accept()
        

class chatWindow(QMainWindow):
    def __init__(self, authenticated_user=None, user_password=None, *args):
        super(chatWindow, self).__init__(*args)
        self.setWindowTitle("Mensajería Segura")
        self.resize(900, 600)

        # Importar módulos necesarios
        from animations import ChatAnimations
        from chat_manager import ChatManager
        from db_main import Database
        from bot_assistant import ConversationalBot

        # Inicializar base de datos y gestor de chats
        self.db = Database()
        self.chat_manager = ChatManager(self.db)
        self.animations = ChatAnimations
        self.bot = ConversationalBot(self.db)

        # Estado de la aplicación (ahora recibe usuario autenticado)
        self.current_user = authenticated_user
        self.current_user_id: int | None = authenticated_user.id if authenticated_user else None
        self.current_user_password: str = user_password or ""
        self.current_chat_id: int | None = None
        self.current_chat_partner_name: str = ""  # Nombre del contacto actual
        self.chat_data: dict = {}  # chat_id -> datos del chat
        self.bot_user_id: int | None = None  # ID del bot

        self.settings = {
            "display_name": authenticated_user.username if authenticated_user else "",
            "theme": "Claro",
            "notifications": True,
        }

        self._create_menu_bar()
        self._create_main_layout()
        self._apply_theme()

        # Inicializar bot y cargar chats
        if self.current_user_id:
            self._initialize_user_session()

    def _create_menu_bar(self):
        menubar: QMenuBar = self.menuBar()

        archivo = menubar.addMenu("Archivo")
        self.act_nuevo_chat = QAction("Nuevo chat", self)
        self.act_nuevo_chat.setShortcut(QKeySequence.StandardKey.New)
        self.act_agregar_amigo = QAction("Agregar amigo…", self)
        self.act_agregar_amigo.setShortcut(QKeySequence("Ctrl+Shift+A"))
        self.act_salir = QAction("Salir", self)
        self.act_salir.setShortcut(QKeySequence.StandardKey.Quit)
        archivo.addAction(self.act_nuevo_chat)
        archivo.addAction(self.act_agregar_amigo)
        archivo.addSeparator()
        archivo.addAction(self.act_salir)

        edicion = menubar.addMenu("Edición")
        self.act_copiar = QAction("Copiar", self)
        self.act_copiar.setShortcut(QKeySequence.StandardKey.Copy)
        self.act_pegar = QAction("Pegar", self)
        self.act_pegar.setShortcut(QKeySequence.StandardKey.Paste)
        self.act_limpiar_chat = QAction("Limpiar chat", self)
        edicion.addAction(self.act_copiar)
        edicion.addAction(self.act_pegar)
        edicion.addSeparator()
        edicion.addAction(self.act_limpiar_chat)

        ver = menubar.addMenu("Ver")
        self.act_toggle_amigos = QAction("Mostrar lista de amigos", self, checkable=True)
        self.act_toggle_amigos.setChecked(True)
        ver.addAction(self.act_toggle_amigos)

        ayuda = menubar.addMenu("Ayuda")
        self.act_acerca_de = QAction("Acerca de", self)
        ayuda.addAction(self.act_acerca_de)

        self.act_nuevo_chat.triggered.connect(self._focus_message_input)
        self.act_agregar_amigo.triggered.connect(self._open_add_friend)
        self.act_salir.triggered.connect(QApplication.instance().quit)
        self.act_copiar.triggered.connect(self._copy_from_input)
        self.act_pegar.triggered.connect(self._paste_to_input)
        self.act_limpiar_chat.triggered.connect(self._clear_chat)
        self.act_toggle_amigos.triggered.connect(self._toggle_friends_panel)
        self.act_acerca_de.triggered.connect(self._show_about)

    def _initialize_user_session(self):
        """Inicializa la sesión del usuario: bot, chats y mensaje de bienvenida."""
        try:
            # Asegurar que el bot existe y crear chat si es necesario
            self.bot_user_id = self.bot.ensure_bot_exists()
            
            # Verificar si es la primera vez del usuario (no tiene chats con el bot)
            bot_chat_id = self.bot.ensure_chat_with_user(
                self.current_user_id, self.chat_manager
            )
            
            # Verificar si hay mensajes en el chat con el bot
            messages = self.chat_manager.get_messages(
                bot_chat_id, "bot_internal_password", limit=1
            )
            
            # Si no hay mensajes, enviar bienvenida
            if not messages:
                self.bot.send_welcome_message(
                    self.current_user_id,
                    self.chat_manager,
                    self.current_user.username,
                )
            
            # Configurar gestor de chats con usuario actual
            self.chat_manager.set_current_user(
                self.current_user_id, self.current_user_password
            )
            
            # Cargar lista de chats
            self._load_user_chats()
            
        except Exception as e:
            print(f"Error inicializando sesión de usuario: {e}")
            QMessageBox.warning(
                self,
                "Error de Inicialización",
                f"Hubo un problema al inicializar tu sesión:\n{e}\n\n"
                "La aplicación puede no funcionar correctamente.",
            )

    def _create_main_layout(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel izquierdo: amigos
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.search_friend = QLineEdit()
        self.search_friend.setPlaceholderText("Buscar amigo…")
        self.search_friend.textChanged.connect(self._filter_friends)
        self.friends_list = QListWidget()
        self.friends_list.itemSelectionChanged.connect(self._on_friend_selected)
        self.btn_add_friend = QPushButton("Agregar amigo")
        self.btn_add_friend.clicked.connect(self._open_add_friend)
        left_layout.addWidget(self.search_friend)
        left_layout.addWidget(self.friends_list, 1)
        left_layout.addWidget(self.btn_add_friend)

        # Panel derecho: chat
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)

        top_bar = QHBoxLayout()
        self.current_chat_label = QLabel("Selecciona un contacto")
        top_bar.addWidget(self.current_chat_label)
        top_bar.addStretch(1)
        self.btn_chat_config = QPushButton("🔒 Seguridad")
        self.btn_chat_config.clicked.connect(self._open_chat_config)
        self.btn_chat_config.setVisible(False)  # Oculto hasta seleccionar chat
        top_bar.addWidget(self.btn_chat_config)
        self.btn_hide_chat = QPushButton("👁 Ocultar")
        self.btn_hide_chat.clicked.connect(self._hide_current_chat)
        self.btn_hide_chat.setVisible(False)
        top_bar.addWidget(self.btn_hide_chat)
        self.btn_settings = QPushButton("⚙ Config")
        self.btn_settings.clicked.connect(self._open_settings)
        top_bar.addWidget(self.btn_settings)
        right_layout.addLayout(top_bar)

        self.messages_view = QListWidget()
        right_layout.addWidget(self.messages_view, 1)

        input_bar = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Escribe un mensaje…")
        self.message_input.returnPressed.connect(self._send_message)
        self.btn_send = QPushButton("Enviar")
        self.btn_send.clicked.connect(self._send_message)
        input_bar.addWidget(self.message_input, 1)
        input_bar.addWidget(self.btn_send)
        right_layout.addLayout(input_bar)

        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([250, 650])

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.addWidget(splitter)
        self.setCentralWidget(container)

    # Acciones del menú
    def _focus_message_input(self):
        self.message_input.setFocus()

    def _copy_from_input(self):
        self.message_input.copy()

    def _paste_to_input(self):
        self.message_input.paste()

    def _clear_chat(self):
        self.messages_view.clear()

    def _toggle_friends_panel(self, checked: bool):
        self.left_panel.setVisible(checked)

    def _show_about(self):
        QMessageBox.information(
            self,
            "Acerca de",
            "Mensajería UI de ejemplo\nConstruida con PyQt5",
        )

    # Lógica de amigos
    def _open_add_friend(self):
        dialog = AddFriendDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            uuid_text = dialog.get_uuid()
            if uuid_text:
                # Por ahora, añadimos una entrada temporal a la lista.
                QListWidgetItem(f"Nuevo ({uuid_text})", self.friends_list)
                # Aquí podrás manejar el UUID como necesites más adelante.

    def _filter_friends(self, text: str):
        text = text.lower()
        for i in range(self.friends_list.count()):
            item = self.friends_list.item(i)
            item.setHidden(text not in item.text().lower())

    def _on_friend_selected(self):
        """Carga el chat con animación cuando se selecciona un amigo."""
        items = self.friends_list.selectedItems()
        if not items:
            return
        
        # Obtener el chat ID almacenado en el item
        chat_id = items[0].data(Qt.ItemDataRole.UserRole)
        
        print(f"DEBUG: chat_id obtenido del item: {chat_id}")
        print(f"DEBUG: chat_data keys: {list(self.chat_data.keys())}")
        
        if not chat_id or chat_id not in self.chat_data:
            print(f"DEBUG: Chat ID no encontrado o no está en chat_data")
            QMessageBox.warning(self, "Error", "No se pudo cargar el chat seleccionado.")
            return
        
        chat = self.chat_data[chat_id]
        
        # Obtener el nombre del otro usuario
        other_user_id = (
            chat.user2_id if chat.user1_id == self.current_user_id else chat.user1_id
        )
        
        print(f"DEBUG: other_user_id: {other_user_id}")
        
        # Obtener información del otro usuario
        session = self.db.get_session()
        from db_main import User
        other_user = session.get(User, other_user_id)
        session.close()
        
        friend_name = other_user.username if other_user else f"Usuario {other_user_id}"
        
        print(f"DEBUG: friend_name: {friend_name}")

        try:
            # Cargar mensajes directamente (sin animación para debug)
            self._load_chat_messages(chat_id, friend_name)

        except Exception as e:
            print(f"DEBUG: Error en animación: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando chat: {e}")

    def _load_chat_messages(self, chat_id: int, friend_name: str):
        """Carga los mensajes del chat seleccionado."""
        print(f"DEBUG _load_chat_messages: Iniciando con chat_id={chat_id}, friend_name={friend_name}")
        
        # Remover cualquier efecto de opacidad previo
        self.messages_view.setGraphicsEffect(None)
        
        self.current_chat_id = chat_id
        self.current_chat_partner_name = friend_name
        self.current_chat_label.setText(friend_name)
        self.btn_chat_config.setVisible(True)
        self.btn_hide_chat.setVisible(True)

        # Limpiar vista de mensajes
        self.messages_view.clear()

        try:
            print(f"DEBUG: Verificando si chat_id {chat_id} está en chat_data")
            # Determinar si es el chat con el bot
            is_bot_chat = False
            if chat_id in self.chat_data:
                print(f"DEBUG: Chat encontrado en chat_data")
                chat = self.chat_data[chat_id]
                is_bot_chat = (chat.user1_id == self.bot_user_id or 
                              chat.user2_id == self.bot_user_id)
                print(f"DEBUG: is_bot_chat={is_bot_chat}")

            # Cargar mensajes
            if chat_id in self.chat_data:
                chat = self.chat_data[chat_id]
                
                # Obtener colores personalizados del chat
                my_color = QColor(chat.my_message_color if hasattr(chat, 'my_message_color') else "#DCF8C6")
                their_color = QColor(chat.their_message_color if hasattr(chat, 'their_message_color') else "#FFFFFF")
                
                # Usar contraseña del bot si es chat con bot
                password = "bot_internal_password" if is_bot_chat else self.current_user_password
                
                print(f"DEBUG: Obteniendo mensajes con password={'bot_internal_password' if is_bot_chat else 'user_password'}")
                messages = self.chat_manager.get_messages(chat_id, password)
                print(f"DEBUG: Número de mensajes obtenidos: {len(messages) if messages else 0}")
                
                if messages:
                    for msg, decrypted_text in messages:
                        # Determinar quién envió el mensaje
                        if msg.sender_id == self.current_user_id:
                            sender_prefix = "Tú"
                            bg_color = my_color
                        elif msg.sender_id == self.bot_user_id:
                            sender_prefix = "🤖 Bot"
                            bg_color = their_color
                        else:
                            sender_prefix = friend_name
                            bg_color = their_color
                        
                        item = QListWidgetItem(
                            f"{sender_prefix}: {decrypted_text}", self.messages_view
                        )
                        
                        # Aplicar color de fondo personalizado
                        item.setBackground(bg_color)
                else:
                    QListWidgetItem(
                        f"Comienza una conversación con {friend_name}", self.messages_view
                    )
            else:
                QListWidgetItem(
                    f"Comienza una conversación con {friend_name}", self.messages_view
                )

        except Exception as e:
            print(f"DEBUG: Exception en _load_chat_messages: {e}")
            import traceback
            traceback.print_exc()
            QListWidgetItem(f"[Error cargando mensajes: {e}]", self.messages_view)

        # Asegurarse de que el widget sea visible sin efectos de opacidad
        print(f"DEBUG: Haciendo visible messages_view")
        self.messages_view.setVisible(True)
        self.messages_view.scrollToBottom()
        print(f"DEBUG: _load_chat_messages finalizado")

    # Chat
    def _send_message(self):
        """Envía un mensaje encriptado al chat actual."""
        msg = self.message_input.text().strip()
        if not msg or not self.current_chat_id:
            return

        try:
            # Determinar si es el chat con el bot
            is_bot_chat = False
            if self.current_chat_id in self.chat_data:
                chat = self.chat_data[self.current_chat_id]
                is_bot_chat = (chat.user1_id == self.bot_user_id or 
                              chat.user2_id == self.bot_user_id)

            # Guardar mensaje encriptado en base de datos
            self.chat_manager.send_message(
                chat_id=self.current_chat_id,
                sender_id=self.current_user_id,
                message=msg,
                password=self.current_user_password,
            )

            # Obtener color personalizado para mensajes propios
            my_color = QColor("#DCF8C6")  # Color por defecto
            if self.current_chat_id in self.chat_data:
                chat = self.chat_data[self.current_chat_id]
                my_color = QColor(chat.my_message_color if hasattr(chat, 'my_message_color') else "#DCF8C6")

            # Añadir a la vista con color personalizado
            item = QListWidgetItem(f"Tú: {msg}", self.messages_view)
            item.setBackground(my_color)
            self.message_input.clear()
            self.messages_view.scrollToBottom()

            # Si es chat con bot, generar respuesta automática
            if is_bot_chat:
                # Pequeño delay para simular "escritura" del bot
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(800, lambda: self._handle_bot_response(msg))

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error enviando mensaje: {e}")
    
    def _handle_bot_response(self, user_message: str):
        """Maneja la respuesta automática del bot."""
        try:
            response = self.bot.handle_user_message(
                message=user_message,
                user_id=self.current_user_id,
                chat_id=self.current_chat_id,
                chat_manager=self.chat_manager,
            )
            
            if response:
                # Obtener color personalizado para mensajes recibidos
                their_color = QColor("#FFFFFF")  # Color por defecto
                if self.current_chat_id in self.chat_data:
                    chat = self.chat_data[self.current_chat_id]
                    their_color = QColor(chat.their_message_color if hasattr(chat, 'their_message_color') else "#FFFFFF")
                
                # Añadir respuesta del bot a la vista
                item = QListWidgetItem(f"🤖 Bot: {response}", self.messages_view)
                item.setBackground(their_color)
                self.messages_view.scrollToBottom()
                
        except Exception as e:
            print(f"Error en respuesta del bot: {e}")

    # Configuración
    def _open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
                new_settings = dlg.get_settings()
                if new_settings:
                    self.settings.update(new_settings)
                    self._apply_theme()

    def _apply_theme(self):
        if self.settings.get("theme") == "Oscuro":
            self._set_theme('dark')
        else:
            self._set_theme('light')

    def _set_theme(self, theme: Literal['light', 'dark']):
        # Estilos simples para tema oscuro
        if theme=='dark':
            self.setStyleSheet(
                """
                QWidget { background-color: #232629; color: #e8e6e3; }
                QLineEdit, QTextEdit, QListWidget { background-color: #2b2f33; color: #e8e6e3; border: 1px solid #3a3f44; }
                QPushButton { background-color: #3a3f44; border: 1px solid #4a4f55; padding: 6px 10px; }
                QPushButton:hover { background-color: #4a4f55; }
                QMenuBar { background-color: #2b2f33; }
                QMenu { background-color: #2b2f33; }
                """
            )
        elif theme=='light':
            self.setStyleSheet("")

    def _load_user_chats(self):
        """Carga la lista de chats del usuario actual."""
        if not self.current_user_id:
            return

        try:
            chats = self.chat_manager.get_user_chats(self.current_user_id)
            print(f"DEBUG: Número de chats encontrados: {len(chats)}")
            self.friends_list.clear()

            for chat in chats:
                print(f"DEBUG: Procesando chat ID: {chat.id}")
                # Determinar el nombre del otro usuario en el chat
                other_user_id = (
                    chat.user2_id if chat.user1_id == self.current_user_id else chat.user1_id
                )
                
                print(f"DEBUG: other_user_id: {other_user_id}, bot_user_id: {self.bot_user_id}")
                
                # Obtener información del otro usuario
                session = self.db.get_session()
                from db_main import User
                other_user = session.get(User, other_user_id)
                session.close()
                
                if other_user:
                    # Marcar el bot con emoji
                    if other_user.id == self.bot_user_id:
                        display_name = f"🤖 {other_user.username}"
                    else:
                        display_name = other_user.username
                else:
                    display_name = f"Usuario {other_user_id}"

                print(f"DEBUG: display_name: {display_name}")
                
                item = QListWidgetItem(display_name, self.friends_list)
                
                # Guardar el chat ID en el item para recuperarlo después
                item.setData(Qt.ItemDataRole.UserRole, chat.id)
                print(f"DEBUG: Guardado chat.id en item: {chat.id}")
                
                # Destacar el chat con el bot
                if other_user and other_user.id == self.bot_user_id:
                    from PyQt6.QtGui import QFont
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                    item.setBackground(Qt.GlobalColor.cyan)
                
                # Guardar referencia al chat
                self.chat_data[chat.id] = chat

        except Exception as e:
            print(f"Error cargando chats: {e}")
            QMessageBox.warning(
                self, "Error", f"Error cargando tus chats:\n{e}"
            )

    def _open_chat_config(self):
        """Abre el diálogo de configuración de seguridad del chat actual."""
        if not self.current_chat_id:
            return

        try:
            chat_info = self.chat_manager.get_chat_info(self.current_chat_id)
            current_config = {
                "encryption_type": chat_info.get("encryption_type", "AES-256-GCM"),
                "auto_delete_hours": chat_info.get("auto_delete_hours"),
                "my_message_color": chat_info.get("my_message_color", "#DCF8C6"),
                "their_message_color": chat_info.get("their_message_color", "#FFFFFF"),
            }

            dlg = ChatConfigDialog(current_config, self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                new_config = dlg.get_config()
                if new_config:
                    # Actualizar configuración de encriptación
                    if new_config["encryption_type"] != current_config["encryption_type"]:
                        reply = QMessageBox.question(
                            self,
                            "Cambiar Encriptación",
                            "¿Deseas cambiar el tipo de encriptación? "
                            "Esto re-encriptará todos los mensajes (puede tardar un momento).",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            self.chat_manager.update_encryption(
                                chat_id=self.current_chat_id,
                                new_encryption_type=new_config["encryption_type"],
                                password=self.current_user_password,
                                new_password=self.current_user_password,
                            )
                            QMessageBox.information(
                                self, "Éxito", "Encriptación actualizada correctamente"
                            )
                    
                    # Actualizar colores del chat
                    if (new_config["my_message_color"] != current_config["my_message_color"] or
                        new_config["their_message_color"] != current_config["their_message_color"]):
                        self.db.update_chat_colors(
                            chat_id=self.current_chat_id,
                            my_color=new_config["my_message_color"],
                            their_color=new_config["their_message_color"]
                        )
                        # Recargar mensajes para aplicar nuevos colores
                        self._load_chat_messages(self.current_chat_id, self.current_chat_partner_name)
                        QMessageBox.information(
                            self, "Éxito", "Colores actualizados correctamente"
                        )

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error configurando chat: {e}")

    def _hide_current_chat(self):
        """Oculta el chat actual de la lista."""
        if not self.current_chat_id or not self.current_user_id:
            return

        try:
            reply = QMessageBox.question(
                self,
                "Ocultar Chat",
                "¿Deseas ocultar este chat? Podrás verlo de nuevo desde configuración.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.chat_manager.hide_chat(self.current_chat_id, self.current_user_id)
                
                # Animar salida del panel de chat
                slide_out_anim = self.animations.slide_out_to_right(
                    self.messages_view, duration=400, distance=300
                )
                slide_out_anim.finished.connect(self._finish_hide_chat)
                slide_out_anim.start()

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error ocultando chat: {e}")

    def _finish_hide_chat(self):
        """Completa el proceso de ocultar chat tras la animación."""
        self.messages_view.clear()
        self.current_chat_label.setText("Selecciona un contacto")
        self.btn_chat_config.setVisible(False)
        self.btn_hide_chat.setVisible(False)
        self.current_chat_id = None
        self._load_user_chats()

        # Restaurar visibilidad del panel
        fade_in_anim = self.animations.fade_in(self.messages_view, duration=300)
        fade_in_anim.start()
            
    # def _save_
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Mostrar ventana de login primero
    from login_window import LoginWindow
    from db_main import Database
    
    db = Database()
    login = LoginWindow(db)
    
    if login.exec() == QDialog.DialogCode.Accepted:
        # Obtener usuario autenticado
        auth_data = login.get_authenticated_user()
        if auth_data:
            user, password = auth_data
            
            # Crear ventana principal con usuario autenticado
            window = chatWindow(authenticated_user=user, user_password=password)
            window.show()
            sys.exit(app.exec())
    
    # Si el login fue cancelado, cerrar aplicación
    sys.exit(0)