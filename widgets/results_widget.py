from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
import requests

class ResultsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результаты тестирования")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Тест", "Пользователь", "Результат (%)", "Дата"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self.load_results)
        
        layout.addWidget(self.table)
        layout.addWidget(self.refresh_btn)
        self.setLayout(layout)
        
        self.load_results()

    def load_results(self):
        try:
            response = requests.get(
                "http://localhost:8000/results",
                headers={"Authorization": f"Bearer {self.parent().current_token}"}
            )
            if response.status_code == 200:
                results = response.json()
                self.table.setRowCount(len(results))
                for row_idx, result in enumerate(results):
                    self.table.setItem(row_idx, 0, QTableWidgetItem(result['test_name']))
                    self.table.setItem(row_idx, 1, QTableWidgetItem(result['username']))
                    self.table.setItem(row_idx, 2, QTableWidgetItem(f"{result['score']:.1f}"))
                    self.table.setItem(row_idx, 3, QTableWidgetItem(result['date']))
            else:
                self.table.setRowCount(0)
        except Exception as e:
            self.table.setRowCount(0)