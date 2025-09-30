import sys
from typing import Literal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,
                             QHBoxLayout,QSplitter,QListWidget,QListWidgetItem,
                             QLineEdit,QPushButton,QLabel,QMenuBar,QMessageBox,
                             QDialog,QDialogButtonBox,QFormLayout,QComboBox,QCheckBox,
                             QFileDialog)


class AddFriendDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar amigo por UUID")
        self.uuid_input = QLineEdit()
        self.uuid_input.setPlaceholderText("Introduce el UUID del amigo")

        form = QFormLayout()
        form.addRow("UUID:", self.uuid_input)

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


class chatWindow(QMainWindow):
    def __init__(self, *args):
        super(chatWindow, self).__init__(*args)
        self.setWindowTitle("Mensajería")
        self.resize(900, 600)

        self.settings = {
            "display_name": "",
            "theme": "Claro",
            "notifications": True,
        }

        self._create_menu_bar()
        self._create_main_layout()
        self._apply_theme()

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

        # Datos de ejemplo iniciales
        for name in ["Ana", "Luis", "María", "Carlos"]:
            QListWidgetItem(name, self.friends_list)

        # Panel derecho: chat
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)

        top_bar = QHBoxLayout()
        self.current_chat_label = QLabel("Selecciona un contacto")
        top_bar.addWidget(self.current_chat_label)
        top_bar.addStretch(1)
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
        items = self.friends_list.selectedItems()
        if not items:
            return
        friend_name = items[0].text()
        self.current_chat_label.setText(friend_name)
        # En una app real, cargarías el historial. Aquí limpiamos y ponemos placeholder.
        self.messages_view.clear()
        QListWidgetItem(f"Comienza una conversación con {friend_name}", self.messages_view)

    # Chat
    def _send_message(self):
        msg = self.message_input.text().strip()
        if not msg:
            return
        QListWidgetItem(f"Tú: {msg}", self.messages_view)
        self.message_input.clear()
        self.messages_view.scrollToBottom()

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
            
    # def _save_
        


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = chatWindow()
    window.show()
    sys.exit(app.exec())