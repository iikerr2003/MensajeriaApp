"""Sistema de autenticación con login, registro y gestión de sesiones."""

import sys
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from db_main import Database


class LoginWindow(QDialog):
    """Ventana de inicio de sesión y registro de usuarios."""

    def __init__(self, database: Database, parent=None):
        super().__init__(parent)
        self.db = database
        self.authenticated_user = None
        self.user_password = None
        
        self.setWindowTitle("Mensajería Segura - Inicio de Sesión")
        self.setMinimumSize(450, 400)
        self.setModal(True)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Título
        title = QLabel("🔒 Mensajería Segura")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Inicia sesión para acceder a tus conversaciones encriptadas")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)
        
        # Formulario de login
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Introduce tu nombre de usuario")
        self.username_input.setMinimumHeight(35)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Introduce tu contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.returnPressed.connect(self._handle_login)
        
        form_layout.addRow("👤 Usuario:", self.username_input)
        form_layout.addRow("🔑 Contraseña:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Botones de acción
        self.btn_login = QPushButton("Iniciar Sesión")
        self.btn_login.setMinimumHeight(40)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        self.btn_login.clicked.connect(self._handle_login)
        layout.addWidget(self.btn_login)
        
        self.btn_register = QPushButton("Crear Cuenta Nueva")
        self.btn_register.setMinimumHeight(40)
        self.btn_register.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self.btn_register.clicked.connect(self._handle_register)
        layout.addWidget(self.btn_register)
        
        # Separador
        separator = QLabel("─" * 50)
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setStyleSheet("color: #ccc;")
        layout.addWidget(separator)
        
        # Opción provisional test_user
        test_label = QLabel("⚠️ Acceso de Desarrollo (Provisional)")
        test_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        test_label.setStyleSheet("color: #ff6b6b; font-style: italic;")
        layout.addWidget(test_label)
        
        self.btn_test_user = QPushButton("Entrar como test_user")
        self.btn_test_user.setMinimumHeight(35)
        self.btn_test_user.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #000;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        self.btn_test_user.clicked.connect(self._handle_test_user)
        layout.addWidget(self.btn_test_user)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _handle_login(self):
        """Maneja el inicio de sesión."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(
                self,
                "Campos Vacíos",
                "Por favor, introduce usuario y contraseña."
            )
            return
        
        try:
            # Verificar usuario
            user = self.db.get_user_by_username(username)
            if not user:
                QMessageBox.warning(
                    self,
                    "Usuario no encontrado",
                    f"No existe ningún usuario con el nombre '{username}'.\n"
                    "¿Deseas crear una cuenta nueva?"
                )
                return
            
            # Verificar contraseña
            hashed_password = self.db.hash_password(username, password)
            if self.db.check_password(username, hashed_password):
                self.authenticated_user = user
                self.user_password = password
                self.db.update_last_login(user.id)
                
                QMessageBox.information(
                    self,
                    "Inicio de Sesión Exitoso",
                    f"¡Bienvenido de nuevo, {user.username}!"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Contraseña Incorrecta",
                    "La contraseña introducida es incorrecta.\n"
                    "Por favor, inténtalo de nuevo."
                )
                self.password_input.clear()
                self.password_input.setFocus()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error de Autenticación",
                f"Error durante el inicio de sesión:\n{e}"
            )
    
    def _handle_register(self):
        """Maneja el registro de nuevos usuarios."""
        from mainui import RegisterDialog
        import uuid
        
        dialog = RegisterDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_data = dialog.get_user_data()
            
            try:
                # Verificar si el usuario ya existe
                existing = self.db.get_user_by_username(user_data["username"])
                if existing:
                    QMessageBox.warning(
                        self,
                        "Usuario Existente",
                        f"Ya existe un usuario con el nombre '{user_data['username']}'.\n"
                        "Por favor, elige otro nombre."
                    )
                    return
                
                existing_email = self.db.get_user_by_email(user_data["email"])
                if existing_email:
                    QMessageBox.warning(
                        self,
                        "Email Existente",
                        f"Ya existe una cuenta con el email '{user_data['email']}'."
                    )
                    return
                
                # Crear hash de contraseña
                hashed_pw = self.db.hash_password(
                    user_data["username"],
                    user_data["password"]
                )
                
                # Crear usuario
                new_user = self.db.add_user(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hashed_pw,
                    uuid=str(uuid.uuid4()),
                    profile_picture=user_data.get("profile_picture"),
                )
                
                QMessageBox.information(
                    self,
                    "Registro Exitoso",
                    f"¡Cuenta creada exitosamente!\n\n"
                    f"Usuario: {new_user.username}\n"
                    f"UUID: {new_user.uuid}\n\n"
                    f"Puedes iniciar sesión ahora."
                )
                
                # Auto-rellenar campos de login
                self.username_input.setText(user_data["username"])
                self.password_input.setText(user_data["password"])
                self.password_input.setFocus()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error de Registro",
                    f"Error al crear la cuenta:\n{e}"
                )
    
    def _handle_test_user(self):
        """Maneja el acceso provisional con test_user."""
        try:
            import uuid as uuid_lib
            
            test_user = self.db.get_user_by_username("test_user")
            if not test_user:
                # Crear test_user si no existe
                hashed_pw = self.db.hash_password("test_user", "password123")
                test_user = self.db.add_user(
                    username="test_user",
                    email="test@example.com",
                    hashed_password=hashed_pw,
                    uuid=str(uuid_lib.uuid4()),
                )
            
            self.authenticated_user = test_user
            self.user_password = "password123"
            self.db.update_last_login(test_user.id)
            
            QMessageBox.information(
                self,
                "Acceso de Desarrollo",
                "Has entrado como test_user.\n"
                "Este acceso es provisional para desarrollo."
            )
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Error al acceder con test_user:\n{e}"
            )
    
    def get_authenticated_user(self) -> Optional[tuple]:
        """Devuelve el usuario autenticado y su contraseña.
        
        Returns
        -------
        tuple or None
            (user_object, password) si la autenticación fue exitosa, None en caso contrario.
        """
        if self.authenticated_user and self.user_password:
            return (self.authenticated_user, self.user_password)
        return None


# Para pruebas independientes
if __name__ == "__main__":
    app = QApplication(sys.argv)
    db = Database()
    
    login = LoginWindow(db)
    if login.exec() == QDialog.DialogCode.Accepted:
        user_data = login.get_authenticated_user()
        if user_data:
            user, password = user_data
            print(f"Usuario autenticado: {user.username}")
            print(f"ID: {user.id}, UUID: {user.uuid}")
            
            # Abrir la ventana principal del chat
            from mainui import chatWindow
            main_window = chatWindow(
                authenticated_user=user,
                user_password=password
            )
            main_window.show()
            sys.exit(app.exec())
    else:
        print("Login cancelado")
        sys.exit(0)
