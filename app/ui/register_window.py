from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.auth_service import AuthService


class RegisterWindow(QWidget):
    """
    Registration screen for HealthSync AI.
    """

    registration_successful = Signal()

    def __init__(self):
        super().__init__()

        self.auth_service = AuthService()

        self.setWindowTitle("HealthSync AI - Sign Up")
        self.setMinimumSize(500, 650)
        self.resize(500, 650)

        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 40, 60, 40)
        layout.setSpacing(16)

        layout.addStretch()

        title = QLabel("HealthSync AI")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Create your account")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(25)

        card = QFrame()
        card.setObjectName("register_card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(12)

        register_label = QLabel("Create Account")
        register_label.setObjectName("register_title")

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Name")
        self.name_input.setObjectName("input")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setObjectName("input")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("input")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText(
            "Confirm Password"
        )
        self.confirm_password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.confirm_password_input.setObjectName("input")

        self.register_button = QPushButton("Create Account")
        self.register_button.setObjectName("register_button")
        self.register_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.back_button = QPushButton("Back to Login")
        self.back_button.setObjectName("back_button")
        self.back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.status_label = QLabel("")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.status_label.setWordWrap(True)

        card_layout.addWidget(register_label)
        card_layout.addSpacing(10)
        card_layout.addWidget(self.name_input)
        card_layout.addWidget(self.email_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(self.confirm_password_input)
        card_layout.addSpacing(8)
        card_layout.addWidget(self.register_button)
        card_layout.addWidget(self.back_button)
        card_layout.addWidget(self.status_label)

        layout.addWidget(card)

        layout.addStretch()

        self.register_button.clicked.connect(
            self.handle_registration
        )

        self.back_button.clicked.connect(
            self.close
        )

        self.confirm_password_input.returnPressed.connect(
            self.handle_registration
        )

    def handle_registration(self):
        name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        if not name or not email or not password or not confirm_password:
            self.status_label.setText(
                "Please fill in all fields."
            )
            return

        if password != confirm_password:
            self.status_label.setText(
                "Passwords do not match."
            )
            return

        user_id = self.auth_service.register_user(
            name,
            email,
            password,
        )

        if user_id is None:
            self.status_label.setText(
                "An account with this email already exists."
            )
            return

        self.status_label.setText(
            "Account created successfully!"
        )

        self.registration_successful.emit()

        # Do not close the window here.
        # The LoginWindow will decide what happens
        # when this window is connected to it.

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

            #register_card {
                background-color: #0B1D2A;
                border: 1px solid #173044;
                border-radius: 16px;
            }

            #register_title {
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

            #register_button {
                background-color: #00A9A5;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: 600;
            }

            #register_button:hover {
                background-color: #008F8C;
            }

            #back_button {
                background-color: transparent;
                color: #90C2E7;
                border: 1px solid #29465A;
                border-radius: 8px;
                padding: 10px;
            }

            #back_button:hover {
                background-color: #0B1D2A;
                color: #FFFFFF;
            }

            #status {
                color: #90C2E7;
                font-size: 12px;
                padding-top: 4px;
            }
            """
        )
