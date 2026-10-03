from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.auth_manager import AuthManager
from app.ui.register_window import RegisterWindow


class LoginWindow(QWidget):
    """
    Login screen for HealthSync AI.
    """

    # Emitted when login succeeds.
    # Sends the authenticated user's information.
    login_successful = Signal(dict)

    def __init__(self, auth_manager: AuthManager):
        super().__init__()

        self.auth_manager = auth_manager
        self.authenticated_user = None

        # Keep the registration window alive.
        self.register_window = None

        self.setWindowTitle("HealthSync AI - Login")
        self.setMinimumSize(500, 600)
        self.resize(500, 600)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(16)

        layout.addStretch()

        title = QLabel("HealthSync AI")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("AI-Powered Health & IoT")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(30)

        card = QFrame()
        card.setObjectName("login_card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)

        login_label = QLabel("Login")
        login_label.setObjectName("login_title")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setObjectName("input")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.password_input.setObjectName("input")

        # Remember Me
        self.remember_me_checkbox = QCheckBox("Remember me")
        self.remember_me_checkbox.setObjectName("remember_me")

        self.login_button = QPushButton("Login")
        self.login_button.setObjectName("login_button")
        self.login_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        # Sign Up
        self.signup_button = QPushButton(
            "Don't have an account? Sign Up"
        )
        self.signup_button.setObjectName("signup_button")
        self.signup_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.status_label.setWordWrap(True)

        card_layout.addWidget(login_label)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.remember_me_checkbox)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.login_button)
        card_layout.addWidget(self.signup_button)
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)

        layout.addStretch()

        self.login_button.clicked.connect(
            self.handle_login
        )

        self.password_input.returnPressed.connect(
            self.handle_login
        )

        self.signup_button.clicked.connect(
            self.open_register_window
        )

    def handle_login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            self.status_label.setText(
                "Please enter email and password."
            )
            return

        remember_me = self.remember_me_checkbox.isChecked()

        user = self.auth_manager.login(
            email,
            password,
            remember_me,
        )

        if user is None:
            self.status_label.setText(
                "Invalid email or password."
            )
            return

        self.authenticated_user = user

        self.status_label.setText(
            f"Welcome, {user['name']}!"
        )

        # Notify main.py that authentication succeeded.
        self.login_successful.emit(user)

    def open_register_window(self):
        """
        Open the account registration window.
        """

        self.register_window = RegisterWindow()

        self.register_window.registration_successful.connect(
            self.handle_registration_success
        )

        self.register_window.show()

    def handle_registration_success(self):
        """
        Handle successful account creation.

        The registration window remains open, so the user
        can see the success message. The login window is
        brought back to the front for the next login.
        """

        self.email_input.clear()
        self.password_input.clear()

        self.status_label.setText(
            "Account created. You can now log in."
        )

        self.activateWindow()
        self.raise_()

    def apply_styles(self):
        self.setStyleSheet(
            """
            QWidget {
                background-color: #07131F;
                color: #FFFFFF;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            #title {
                color: #FFFFFF;
                font-size: 30px;
                font-weight: 700;
            }

            #subtitle {
                color: #90C2E7;
                font-size: 13px;
            }

            #login_card {
                background-color: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 16px;
            }

            #login_title {
                color: #FFFFFF;
                font-size: 22px;
                font-weight: 600;
            }

            #input {
                background-color: #07131F;
                color: #FFFFFF;
                border: 1px solid #29465A;
                border-radius: 8px;
                padding: 12px;
            }

            #input:focus {
                border: 1px solid #00A9A5;
            }

            #remember_me {
                color: #90C2E7;
                spacing: 8px;
            }

            #remember_me:hover {
                color: #FFFFFF;
            }

            #remember_me::indicator {
                width: 16px;
                height: 16px;
            }

            #remember_me::indicator:unchecked {
                background-color: #07131F;
                border: 1px solid #29465A;
                border-radius: 4px;
            }

            #remember_me::indicator:checked {
                background-color: #00A9A5;
                border: 1px solid #00A9A5;
                border-radius: 4px;
            }

            #login_button {
                background-color: #00A9A5;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: 600;
            }

            #login_button:hover {
                background-color: #008F8C;
            }

            #signup_button {
                background-color: transparent;
                color: #90C2E7;
                border: none;
                padding: 8px;
            }

            #signup_button:hover {
                color: #00A9A5;
            }

            #status {
                color: #90C2E7;
                font-size: 12px;
                padding-top: 4px;
            }
            """
        )
