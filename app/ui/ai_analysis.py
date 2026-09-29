from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AIAnalysisPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("AI Analysis")
        title.setObjectName("page_title")

        description = QLabel(
            "Health analysis and AI-generated reports will appear here."
        )
        description.setObjectName("page_description")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch()