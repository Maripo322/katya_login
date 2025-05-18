import io
import os

import requests
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QCheckBox, QHBoxLayout, QListWidget, QMessageBox,
    QFileDialog, QHeaderView
)
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

import numpy as np
import pandas as pd

from analysis import PracticeAnalysis, interpret_p_value, interpret_cramers_v, interpret_phi, \
    interpret_contingency_coefficient, interpret_odds_ratio, interpret_goodman_kruskal_tau
from dialogs import GitHubDialog, ManualInputDialog


class PracticeWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.df = None
        self.current_table = None
        self.selected_source = None
        self.selected_columns = []
        self.selected_method = None
        self.methods = {
            'Хи-квадрат Пирсона': PracticeAnalysis.chi_square,
            'Точный тест Фишера': PracticeAnalysis.fishers_exact,
            'Коэффициент Крамера V': PracticeAnalysis.cramers_v,
            'Коэффициент сопряженности': PracticeAnalysis.contingency_coefficient,
            'Коэффициент Фи': PracticeAnalysis.phi_coefficient,
            'Отношение шансов': PracticeAnalysis.odds_ratio,
            'Тау-коэффициент Гудмана-Краскела': PracticeAnalysis.goodman_kruskal_tau
        }

        self.current_step = 0
        self.remove_na_checkbox = QCheckBox("Удалить строки с пропусками в выбранных столбцах")
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.settings_panel = QGroupBox("Текущие настройки:")
        settings_layout = QVBoxLayout()
        self.source_info = QLabel("Источник данных: не выбран")
        self.columns_info = QLabel("Выбранные столбцы: нет")
        self.method_info = QLabel("Метод анализа: не выбран")
        settings_layout.addWidget(self.source_info)
        settings_layout.addWidget(self.columns_info)
        settings_layout.addWidget(self.method_info)
        self.settings_panel.setLayout(settings_layout)
        self.step1_group = QGroupBox("Шаг 1: Источник данных")
        step1_layout = QVBoxLayout()
        data_btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Загрузить CSV")
        self.load_btn.clicked.connect(self.load_csv)
        self.manual_btn = QPushButton("Ручной ввод")
        self.manual_btn.clicked.connect(self.manual_input)
        self.github_btn = QPushButton("Загрузить из GitHub")
        self.github_btn.clicked.connect(self.load_from_github)
        data_btn_layout.addWidget(self.load_btn)
        data_btn_layout.addWidget(self.manual_btn)
        data_btn_layout.addWidget(self.github_btn)
        self.load_status = QLabel("Данные не загружены")
        self.load_status.setAlignment(Qt.AlignCenter)
        self.load_status.setStyleSheet("font-weight: bold; color: #666;")
        self.step1_next_btn = QPushButton("Далее →")
        self.step1_next_btn.clicked.connect(self.next_step)
        self.step1_next_btn.setEnabled(False)
        step1_layout.addLayout(data_btn_layout)
        step1_layout.addWidget(self.load_status)
        step1_layout.addWidget(self.step1_next_btn)
        self.step1_group.setLayout(step1_layout)
        self.step2_group = QGroupBox("Шаг 2: Выбор столбцов для анализа")
        self.step2_group.setVisible(False)
        step2_layout = QVBoxLayout()
        data_and_columns_layout = QHBoxLayout()
        self.data_table = QTableWidget()
        data_and_columns_layout.addWidget(self.data_table)
        columns_layout = QVBoxLayout()
        self.column_list = QListWidget()
        self.column_list.setSelectionMode(QListWidget.MultiSelection)
        columns_layout.addWidget(QLabel("Выберите минимум 2 столбца:"))
        columns_layout.addWidget(self.column_list)
        columns_layout.addWidget(self.remove_na_checkbox)
        data_and_columns_layout.addLayout(columns_layout)
        step2_layout.addLayout(data_and_columns_layout)
        step2_btn_layout = QHBoxLayout()
        self.step2_back_btn = QPushButton("← Назад")
        self.step2_back_btn.clicked.connect(self.prev_step)
        self.step2_next_btn = QPushButton("Далее →")
        self.step2_next_btn.clicked.connect(self.next_step)
        self.step2_next_btn.setEnabled(False)
        step2_btn_layout.addWidget(self.step2_back_btn)
        step2_btn_layout.addWidget(self.step2_next_btn)
        step2_layout.addLayout(step2_btn_layout)
        self.step2_group.setLayout(step2_layout)
        self.step3_group = QGroupBox("Шаг 3: Настройка анализа")
        self.step3_group.setVisible(False)
        step3_layout = QVBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.addItems(self.methods.keys())
        step3_btn_layout = QHBoxLayout()
        self.step3_back_btn = QPushButton("← Назад")
        self.step3_back_btn.clicked.connect(self.prev_step)
        self.analyze_btn = QPushButton("Выполнить анализ")
        self.analyze_btn.clicked.connect(self.perform_analysis)
        step3_layout.addWidget(QLabel("Выберите метод анализа:"))
        step3_layout.addWidget(self.method_combo)
        step3_btn_layout.addWidget(self.step3_back_btn)
        step3_btn_layout.addWidget(self.analyze_btn)
        step3_layout.addLayout(step3_btn_layout)
        self.step3_group.setLayout(step3_layout)
        self.step4_group = QGroupBox("Результаты анализа")
        self.step4_group.setVisible(False)
        step4_layout = QVBoxLayout()
        self.visualization_tabs = QTabWidget()
        self.raw_data_tab = QTableWidget()
        self.contingency_table = QTableWidget()
        self.heatmap_tab = QWidget()
        self.bar_chart_tab = QWidget()
        self.pie_chart_tab = QWidget()
        self.visualization_tabs.addTab(self.raw_data_tab, "Исходные данные")
        self.visualization_tabs.addTab(self.contingency_table, "Таблица сопряжения")
        self.visualization_tabs.addTab(self.heatmap_tab, "Тепловая карта")
        self.visualization_tabs.addTab(self.bar_chart_tab, "Столбчатая")
        self.visualization_tabs.addTab(self.pie_chart_tab, "Круговая")
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.interpretation_text = QTextEdit()
        self.interpretation_text.setReadOnly(True)
        self.results_group = QGroupBox("Результаты анализа")
        results_group_layout = QVBoxLayout()
        results_group_layout.addWidget(self.results_text)
        self.results_group.setLayout(results_group_layout)
        self.interpretation_group = QGroupBox("Интерпретация")
        interpretation_group_layout = QVBoxLayout()
        interpretation_group_layout.addWidget(self.interpretation_text)
        self.interpretation_group.setLayout(interpretation_group_layout)
        self.step4_back_btn = QPushButton("← Новый анализ")
        self.step4_back_btn.clicked.connect(self.reset_ui)
        results_layout = QVBoxLayout()
        results_layout.addWidget(self.results_group)
        results_layout.addWidget(self.interpretation_group)
        results_layout.addWidget(self.step4_back_btn, 0, Qt.AlignVCenter)
        results_layout.setContentsMargins(0, 0, 0, 0)
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.visualization_tabs, 60)
        main_layout.addLayout(results_layout, 40)
        step4_layout.addLayout(main_layout)
        self.step4_group.setLayout(step4_layout)
        self.layout.addWidget(self.settings_panel)
        self.layout.addWidget(self.step1_group)
        self.layout.addWidget(self.step2_group)
        self.layout.addWidget(self.step3_group)
        self.layout.addWidget(self.step4_group)
        self.setLayout(self.layout)

    def load_from_github(self):
        try:
            dialog = GitHubDialog(self)
            if dialog.exec_():
                selected_item = dialog.file_list.currentItem()
                if not selected_item:
                    raise ValueError("Файл не выбран")
                selected_file = selected_item.text()
                self.selected_source = f"GitHub: {selected_file}"
                self._update_settings_display()
                raw_url = f"https://raw.githubusercontent.com/huimorzhaa/Analysis-of-conjugacy-tables/main/{selected_file}"
                response = requests.get(raw_url)
                response.raise_for_status()
                self.df = pd.read_csv(io.StringIO(response.text))
                self.update_data_display()
                self.update_column_list()
                self.load_status.setText(f"✓ Данные загружены из GitHub: {selected_file}")
                self.load_status.setStyleSheet("color: green; font-weight: bold;")
                self.step1_next_btn.setEnabled(True)
                self.selected_source = f"GitHub - {selected_file} "
                self._update_settings_display()
        except Exception as e:
            self.selected_source = "Ошибка загрузки"
            self.load_status.setStyleSheet("font-weight: bold; color: #666;")
            self._update_settings_display()
            self.load_status.setText("Ошибка загрузки из GitHub")
            self.load_status.setStyleSheet("font-weight: bold; color: #666;")
            #QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки:\n{str(e)}")
            self.reset_ui()

    def _update_settings_display(self):
        source_text = self.selected_source or "не выбран"
        columns_text = ", ".join(self.selected_columns) if self.selected_columns else "нет"
        method_text = self.selected_method or "не выбран"
        self.source_info.setText(f"Источник данных: {source_text}")
        self.columns_info.setText(f"Выбранные столбцы: {columns_text}")
        self.method_info.setText(f"Метод анализа: {method_text}")

    def next_step(self):
        try:
            if self.current_step == 0:
                if self.df is not None and not self.df.empty:
                    self.current_step = 1
                    self.step1_group.setVisible(False)
                    self.step2_group.setVisible(True)
                    self._update_settings_display()
                else:
                    QMessageBox.warning(self, "Ошибка", "Сначала загрузите данные!")
                    self.load_status.setStyleSheet("font-weight: bold; color: red;")
            elif self.current_step == 1:
                if len(self.selected_columns) >= 2:
                    self.current_step = 2
                    self.step2_group.setVisible(False)
                    self.step3_group.setVisible(True)
                    self._update_settings_display()
                else:
                    QMessageBox.warning(self, "Ошибка", "Выберите минимум 2 столбца!")
            elif self.current_step == 2:
                if self.selected_method:
                    self.current_step = 3
                    self.step3_group.setVisible(False)
                    self.step4_group.setVisible(True)
                    self._update_settings_display()
                    self.perform_analysis()
                else:
                    QMessageBox.warning(self, "Ошибка", "Выберите метод анализа!")
            else:
                self.reset_ui()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка перехода между шагами: {str(e)}")
            self.reset_ui()

    def prev_step(self):
        try:
            if self.current_step == 1:
                self.current_step = 0
                self.step2_group.setVisible(False)
                self.step1_group.setVisible(True)
            elif self.current_step == 2:
                self.current_step = 1
                self.step3_group.setVisible(False)
                self.step2_group.setVisible(True)
            elif self.current_step == 3:
                self.current_step = 2
                self.step4_group.setVisible(False)
                self.step3_group.setVisible(True)
            self._update_settings_display()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка возврата: {str(e)}")
            self.reset_ui()

    def reset_ui(self):
        self.selected_source = None
        self.selected_columns = []
        self.selected_method = None
        self._update_settings_display()
        self.df = None
        self.current_table = None
        self.data_table.clear()
        self.column_list.clear()
        self.contingency_table.clear()
        self.results_text.clear()
        self.clear_visualizations()
        self.current_step = 0
        self.step1_group.setVisible(True)
        self.step2_group.setVisible(False)
        self.step3_group.setVisible(False)
        self.step4_group.setVisible(False)
        self.load_status.setText("Данные не загружены")
        self.step1_next_btn.setEnabled(False)
        self.step2_next_btn.setEnabled(False)

    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            self.df = PracticeAnalysis.load_data(path)
            self.update_data_display()
            self.update_column_list()
            self.load_status.setText(f"✓ Данные загружены из файла: {os.path.basename(path)}")
            self.load_status.setStyleSheet("color: green; font-weight: bold;")
            self.step1_next_btn.setEnabled(True)
            self.selected_source = f"Файл: {os.path.basename(path)}"
            self._update_settings_display()
        except pd.errors.ParserError as e:
            self.df = None
            self.load_status.setText(f"Ошибка формата CSV: {e}")
        except Exception as e:
            self.df = None
            self.load_status.setText(f"Ошибка загрузки файла: {e}")
            self.load_status.setStyleSheet("font-weight: bold; color: #666;")

    def manual_input(self):
        dialog = ManualInputDialog(self)
        if dialog.exec_():
            try:
                rows = dialog.data_table.rowCount()
                cols = dialog.data_table.columnCount()
                # Проверяем, что задано хотя бы по одному признаку и наблюдению
                if rows == 0 or cols == 0:
                    self.load_status.setText("Сначала введите данные!")
                    return
                # Собираем данные и проверяем, есть ли хоть одно заполненное поле
                data = []
                any_filled = False
                for r in range(rows):
                    row_data = []
                    for c in range(cols):
                        item = dialog.data_table.item(r, c)
                        value = item.text().strip() if item else ""
                        row_data.append(value)
                        if value:
                            any_filled = True
                    data.append(row_data)
                if not any_filled:
                    self.load_status.setText("Сначала введите данные!")
                    self.load_status.setStyleSheet("color: red; font-weight: bold;")
                    return

                columns = [f"Признак {i + 1}" for i in range(cols)]
                self.df = pd.DataFrame(data, columns=columns)
                self.update_data_display()
                self.update_column_list()
                self.load_status.setText("✓ Данные введены вручную")
                self.load_status.setStyleSheet("font-weight: bold; color: #666;")
                self.step1_next_btn.setEnabled(True)
                self.selected_source = "Ручной ввод"
                self._update_settings_display()
            except Exception as e:
                self.df = None
                self.load_status.setText("Ошибка ручного ввода")
                self.load_status.setStyleSheet("color: red; font-weight: bold;")
                QMessageBox.critical(self, "Ошибка", f"Ошибка ввода данных:\n{str(e)}")
                self.reset_ui()

    def update_data_display(self):
        self.data_table.clear()
        if self.df is not None:
            self.data_table.setRowCount(self.df.shape[0])
            self.data_table.setColumnCount(self.df.shape[1])
            self.data_table.setHorizontalHeaderLabels(self.df.columns)
            for row in range(self.df.shape[0]):
                for col in range(self.df.shape[1]):
                    item = QTableWidgetItem(str(self.df.iat[row, col]))
                    self.data_table.setItem(row, col, item)
            self.data_table.resizeColumnsToContents()

    def update_column_list(self):
        self.column_list.clear()
        if self.df is not None:
            self.column_list.addItems(self.df.columns)
            self.column_list.itemSelectionChanged.connect(self.check_selection)
        self.column_list.itemSelectionChanged.connect(self._update_columns_selection)

    def _update_columns_selection(self):
        self.selected_columns = [item.text() for item in self.column_list.selectedItems()]
        self._update_settings_display()
        self.step2_next_btn.setEnabled(len(self.selected_columns) >= 2)

    def check_selection(self):
        self.step2_next_btn.setEnabled(len(self.column_list.selectedItems()) >= 2)

    def perform_analysis(self):
        self.selected_method = self.method_combo.currentText()
        self._update_settings_display()
        try:
            selected = [item.text() for item in self.column_list.selectedItems()]
            if len(selected) < 2:
                raise ValueError("Необходимо выбрать минимум 2 столбца")
            if self.remove_na_checkbox.isChecked():
                df_filtered = self.df.dropna(subset=selected)
            else:
                df_filtered = self.df
            self.filtered_df = df_filtered
            contingency_table = PracticeAnalysis.create_contingency_table(df_filtered, selected)
            self.current_table = contingency_table
            self.show_contingency_table(contingency_table)
            self.show_visualizations(contingency_table)
            method = self.methods[self.method_combo.currentText()]
            result = method(contingency_table)
            self.show_results(result)
            self.current_step = 3
            self.step3_group.setVisible(False)
            self.step4_group.setVisible(True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка анализа", str(e))
            self.reset_ui()

    def show_visualizations(self, df):
        try:
            self.clear_visualizations()
            self.show_raw_data()
            self.create_heatmap(df)
            self.create_bar_chart(df)
            self.create_pie_chart(df)
            self.show_contingency_table(df)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка визуализации", f"Ошибка при создании графиков: {str(e)}")
            self.reset_ui()

    def show_results(self, result):
        output = [f"({self.method_combo.currentText()})"]
        interpretation = []
        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, (float, np.floating)):
                    output.append(f"{k}: {v:.4f}")
                elif isinstance(v, np.ndarray):
                    output.append(f"{k}:\n{np.array2string(v, precision=2)}")
                else:
                    output.append(f"{k}: {v}")
                if k == 'p-значение':
                    interpretation.append(f"{k}: {interpret_p_value(v)}")
                elif k == 'Коэффициент Крамера V':
                    interpretation.append(f"{k}: {interpret_cramers_v(v)}")
                elif k == 'Коэффициент Фи':
                    interpretation.append(f"{k}: {interpret_phi(v)}")
                elif k == 'Коэффициент сопряженности':
                    interpretation.append(f"{k}: {interpret_contingency_coefficient(v)}")
                elif k == 'Отношение шансов':
                    interpretation.append(f"{k}: {interpret_odds_ratio(v)}")
                elif k == 'Тау-коэффициент':
                    interpretation.append(f"{k}: {interpret_goodman_kruskal_tau(v)}")
        self.results_text.setPlainText("\n".join(output))
        if interpretation:
            interpretation_text = "\n".join(interpretation)
        else:
            interpretation_text = "Интерпретация отсутствует."
        self.interpretation_text.setPlainText(interpretation_text)

    def show_contingency_table(self, table):
        try:
            self.contingency_table.clear()
            if isinstance(table, pd.DataFrame):
                rows = table.index.tolist()
                cols = table.columns.tolist()
                self.contingency_table.setRowCount(len(rows))
                self.contingency_table.setColumnCount(len(cols) + 1)
                self.contingency_table.setHorizontalHeaderLabels(["Index"] + [str(c) for c in cols])
                self.contingency_table.setVerticalHeaderLabels([str(i) for i in range(1, len(rows) + 1)])
                for i, idx in enumerate(rows):
                    index_item = QTableWidgetItem(str(idx))
                    index_item.setTextAlignment(Qt.AlignCenter)
                    self.contingency_table.setItem(i, 0, index_item)
                    for j, col in enumerate(cols, start=1):
                        value = table.loc[idx, col]
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignCenter)
                        self.contingency_table.setItem(i, j, item)
                self.contingency_table.resizeColumnsToContents()
                self.contingency_table.setAlternatingRowColors(True)
            else:
                self.contingency_table.setRowCount(0)
                self.contingency_table.setColumnCount(0)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка таблицы", f"Ошибка отображения таблицы сопряженности:\n{str(e)}")

    def clear_visualizations(self):
        try:
            self.contingency_table.clearContents()
            self.contingency_table.setRowCount(0)
            self.contingency_table.setColumnCount(0)
            for tab in [self.heatmap_tab, self.bar_chart_tab, self.pie_chart_tab]:
                if tab.layout():
                    while tab.layout().count():
                        item = tab.layout().takeAt(0)
                        widget = item.widget()
                        if widget:
                            widget.deleteLater()
            if self.df is not None:
                self.show_raw_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка очистки", f"Ошибка при сбросе визуализаций:\n{str(e)}")

    def show_raw_data(self):
        try:
            if self.df is not None and not self.df.empty:
                rows, cols = self.df.shape
                self.raw_data_tab.setRowCount(rows)
                self.raw_data_tab.setColumnCount(cols)
                self.raw_data_tab.setHorizontalHeaderLabels(self.df.columns.tolist())
                for i in range(rows):
                    for j in range(cols):
                        item = QTableWidgetItem(str(self.df.iloc[i, j]))
                        item.setTextAlignment(Qt.AlignCenter)
                        self.raw_data_tab.setItem(i, j, item)
                self.raw_data_tab.setEditTriggers(QTableWidget.NoEditTriggers)
                self.raw_data_tab.verticalHeader().setVisible(False)
                self.raw_data_tab.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                self.raw_data_tab.setAlternatingRowColors(True)
            else:
                self.raw_data_tab.setRowCount(0)
                self.raw_data_tab.setColumnCount(0)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка данных", f"Не удалось отобразить исходные данные: {str(e)}")

    def interpret_heatmap(self, table):
        try:
            data = table.values.flatten()
            if len(data) == 0:
                return "Нет данных для анализа."
            max_val = np.max(data)
            min_val = np.min(data)
            std_dev = np.std(data)
            mean_val = np.mean(data)
            interpretation = [
                "Интерпретация тепловой карты:",
                f"- Максимальное значение: {max_val:.1f}",
                f"- Минимальное значение: {min_val:.1f}",
                f"- Среднее значение: {mean_val:.1f}",
                f"- Стандартное отклонение: {std_dev:.1f}",
            ]
            if std_dev > mean_val:
                interpretation.append("\nВывод: Значительные различия между категориями указывают на сильную связь переменных.")
            elif std_dev > mean_val / 2:
                interpretation.append("\nВывод: Умеренные различия свидетельствуют о возможной ассоциации.")
            else:
                interpretation.append("\nВывод: Небольшие различия могут говорить об отсутствии сильной связи.")
            return "\n".join(interpretation)
        except:
            return "Не удалось проанализировать тепловую карту"

    def interpret_bar_chart(self, table):
        try:
            sums = table.sum(axis=0)
            total = sums.sum()
            n_categories = len(sums)
            if total == 0 or n_categories == 0:
                return "Нет данных для анализа"
            max_sum = sums.max()
            min_sum = sums.min()
            max_category = sums.idxmax()
            max_ratio = max_sum / total
            min_ratio = min_sum / total
            range_ratio = max_ratio - min_ratio
            from scipy.stats import chisquare
            chi2_stat, p_value = chisquare(sums)
            interpretation = [
                "Интерпретация столбчатой диаграммы:",
                f"-Общее количество наблюдений: {total:,}".replace(",", " "),
                f"-Количество категорий: {n_categories}",
                f"-Самая частая категория: '{max_category}' ({max_sum} наблюд., {max_ratio:.1%})",
                f"-Самая редкая категория: {min_sum} наблюд. ({min_ratio:.1%})",
                f"-Разница между категориями: {range_ratio:.1%}",
            ]
            if p_value < 0.05:
                interpretation.append("\nВывод: Распределение значимо отличается от равномерного (p < 0.05)")
                if max_ratio > 0.5:
                    interpretation.append(f"- Явное доминирование категории '{max_category}' (>50% всех случаев)")
                elif max_ratio > 0.3:
                    interpretation.append("- Заметное преобладание нескольких основных категорий")
                else:
                    interpretation.append("- Сбалансированное распределение с выраженными лидерами")
                if range_ratio > 0.4:
                    interpretation.append("- Экстремальные различия между категориями")
                elif range_ratio > 0.2:
                    interpretation.append("- Существенные различия в распределении")
            else:
                interpretation.append("\nВывод: Распределение близко к равномерному (p ≥ 0.05)")
            return "\n".join(interpretation)
        except Exception as e:
            print(f"Ошибка интерпретации: {str(e)}")
            return "Не удалось проанализировать диаграмму"

    def interpret_pie_chart(self, table):
        try:
            sums = table.sum(axis=1)
            total = sums.sum()
            max_percent = (sums.max() / total) * 100 if total > 0 else 0
            interpretation = [
                "Интерпретация круговой диаграммы:",
                f"- Всего наблюдений: {total:.1f}",
                f"- Наибольшая доля: {max_percent:.1f}%",
            ]
            if max_percent > 50:
                interpretation.append("\nВывод: Доминирующая категория занимает более половины распределения.")
            elif max_percent > 30:
                interpretation.append("\nВывод: Наличие выраженной основной категории.")
            else:
                interpretation.append("\nВывод: Относительно равномерное распределение долей.")
            return "\n".join(interpretation)
        except:
            return "Не удалось проанализировать круговую диаграмму"

    def create_heatmap(self, df):
        try:
            if self.heatmap_tab.layout():
                QWidget().setLayout(self.heatmap_tab.layout())
            fig = Figure(figsize=(6, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            data = df.values.astype(float)
            cax = ax.matshow(data, cmap='coolwarm')
            fig.colorbar(cax)
            ax.set_xticks(range(len(df.columns)))
            ax.set_xticklabels(df.columns.astype(str), rotation=45)
            if isinstance(df.index, pd.MultiIndex):
                y_labels = [' | '.join(map(str, idx)) for idx in df.index]
            else:
                y_labels = df.index.astype(str)
            ax.set_yticks(range(len(y_labels)))
            ax.set_yticklabels(y_labels)
            ax.set_title("Тепловая карта")
            interpretation = self.interpret_heatmap(df)
            text_edit = QTextEdit()
            text_edit.setPlainText(interpretation)
            text_edit.setReadOnly(True)
            text_edit.setMaximumHeight(150)
            layout = QVBoxLayout()
            layout.addWidget(canvas, 70)
            layout.addWidget(text_edit, 30)
            self.heatmap_tab.setLayout(layout)
        except Exception as e:
            print(f"Ошибка создания тепловой карты: {str(e)}")

    def create_bar_chart(self, df):
        try:
            if self.bar_chart_tab.layout():
                QWidget().setLayout(self.bar_chart_tab.layout())
            fig = Figure(figsize=(6, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            if isinstance(df.index, pd.MultiIndex):
                df.index = [' | '.join(map(str, idx)) for idx in df.index]
            df.plot(kind='bar', ax=ax)
            ax.legend(title='Категории')
            ax.set_ylabel('Частота')
            ax.set_title('Столбчатая диаграмма')
            ax.grid(True)
            interpretation = self.interpret_bar_chart(df)
            text_edit = QTextEdit()
            text_edit.setPlainText(interpretation)
            text_edit.setReadOnly(True)
            text_edit.setMaximumHeight(150)
            layout = QVBoxLayout()
            layout.addWidget(canvas, 70)
            layout.addWidget(text_edit, 30)
            self.bar_chart_tab.setLayout(layout)
        except Exception as e:
            print(f"Ошибка создания столбчатой диаграммы: {str(e)}")

    def create_pie_chart(self, df):
        try:
            if self.pie_chart_tab.layout():
                QWidget().setLayout(self.pie_chart_tab.layout())
            fig = Figure(figsize=(6, 4))
            canvas = FigureCanvas(fig)
            ax = fig.add_subplot(111)
            if isinstance(df.index, pd.MultiIndex):
                labels = [f"{x[0]} | {x[1]}" for x in df.index]
                sizes = df.sum(axis=1)
            else:
                labels = df.index.astype(str)
                sizes = df.sum(axis=1)
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Круговая диаграмма')
            interpretation = self.interpret_pie_chart(df)
            text_edit = QTextEdit()
            text_edit.setPlainText(interpretation)
            text_edit.setReadOnly(True)
            text_edit.setMaximumHeight(150)
            layout = QVBoxLayout()
            layout.addWidget(canvas, 70)
            layout.addWidget(text_edit, 30)
            self.pie_chart_tab.setLayout(layout)
        except Exception as e:
            print(f"Ошибка создания круговой диаграммы: {str(e)}")