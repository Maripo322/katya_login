import io
import requests
import pandas as pd
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QListWidget, QHBoxLayout,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QLineEdit
)
from PyQt5.QtCore import Qt

class GitHubDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор файла из репозитория")
        self.owner = "huimorzhaa"
        self.repo = "Analysis-of-conjugacy-tables"
        self.file_list = QListWidget()
        self._build_ui()
        self._load_file_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Доступные CSV-файлы:"))
        layout.addWidget(self.file_list)
        btn_layout = QHBoxLayout()
        ok = QPushButton("OK"); ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        btn_layout.addWidget(ok); btn_layout.addWidget(cancel)
        layout.addLayout(btn_layout)

    def _load_file_list(self):
        try:
            url = f"https://api.github.com/repos/{self.owner}/{self.repo}/contents/"
            resp = requests.get(url); resp.raise_for_status()
            names = [f['name'] for f in resp.json() if f['name'].endswith('.csv')]
            self.file_list.addItems(names)
            if not names:
                QMessageBox.information(self, "Info", "CSV-файлов не найдено")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{e}")

class ManualInputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ручной ввод данных")
        self.feature_input = QLineEdit()
        self.obs_input = QLineEdit()
        self.data_table = QTableWidget()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Число признаков:")); layout.addWidget(self.feature_input)
        layout.addWidget(QLabel("Число наблюдений:")); layout.addWidget(self.obs_input)
        btn = QPushButton("Создать таблицу"); btn.clicked.connect(self._make_table)
        layout.addWidget(btn)
        layout.addWidget(self.data_table)
        ok_layout = QHBoxLayout()
        ok = QPushButton("OK"); ok.clicked.connect(self.accept)
        cancel = QPushButton("Cancel"); cancel.clicked.connect(self.reject)
        ok_layout.addWidget(ok); ok_layout.addWidget(cancel)
        layout.addLayout(ok_layout)

    def _make_table(self):
        try:
            f = int(self.feature_input.text())
            n = int(self.obs_input.text())
            self.data_table.setColumnCount(f)
            self.data_table.setRowCount(n)
            self.data_table.setHorizontalHeaderLabels([f"Признак {i+1}" for i in range(f)])
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректные числа")

    def get_dataframe(self):
        rows = self.data_table.rowCount()
        cols = self.data_table.columnCount()
        data = []
        for i in range(rows):
            row = []
            for j in range(cols):
                item = self.data_table.item(i, j)
                row.append(item.text() if item else "")
            data.append(row)
        return pd.DataFrame(data, columns=[self.data_table.horizontalHeaderItem(i).text() for i in range(cols)])
