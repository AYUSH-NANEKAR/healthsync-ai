from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MyHealthPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("My Health")
        title.setObjectName("page_title")

        description = QLabel(
            "Your vitals, activity, and health history will appear here."
        )
        description.setObjectName("page_description")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()