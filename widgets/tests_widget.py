import random
import requests
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QLabel, QScrollArea, QHBoxLayout, QPushButton, QMessageBox, \
    QGroupBox, QButtonGroup, QRadioButton


class TestsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.current_test = None
        self.selected_answers = {}
        self.question_widgets = []
        self.test_questions = []
        self.methods_mapping = {}
        self.init_ui()
        self.load_test_list()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.test_combo = QComboBox()
        self.test_combo.currentIndexChanged.connect(self.load_test)
        self.layout.addWidget(QLabel("Выберите тест:"))
        self.layout.addWidget(self.test_combo)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.questions_container = QWidget()
        self.questions_layout = QVBoxLayout()
        self.questions_container.setLayout(self.questions_layout)
        self.scroll_area.setWidget(self.questions_container)
        self.layout.addWidget(self.scroll_area)
        self.buttons_layout = QHBoxLayout()
        self.check_btn = QPushButton("Проверить ответы")
        self.check_btn.clicked.connect(self.check_answers)
        self.check_btn.hide()
        self.restart_btn = QPushButton("Новый тест")
        self.restart_btn.clicked.connect(self.generate_new_test)
        self.restart_btn.hide()
        self.buttons_layout.addWidget(self.check_btn)
        self.buttons_layout.addWidget(self.restart_btn)
        self.layout.addLayout(self.buttons_layout)
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.hide()
        self.layout.addWidget(self.result_label)
        self.setLayout(self.layout)

    def load_test(self):
        eng_name = self.test_combo.currentData()
        try:
            raw_url = f"https://raw.githubusercontent.com/huimorzhaa/Analysis-of-conjugacy-tables/main/tests/{eng_name}.json"
            response = requests.get(raw_url)
            response.raise_for_status()
            self.current_test = response.json()
            self.validate_test_structure()
            self.test_questions = self.current_test['questions'].copy()
            self.generate_new_test()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки теста: {str(e)}")

    def generate_new_test(self):
        if not self.test_questions:
            return
        random.shuffle(self.test_questions)
        self.questions = self.test_questions[:3]
        self.selected_answers = {}
        self.show_questions()
        self.check_btn.show()
        self.restart_btn.show()
        self.result_label.hide()
        self.set_answers_enabled(True)

    def show_questions(self):
        self.clear_questions()
        for i, question in enumerate(self.questions):
            group_box = QGroupBox(f"Вопрос {i + 1}: {question['question']}")
            vbox = QVBoxLayout()
            bg = QButtonGroup(group_box)
            for j, option in enumerate(question['options']):
                rb = QRadioButton(option)
                bg.addButton(rb, j)
                vbox.addWidget(rb)
            group_box.setLayout(vbox)
            self.questions_layout.addWidget(group_box)
            self.question_widgets.append({
                'widget': group_box,
                'buttons': bg,
                'correct': question['correct']
            })

    def clear_questions(self):
        for i in reversed(range(self.questions_layout.count())):
            widget = self.questions_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.question_widgets = []

    def check_answers(self):
        correct_count = 0
        total = len(self.questions)
        for idx, question in enumerate(self.question_widgets):
            selected = question['buttons'].checkedId()
            correct = question['correct']
            buttons = question['buttons'].buttons()
            for btn in buttons:
                btn.setEnabled(False)
            if selected == -1:
                continue
            if selected == correct:
                correct_count += 1
                buttons[selected].setStyleSheet("background-color: #e6ffe6; border: 2px solid #4CAF50;")
            else:
                buttons[selected].setStyleSheet("background-color: #ffe6e6; border: 2px solid #f44336;")
                buttons[correct].setStyleSheet("background-color: #e6ffe6; border: 2px solid #4CAF50;")
        
        # Код сохранения результатов (обновленный)
        if self.main_window.current_token and self.main_window.user_role == 'student':
            try:
                test_name = self.test_combo.currentData()
                score = (correct_count / total) * 100 if total > 0 else 0
                
                response = requests.post(
                    "http://localhost:8000/results",
                    json={"test_name": test_name, "score": score},
                    headers={"Authorization": f"Bearer {self.main_window.current_token}"}
                )
                
                if response.status_code == 200:
                    QMessageBox.information(self, "Успех", "Результат сохранен!")
                else:
                    QMessageBox.warning(self, "Ошибка", 
                        f"Ошибка сохранения: {response.status_code}\n{response.text}")
                    
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка соединения: {str(e)}")
            else:
                buttons[selected].setStyleSheet("background-color: #ffe6e6; border: 2px solid #f44336;")
                buttons[correct].setStyleSheet("background-color: #e6ffe6; border: 2px solid #4CAF50;")
        self.result_label.show()
        self.result_label.setText(f"Правильных ответов: {correct_count}/{total}\nРезультат: {correct_count / total * 100:.1f}%")
        self.check_btn.hide()
        self.set_answers_enabled(False)

    def set_answers_enabled(self, enabled):
        for question in self.question_widgets:
            for btn in question['buttons'].buttons():
                btn.setEnabled(enabled)

    def reset_test(self):
        self.clear_questions()
        self.selected_answers = {}
        self.result_label.hide()
        self.check_btn.hide()
        self.restart_btn.hide()

    def validate_test_structure(self):
        required_fields = ["method", "questions"]
        for field in required_fields:
            if field not in self.current_test:
                raise ValueError(f"Отсутствует обязательное поле: {field}")
        if len(self.current_test["questions"]) < 3:
            raise ValueError("Тест должен содержать минимум 3 вопроса")
        for question in self.current_test["questions"]:
            if not all(key in question for key in ["question", "type", "options", "correct"]):
                raise ValueError("Некорректная структура вопроса")
            if question['type'] != 'single':
                raise ValueError("Поддерживается только тип 'single' для вопросов")
            if not (0 <= question['correct'] < len(question['options'])):
                raise ValueError("Некорректный индекс правильного ответа")

    def load_test_list(self):
        try:
            self.load_methods_mapping()
            url = "https://api.github.com/repos/huimorzhaa/Analysis-of-conjugacy-tables/contents/tests"
            response = requests.get(url)
            response.raise_for_status()
            self.test_combo.clear()
            for item in response.json():
                if item['name'].endswith('.json'):
                    eng_name = item['name'][:-5]
                    ru_name = self.methods_mapping.get(eng_name, eng_name)
                    self.test_combo.addItem(ru_name, userData=eng_name)
            if self.test_combo.count() == 0:
                QMessageBox.warning(self, "Внимание", "В репозитории нет тестов!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки списка тестов: {str(e)}")

    def load_methods_mapping(self):
        try:
            mapping_url = "https://raw.githubusercontent.com/huimorzhaa/Analysis-of-conjugacy-tables/main/methods_mapping.json"
            response = requests.get(mapping_url)
            response.raise_for_status()
            self.methods_mapping = response.json()
        except Exception as e:
            QMessageBox.warning(self, "Внимание", f"Не удалось загрузить соответствие названий: {str(e)}")
            self.methods_mapping = {}
