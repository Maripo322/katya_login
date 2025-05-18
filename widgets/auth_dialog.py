from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QHBoxLayout, QComboBox
)

class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Авторизация")
        self.username_edit = QLineEdit()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["ученик", "учитель"])
        self.is_login = True
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Имя пользователя:"))
        layout.addWidget(self.username_edit)
        layout.addWidget(QLabel("Пароль:"))
        layout.addWidget(self.password_edit)
        layout.addWidget(QLabel("Роль:"))
        layout.addWidget(self.role_combo)
        
        btn_layout = QHBoxLayout()
        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.accept_login)
        register_btn = QPushButton("Регистрация")
        register_btn.clicked.connect(self.accept_register)
        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(register_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def accept_login(self):
        self.is_login = True
        self.accept()

    def accept_register(self):
        self.is_login = False
        self.accept()

    def get_credentials(self):
        return {
            "username": self.username_edit.text(),
            "password": self.password_edit.text(),
            "role": "student" if self.role_combo.currentText() == "ученик" else "teacher"
        }