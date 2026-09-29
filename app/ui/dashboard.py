from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Dashboard")
        title.setObjectName("page_title")

        description = QLabel(
            "Health and IoT overview will appear here."
        )
        description.setObjectName("page_description")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()