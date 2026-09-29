from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class HospitalsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Hospitals")
        title.setObjectName("page_title")

        description = QLabel(
            "Nearby hospital discovery will appear here."
        )
        description.setObjectName("page_description")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()