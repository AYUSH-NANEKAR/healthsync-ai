from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DevicesPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Devices")
        title.setObjectName("page_title")

        description = QLabel(
            "BLE device discovery and connection management will appear here."
        )
        description.setObjectName("page_description")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()