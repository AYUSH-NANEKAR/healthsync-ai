from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmergencyPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Emergency")
        title.setObjectName("page_title")

        description = QLabel(
            "Emergency contacts and SOS functionality will appear here."
        )
        description.setObjectName("page_description")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()