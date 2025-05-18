from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QComboBox, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView
import requests

class TheoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.methods_mapping = {}
        self.init_ui()
        self.load_theory_list()

    def init_ui(self):
        layout = QVBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.currentIndexChanged.connect(self.load_theory)
        layout.addWidget(QLabel("Выберите метод анализа:"))
        layout.addWidget(self.method_combo)
        self.web_view = QWebEngineView()
        self.web_view.setZoomFactor(1.2)
        layout.addWidget(self.web_view, stretch=1)
        self.setLayout(layout)

    def load_theory_list(self):
        try:
            mapping_url = "https://raw.githubusercontent.com/huimorzhaa/Analysis-of-conjugacy-tables/main/methods_mapping.json"
            response = requests.get(mapping_url)
            response.raise_for_status()
            self.methods_mapping = response.json()
            theory_url = "https://api.github.com/repos/huimorzhaa/Analysis-of-conjugacy-tables/contents/theory"
            theory_response = requests.get(theory_url)
            theory_response.raise_for_status()
            self.method_combo.clear()
            for item in theory_response.json():
                if item['name'].endswith('.html'):
                    eng_name = item['name'][:-5]
                    ru_name = self.methods_mapping.get(eng_name, eng_name)
                    self.method_combo.addItem(ru_name, userData=eng_name)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных: {str(e)}")

    def load_theory(self):
        if self.method_combo.count() == 0:
            return
        try:
            eng_name = self.method_combo.currentData()
            raw_url = f"https://raw.githubusercontent.com/huimorzhaa/Analysis-of-conjugacy-tables/main/theory/{eng_name}.html"
            response = requests.get(raw_url)
            response.raise_for_status()
            self.web_view.setHtml(response.text)
        except Exception as e:
            self.web_view.setHtml(f"""
                <h1>Ошибка загрузки теории</h1>
                <p>{str(e)}</p>
                <p>URL: {raw_url}</p>
            """)