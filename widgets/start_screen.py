from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class StartScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("Выберите раздел для работы\nс таблицами сопряженности")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)
        for name, idx in [("Практика", 0), ("Теория", 1), ("Тесты", 2)]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _, i=idx: parent.show_main_interface(i))
            layout.addWidget(btn)
