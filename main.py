import sys
import requests
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QHBoxLayout, QListWidget, QListWidgetItem, QSplitter, QPushButton, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

from widgets.start_screen import StartScreen
from widgets.practice_widget import PracticeWidget
from widgets.theory_widget import TheoryWidget
from widgets.tests_widget import TestsWidget
from widgets.auth_dialog import AuthDialog

STYLE = """
/* общие настройки */
QWidget {
    background-color: #f0f2f5;
    font-family: "Segoe UI", Tahoma, sans-serif;
    font-size: 16px;  /* Увеличенный размер шрифта */
    color: #333;
}

/* главное окно */
QMainWindow {
    background-color: #f0f2f5;
}

/* кнопки */
QPushButton {
    background-color: #4a90e2;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-size: 16px;
}
QPushButton:hover {
    background-color: #4281c9;
}
QPushButton:pressed {
    background-color: #3a75b1;
}

/* меню */
QListWidget {
    background: #ffffff;
    border: none;
    padding: 4px;
    font-size: 16px;
}
QListWidget::item {
    padding: 12px;
    margin: 4px 0;
}
QListWidget::item:selected {
    background: #4a90e2;
    color: white;
    border-radius: 4px;
}

/* заголовки  */
QGroupBox {
    border: 1px solid #d0d3d8;
    border-radius: 4px;
    margin-top: 10px;
    font-size: 16px;
}
QGroupBox:title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px;
    color: #4a90e2;
    font-weight: bold;
    font-size: 18px;
}

/* вкладки */
QTabWidget::pane {
    border: 1px solid #d0d3d8;
    border-radius: 4px;
}
QTabBar::tab {
    background: #e6e8eb;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 16px;
}
QTabBar::tab:selected {
    background: #ffffff;
    font-weight: bold;
}

/* Поля ввода */
QLineEdit, QTextEdit {
    background: #ffffff;
    border: 1px solid #d0d3d8;
    border-radius: 4px;
    padding: 6px;
    font-size: 16px;
}

/* ComboBox */
QComboBox {
    background: #ffffff;
    border: 1px solid #d0d3d8;
    border-radius: 4px;
    padding: 6px;
    font-size: 16px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ таблиц сопряженности")
        self.resize(1200, 800)
        self.current_token = None
        self.user_role = None
        self.current_username = None
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self._init_ui()
        self._init_toolbar()    


    def _init_toolbar(self):
        self.toolbar = self.addToolBar("Main")
        self.auth_button = QPushButton("Войти")
        self.auth_button.clicked.connect(self.handle_auth)
        self.toolbar.addWidget(self.auth_button)
        
        self.results_button = QPushButton("Результаты")
        self.results_button.setStyleSheet("padding: 5px 15px;")
        self.results_button.clicked.connect(self.show_results)
        self.toolbar.addWidget(self.results_button)

    def _init_ui(self):
        # Start screen
        self.start = StartScreen(self)
        self.stack.addWidget(self.start)

        # Main interface
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        splitter = QSplitter()
        self.menu = QListWidget()
        self.menu.setFixedWidth(200)
        self.menu.itemClicked.connect(lambda i: self._switch_tab(self.menu.row(i)))
        
        self.content = QStackedWidget()
        splitter.addWidget(self.menu)
        splitter.addWidget(self.content)
        splitter.setSizes([200, 1000])
        
        main_layout.addWidget(splitter)
        
        # Добавляем виджеты в стек
        for text, icon, widget in [
            ("Практика", "icons/practice.svg", PracticeWidget()),
            ("Теория", "icons/theory.svg", TheoryWidget()),
            ("Тесты", "icons/tests.svg", TestsWidget())
        ]:
            item = QListWidgetItem(QIcon(icon), text)
            item.setSizeHint(QSize(180, 40))
            self.menu.addItem(item)
            self.content.addWidget(widget)
            widget.main_window = self
        
        self.stack.addWidget(main_widget)

    def show_main_interface(self, idx):
        self.stack.setCurrentIndex(1)
        self.menu.setCurrentRow(idx)
        self.content.setCurrentIndex(idx)

    def _switch_tab(self, idx):
        self.content.setCurrentIndex(idx)

    def handle_auth(self):
            if self.current_token:
                self.current_token = None
                self.user_role = None
                self.current_username = None
                self.auth_button.setText("Войти")
                self.results_button.hide()
                QMessageBox.information(self, "Успех", "Вы вышли из системы")
            else:
                dialog = AuthDialog(self)
                if dialog.exec_():
                    self.process_auth(dialog)    

    def process_auth(self, dialog):
            credentials = dialog.get_credentials()
            try:
                if dialog.is_login:
                    response = requests.post(
                        "http://localhost:8000/token",
                        data={
                            "username": credentials['username'],
                            "password": credentials['password'],
                            "grant_type": "password"
                        },
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
                    if response.status_code == 200:
                        self.current_token = response.json()["access_token"]
                        me_response = requests.get(
                            "http://localhost:8000/me",
                            headers={"Authorization": f"Bearer {self.current_token}"}
                        )
                        if me_response.status_code == 200:
                            user_info = me_response.json()
                            self.user_role = user_info['role']
                            self.current_username = user_info['username']
                            self.auth_button.setText(f"Выйти ({self.current_username})")
                            self.results_button.setVisible(self.user_role == 'teacher')
                            QMessageBox.information(self, "Успех", "Авторизация прошла успешно")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Неверные учетные данные")
                else:
                    response = requests.post(
                        "http://localhost:8000/register",
                        json={
                            "username": credentials['username'],
                            "password": credentials['password'],
                            "role": credentials['role']
                        }
                    )
                    if response.status_code == 200:
                        QMessageBox.information(self, "Успех", "Регистрация прошла успешно")
                    else:
                        error = response.json().get("detail", "Ошибка регистрации")
                        QMessageBox.warning(self, "Ошибка", error)
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка соединения: {str(e)}")

    def show_results(self):
            from widgets.results_widget import ResultsDialog
            dialog = ResultsDialog(self)
            dialog.exec_()    
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
