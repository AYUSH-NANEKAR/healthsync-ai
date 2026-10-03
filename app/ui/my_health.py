from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.connection import get_connection
from app.services.health_profile_service import HealthProfileService


class MyHealthPage(QWidget):
    """
    User-specific My Health page.

    The page receives the authenticated user_id from MainWindow.
    User identity information is loaded from the users table, while
    health information is loaded from health_profiles.
    """

    def __init__(self, user_id: int):
        super().__init__()

        self.user_id = user_id
        self.health_service = HealthProfileService()

        self.is_editing = False
        self.original_values = {}

        self.setObjectName("my_health_page")

        self._build_ui()
        self._load_user_data()
        self._set_edit_mode(False)

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 32)
        content_layout.setSpacing(20)

        # --------------------------------------------------------
        # Header
        # --------------------------------------------------------

        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)

        title = QLabel("My Health")
        title.setObjectName("page_title")

        subtitle = QLabel(
            "Manage your personal, physical, and medical information."
        )
        subtitle.setObjectName("page_description")
        subtitle.setWordWrap(True)

        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        self.edit_button = QPushButton("Edit Profile")
        self.edit_button.setObjectName("primary_button")
        self.edit_button.setFixedHeight(42)
        self.edit_button.setMinimumWidth(125)
        self.edit_button.clicked.connect(self._toggle_edit_mode)

        header_layout.addWidget(self.edit_button)

        content_layout.addLayout(header_layout)

        # --------------------------------------------------------
        # Status message
        # --------------------------------------------------------

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        self.status_label.setWordWrap(True)
        self.status_label.hide()

        content_layout.addWidget(self.status_label)

        # --------------------------------------------------------
        # Personal Information
        # --------------------------------------------------------

        personal_card = self._create_card(
            "Personal Information",
            "Your basic account and personal information.",
        )

        personal_layout = QGridLayout()
        personal_layout.setHorizontalSpacing(24)
        personal_layout.setVerticalSpacing(16)

        self.name_input = self._create_line_edit()
        self.email_input = self._create_line_edit()
        self.mobile_input = self._create_line_edit()
        self.dob_input = self._create_date_edit()
        self.age_input = self._create_line_edit()
        self.gender_input = self._create_combo(
            [
                "Select Gender",
                "Male",
                "Female",
                "Other",
                "Prefer not to say",
            ]
        )
        self.city_input = self._create_line_edit()

        self.name_input.setReadOnly(True)
        self.email_input.setReadOnly(True)
        self.age_input.setReadOnly(True)

        personal_layout.addLayout(
            self._field_layout("Full Name", self.name_input),
            0,
            0,
        )

        personal_layout.addLayout(
            self._field_layout("Email", self.email_input),
            0,
            1,
        )

        personal_layout.addLayout(
            self._field_layout("Mobile Number", self.mobile_input),
            1,
            0,
        )

        personal_layout.addLayout(
            self._field_layout("Date of Birth", self.dob_input),
            1,
            1,
        )

        personal_layout.addLayout(
            self._field_layout("Age", self.age_input),
            2,
            0,
        )

        personal_layout.addLayout(
            self._field_layout("Gender", self.gender_input),
            2,
            1,
        )

        personal_layout.addLayout(
            self._field_layout("City / Location", self.city_input),
            3,
            0,
            1,
            2,
        )

        personal_card.layout().addLayout(personal_layout)

        content_layout.addWidget(personal_card)

        # --------------------------------------------------------
        # Physical Information
        # --------------------------------------------------------

        physical_card = self._create_card(
            "Physical & Health Profile",
            "Your physical measurements and calculated BMI.",
        )

        physical_layout = QGridLayout()
        physical_layout.setHorizontalSpacing(24)
        physical_layout.setVerticalSpacing(16)

        self.blood_group_input = self._create_combo(
            [
                "Select Blood Group",
                "A+",
                "A-",
                "B+",
                "B-",
                "AB+",
                "AB-",
                "O+",
                "O-",
            ]
        )

        self.height_input = self._create_line_edit()
        self.weight_input = self._create_line_edit()

        self.height_input.setPlaceholderText("e.g. 183")
        self.weight_input.setPlaceholderText("e.g. 75")

        self.bmi_value = QLabel("—")
        self.bmi_value.setObjectName("health_value")

        self.bmi_category = QLabel("BMI will be calculated automatically")
        self.bmi_category.setObjectName("health_secondary")

        bmi_container = QWidget()
        bmi_layout = QHBoxLayout(bmi_container)
        bmi_layout.setContentsMargins(0, 0, 0, 0)
        bmi_layout.setSpacing(10)

        bmi_layout.addWidget(self.bmi_value)
        bmi_layout.addWidget(self.bmi_category)
        bmi_layout.addStretch()

        physical_layout.addLayout(
            self._field_layout(
                "Blood Group",
                self.blood_group_input,
            ),
            0,
            0,
        )

        physical_layout.addLayout(
            self._field_layout(
                "Height (cm)",
                self.height_input,
            ),
            0,
            1,
        )

        physical_layout.addLayout(
            self._field_layout(
                "Weight (kg)",
                self.weight_input,
            ),
            1,
            0,
        )

        physical_layout.addLayout(
            self._field_layout(
                "BMI",
                bmi_container,
            ),
            1,
            1,
        )

        physical_card.layout().addLayout(physical_layout)

        content_layout.addWidget(physical_card)

        # --------------------------------------------------------
        # Medical Information
        # --------------------------------------------------------

        medical_card = self._create_card(
            "Medical Information",
            "Information that can help provide relevant health context.",
        )

        medical_layout = QGridLayout()
        medical_layout.setHorizontalSpacing(24)
        medical_layout.setVerticalSpacing(16)

        self.allergies_input = self._create_text_edit()
        self.conditions_input = self._create_text_edit()
        self.medications_input = self._create_text_edit()

        self.allergies_input.setPlaceholderText(
            "Enter known allergies, or write None."
        )

        self.conditions_input.setPlaceholderText(
            "Enter known medical conditions, or write None."
        )

        self.medications_input.setPlaceholderText(
            "Enter current medications, or write None."
        )

        medical_layout.addLayout(
            self._field_layout(
                "Allergies",
                self.allergies_input,
            ),
            0,
            0,
        )

        medical_layout.addLayout(
            self._field_layout(
                "Medical Conditions",
                self.conditions_input,
            ),
            0,
            1,
        )

        medical_layout.addLayout(
            self._field_layout(
                "Current Medications",
                self.medications_input,
            ),
            1,
            0,
            1,
            2,
        )

        medical_card.layout().addLayout(medical_layout)

        content_layout.addWidget(medical_card)

        # --------------------------------------------------------
        # Bottom action buttons
        # --------------------------------------------------------

        self.action_container = QWidget()
        action_layout = QHBoxLayout(self.action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(10)

        action_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("secondary_button")
        self.cancel_button.setFixedHeight(42)
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.clicked.connect(self._cancel_edit)

        self.save_button = QPushButton("Save Changes")
        self.save_button.setObjectName("primary_button")
        self.save_button.setFixedHeight(42)
        self.save_button.setMinimumWidth(135)
        self.save_button.clicked.connect(self._save_profile)

        action_layout.addWidget(self.cancel_button)
        action_layout.addWidget(self.save_button)

        content_layout.addWidget(self.action_container)

        content_layout.addStretch()

        scroll_area.setWidget(content)
        root_layout.addWidget(scroll_area)

        self._apply_styles()

        # Recalculate BMI when height or weight changes.
        self.height_input.textChanged.connect(self._update_bmi)
        self.weight_input.textChanged.connect(self._update_bmi)

        # Recalculate age when DOB changes.
        self.dob_input.dateChanged.connect(self._update_age)

    # ============================================================
    # CARD / FIELD HELPERS
    # ============================================================

    def _create_card(self, title_text, description_text):
        card = QFrame()
        card.setObjectName("health_card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 20, 22, 22)
        layout.setSpacing(5)

        title = QLabel(title_text)
        title.setObjectName("section_title")

        description = QLabel(description_text)
        description.setObjectName("section_description")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        return card

    def _field_layout(self, label_text, widget):
        container = QVBoxLayout()
        container.setSpacing(6)

        label = QLabel(label_text)
        label.setObjectName("field_label")

        container.addWidget(label)
        container.addWidget(widget)

        return container

    @staticmethod
    def _create_line_edit():
        widget = QLineEdit()
        widget.setMinimumHeight(42)
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        return widget

    @staticmethod
    def _create_text_edit():
        widget = QTextEdit()
        widget.setMinimumHeight(90)
        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        return widget

    @staticmethod
    def _create_combo(items):
        widget = QComboBox()
        widget.addItems(items)
        widget.setMinimumHeight(42)
        return widget

    @staticmethod
    def _create_date_edit():
        widget = QDateEdit()
        widget.setCalendarPopup(True)
        widget.setDisplayFormat("dd MMM yyyy")
        widget.setMinimumHeight(42)
        widget.setSpecialValueText("Select date")

        widget.setDate(
            QDate(2000, 1, 1)
        )

        return widget

    # ============================================================
    # USER DATA
    # ============================================================

    def _load_user_data(self):
        """
        Load name and email from the authenticated user's account.
        """

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT name, email
                FROM users
                WHERE id = ?
                LIMIT 1
                """,
                (self.user_id,),
            )

            user = cursor.fetchone()

        finally:
            connection.close()

        if user is None:
            self._show_status(
                "Unable to load your account information.",
                error=True,
            )
            return

        self.name_input.setText(user[0] or "")
        self.email_input.setText(user[1] or "")

        profile = self.health_service.get_profile(
            self.user_id
        )

        if profile is None:
            self._clear_profile_fields()
            self._show_status(
                "Your health profile is ready to be completed.",
                error=False,
            )
            return

        self._populate_profile(profile)

    def _populate_profile(self, profile):
        """
        Populate the UI from a health profile.
        """

        self.mobile_input.setText(
            profile.get("mobile_number") or ""
        )

        date_of_birth = profile.get("date_of_birth")

        if date_of_birth:
            parsed_date = QDate.fromString(
                str(date_of_birth),
                "yyyy-MM-dd",
            )

            if parsed_date.isValid():
                self.dob_input.setDate(parsed_date)

        gender = profile.get("gender")
        self._set_combo_value(
            self.gender_input,
            gender,
        )

        blood_group = profile.get("blood_group")
        self._set_combo_value(
            self.blood_group_input,
            blood_group,
        )

        height = profile.get("height")
        weight = profile.get("weight")

        if height is not None:
            self.height_input.setText(
                self._format_number(height)
            )

        else:
            self.height_input.clear()

        if weight is not None:
            self.weight_input.setText(
                self._format_number(weight)
            )

        else:
            self.weight_input.clear()

        self.city_input.setText(
            profile.get("city") or ""
        )

        self.allergies_input.setPlainText(
            profile.get("allergies") or ""
        )

        self.conditions_input.setPlainText(
            profile.get("medical_conditions") or ""
        )

        self.medications_input.setPlainText(
            profile.get("medications") or ""
        )

        self._update_age()
        self._update_bmi()

        self.original_values = self._get_form_values()

    def _clear_profile_fields(self):
        """
        Clear fields when a profile does not yet exist.
        """

        self.mobile_input.clear()

        self.gender_input.setCurrentIndex(0)
        self.blood_group_input.setCurrentIndex(0)

        self.city_input.clear()
        self.height_input.clear()
        self.weight_input.clear()

        self.allergies_input.clear()
        self.conditions_input.clear()
        self.medications_input.clear()

        self.age_input.clear()
        self.bmi_value.setText("—")
        self.bmi_category.setText(
            "BMI will be calculated automatically"
        )

        self.original_values = self._get_form_values()

    # ============================================================
    # EDIT MODE
    # ============================================================

    def _toggle_edit_mode(self):
        if self.is_editing:
            self._cancel_edit()
            return

        self._start_edit()

    def _start_edit(self):
        self.is_editing = True

        self.original_values = self._get_form_values()

        self._set_edit_mode(True)

    def _cancel_edit(self):
        if not self.is_editing:
            return

        self._restore_form_values(
            self.original_values
        )

        self.is_editing = False

        self._set_edit_mode(False)

        self._show_status(
            "Changes discarded.",
            error=False,
        )

    def _set_edit_mode(self, enabled):
        """
        Enable or disable editable health fields.
        """

        editable_widgets = [
            self.mobile_input,
            self.dob_input,
            self.gender_input,
            self.city_input,
            self.blood_group_input,
            self.height_input,
            self.weight_input,
            self.allergies_input,
            self.conditions_input,
            self.medications_input,
        ]

        for widget in editable_widgets:
            widget.setEnabled(enabled)

        # Name and email come from the account system and are
        # intentionally not editable from this page.
        self.name_input.setReadOnly(True)
        self.email_input.setReadOnly(True)
        self.age_input.setReadOnly(True)

        self.action_container.setVisible(enabled)

        if enabled:
            self.edit_button.setText("Editing...")
            self.edit_button.setEnabled(False)

        else:
            self.edit_button.setText("Edit Profile")
            self.edit_button.setEnabled(True)

    # ============================================================
    # SAVE
    # ============================================================

    def _save_profile(self):
        try:
            height = self._parse_positive_number(
                self.height_input.text(),
                "Height",
            )

            weight = self._parse_positive_number(
                self.weight_input.text(),
                "Weight",
            )

            date_of_birth = None

            if self.dob_input.date().isValid():
                date_of_birth = self.dob_input.date().toString(
                    "yyyy-MM-dd"
                )

            gender = self._get_combo_value(
                self.gender_input
            )

            blood_group = self._get_combo_value(
                self.blood_group_input
            )

            self.health_service.save_profile(
                user_id=self.user_id,
                mobile_number=self.mobile_input.text(),
                date_of_birth=date_of_birth,
                gender=gender,
                blood_group=blood_group,
                height=height,
                weight=weight,
                city=self.city_input.text(),
                allergies=self.allergies_input.toPlainText(),
                medical_conditions=(
                    self.conditions_input.toPlainText()
                ),
                medications=(
                    self.medications_input.toPlainText()
                ),
            )

        except ValueError as error:
            QMessageBox.warning(
                self,
                "Invalid Information",
                str(error),
            )
            return

        except Exception as error:
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Unable to save your health profile.\n\n{error}",
            )
            return

        self.is_editing = False

        profile = self.health_service.get_profile(
            self.user_id
        )

        if profile is not None:
            self._populate_profile(profile)

        self._set_edit_mode(False)

        self._show_status(
            "Your health profile has been saved successfully.",
            error=False,
        )

    # ============================================================
    # AGE / BMI
    # ============================================================

    def _update_age(self):
        if not self.dob_input.date().isValid():
            self.age_input.clear()
            return

        date_of_birth = self.dob_input.date().toString(
            "yyyy-MM-dd"
        )

        age = self.health_service.calculate_age(
            date_of_birth
        )

        if age is None:
            self.age_input.clear()
            return

        self.age_input.setText(
            f"{age} years"
        )

    def _update_bmi(self):
        height = self.height_input.text().strip()
        weight = self.weight_input.text().strip()

        if not height or not weight:
            self.bmi_value.setText("—")
            self.bmi_category.setText(
                "BMI will be calculated automatically"
            )
            return

        try:
            height_value = float(height)
            weight_value = float(weight)

        except ValueError:
            self.bmi_value.setText("—")
            self.bmi_category.setText(
                "Enter valid height and weight"
            )
            return

        bmi = self.health_service.calculate_bmi(
            height_value,
            weight_value,
        )

        if bmi is None:
            self.bmi_value.setText("—")
            self.bmi_category.setText(
                "Enter valid height and weight"
            )
            return

        category = self.health_service.get_bmi_category(
            bmi
        )

        self.bmi_value.setText(
            str(bmi)
        )

        self.bmi_category.setText(
            category
        )

    # ============================================================
    # FORM STATE
    # ============================================================

    def _get_form_values(self):
        return {
            "mobile_number": self.mobile_input.text(),
            "date_of_birth": self.dob_input.date().toString(
                "yyyy-MM-dd"
            ),
            "gender": self.gender_input.currentText(),
            "blood_group": self.blood_group_input.currentText(),
            "height": self.height_input.text(),
            "weight": self.weight_input.text(),
            "city": self.city_input.text(),
            "allergies": self.allergies_input.toPlainText(),
            "medical_conditions": (
                self.conditions_input.toPlainText()
            ),
            "medications": (
                self.medications_input.toPlainText()
            ),
        }

    def _restore_form_values(self, values):
        self.mobile_input.setText(
            values.get("mobile_number", "")
        )

        date_string = values.get(
            "date_of_birth",
            "",
        )

        parsed_date = QDate.fromString(
            date_string,
            "yyyy-MM-dd",
        )

        if parsed_date.isValid():
            self.dob_input.setDate(parsed_date)

        self._set_combo_value(
            self.gender_input,
            values.get("gender"),
        )

        self._set_combo_value(
            self.blood_group_input,
            values.get("blood_group"),
        )

        self.height_input.setText(
            values.get("height", "")
        )

        self.weight_input.setText(
            values.get("weight", "")
        )

        self.city_input.setText(
            values.get("city", "")
        )

        self.allergies_input.setPlainText(
            values.get("allergies", "")
        )

        self.conditions_input.setPlainText(
            values.get("medical_conditions", "")
        )

        self.medications_input.setPlainText(
            values.get("medications", "")
        )

        self._update_age()
        self._update_bmi()

    # ============================================================
    # FORM HELPERS
    # ============================================================

    @staticmethod
    def _set_combo_value(combo, value):
        if not value:
            combo.setCurrentIndex(0)
            return

        index = combo.findText(
            str(value),
            Qt.MatchFlag.MatchFixedString,
        )

        if index >= 0:
            combo.setCurrentIndex(index)

        else:
            combo.setCurrentIndex(0)

    @staticmethod
    def _get_combo_value(combo):
        value = combo.currentText().strip()

        if not value or value.startswith("Select "):
            return None

        return value

    @staticmethod
    def _format_number(value):
        try:
            number = float(value)

            if number.is_integer():
                return str(int(number))

            return f"{number:.1f}"

        except (TypeError, ValueError):
            return str(value)

    @staticmethod
    def _parse_positive_number(value, field_name):
        value = value.strip()

        if not value:
            return None

        try:
            number = float(value)

        except ValueError:
            raise ValueError(
                f"{field_name} must contain a valid number."
            )

        if number <= 0:
            raise ValueError(
                f"{field_name} must be greater than zero."
            )

        return number

    # ============================================================
    # STATUS
    # ============================================================

    def _show_status(self, message, error=False):
        self.status_label.setText(message)
        self.status_label.setProperty(
            "error",
            error,
        )

        self.status_label.style().unpolish(
            self.status_label
        )
        self.status_label.style().polish(
            self.status_label
        )

        self.status_label.show()

    # ============================================================
    # STYLES
    # ============================================================

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget#my_health_page {
                background-color: #07131F;
            }

            QLabel#page_title {
                color: #FFFFFF;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#page_description {
                color: #90C2E7;
                font-size: 14px;
            }

            QFrame#health_card {
                background-color: #0B1D2A;
                border: 1px solid #163447;
                border-radius: 14px;
            }

            QLabel#section_title {
                color: #FFFFFF;
                font-size: 18px;
                font-weight: 650;
                padding-bottom: 2px;
            }

            QLabel#section_description {
                color: #7895A8;
                font-size: 12px;
                padding-bottom: 8px;
            }

            QLabel#field_label {
                color: #90C2E7;
                font-size: 12px;
                font-weight: 600;
            }

            QLineEdit,
            QComboBox,
            QDateEdit,
            QTextEdit {
                background-color: #081824;
                color: #FFFFFF;
                border: 1px solid #1B3B4D;
                border-radius: 8px;
                padding: 8px 10px;
                font-size: 13px;
            }

            QLineEdit:focus,
            QComboBox:focus,
            QDateEdit:focus,
            QTextEdit:focus {
                border: 1px solid #00A9A5;
            }

            QLineEdit:disabled,
            QComboBox:disabled,
            QDateEdit:disabled,
            QTextEdit:disabled {
                background-color: #091A26;
                color: #7895A8;
                border: 1px solid #142D3B;
            }

            QComboBox QAbstractItemView {
                background-color: #0B1D2A;
                color: #FFFFFF;
                selection-background-color: #00A9A5;
                selection-color: #FFFFFF;
                border: 1px solid #1B3B4D;
            }

            QLabel#health_value {
                color: #00D5CF;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#health_secondary {
                color: #90C2E7;
                font-size: 12px;
            }

            QLabel#status_label {
                background-color: #0B2631;
                color: #7BE7DF;
                border: 1px solid #155A5A;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 12px;
            }

            QLabel#status_label[error="true"] {
                background-color: #2A171A;
                color: #FF9B9B;
                border: 1px solid #6E3036;
            }

            QPushButton#primary_button {
                background-color: #00A9A5;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 650;
            }

            QPushButton#primary_button:hover {
                background-color: #00BCB7;
            }

            QPushButton#primary_button:pressed {
                background-color: #008F8B;
            }

            QPushButton#primary_button:disabled {
                background-color: #18504F;
                color: #7895A8;
            }

            QPushButton#secondary_button {
                background-color: #102A38;
                color: #90C2E7;
                border: 1px solid #1B465A;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton#secondary_button:hover {
                background-color: #163748;
                color: #FFFFFF;
            }

            QScrollBar:vertical {
                background-color: #07131F;
                width: 8px;
                margin: 2px;
            }

            QScrollBar::handle:vertical {
                background-color: #214456;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #00A9A5;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            """
        )