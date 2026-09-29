
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class OutbreakAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Outbreak Analysis")
        title.setObjectName("page_title")

        description = QLabel(
            "Outbreak data analysis and visualization will appear here."
        )
        description.setObjectName("page_description")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()

