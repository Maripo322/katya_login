import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, fisher_exact

def interpret_p_value(p):
    if p < 0.001:
        return "Очень сильные свидетельства против нулевой гипотезы"
    elif p < 0.01:
        return "Сильные свидетельства против нулевой гипотезы"
    elif p < 0.05:
        return "Умеренные свидетельства против нулевой гипотезы"
    elif p < 0.1:
        return "Слабые свидетельства против нулевой гипотезы"
    else:
        return "Недостаточно свидетельств против нулевой гипотезы"

def interpret_cramers_v(v):
    if v < 0.1:
        return "Пренебрежимо малая связь"
    elif v < 0.2:
        return "Слабая связь"
    elif v < 0.4:
        return "Умеренная связь"
    elif v < 0.6:
        return "Относительно сильная связь"
    else:
        return "Очень сильная связь"

def interpret_phi(phi):
    if phi < 0.1:
        return "Слабая связь"
    elif phi < 0.3:
        return "Умеренная связь"
    else:
        return "Сильная связь"

def interpret_contingency_coefficient(c):
    if c < 0.3:
        return "Слабая связь"
    elif c < 0.6:
        return "Умеренная связь"
    else:
        return "Сильная связь"

#def interpret_odds_ratio(or_val):
 #   if or_val < 0.33:
  #      return "Сильная отрицательная связь"
   # elif or_val < 0.67:
    #    return "Умеренная отрицательная связь"
 #   elif or_val < 1.5:
  #      return "Слабая или отсутствующая связь"
   # elif or_val < 3:
    #    return "Умеренная положительная связь"
    #else:
     #   return "Сильная положительная связь"

def interpret_odds_ratio(or_val):
    intervals = [
        (0, 0.2, "Сильная отрицательная связь (OR < 0.2)"),
        (0.2, 0.5, "Умеренная отрицательная связь (0.2 ≤ OR < 0.5)"),
        (0.5, 1.5, "Слабая или отсутствующая связь (0.5 ≤ OR < 1.5)"),
        (1.5, 5.0, "Умеренная положительная связь (1.5 ≤ OR < 5.0)"),
        (5.0, float('inf'), "Сильная положительная связь (OR ≥ 5.0)")
    ]
    for lower, upper, desc in intervals:
        if lower <= or_val < upper:
            return desc

def interpret_goodman_kruskal_tau(tau):
    if tau < 0.1:
        return "Очень слабая ассоциация"
    elif tau < 0.3:
        return "Слабая ассоциация"
    elif tau < 0.5:
        return "Умеренная ассоциация"
    else:
        return "Сильная ассоциация"

class PracticeAnalysis:
    @staticmethod
    def _cramers_v(table):
        chi2 = chi2_contingency(table)[0]
        n = table.sum().sum()
        phi2 = chi2 / n
        r, k = table.shape
        return np.sqrt(phi2 / min((k - 1), (r - 1)))

    @staticmethod
    def _contingency_coefficient(table):
        chi2 = chi2_contingency(table)[0]
        total = table.sum().sum()
        return np.sqrt(chi2 / (chi2 + total))

    @staticmethod
    def _phi_coefficient(table):
        if table.shape != (2, 2):
            raise ValueError("Phi coefficient requires 2x2 table")
        a, b = table.values[0]
        c, d = table.values[1]
        return (a * d - b * c) / np.sqrt((a + b) * (c + d) * (a + c) * (b + d))

    @staticmethod
    def _odds_ratio(table):
        if table.shape != (2, 2):
            raise ValueError("Odds ratio requires 2x2 table")
        a, b = table.values[0]
        c, d = table.values[1]
        return (a * d) / (b * c)

    @staticmethod
    def _goodman_kruskal_tau(table):
        chi2 = chi2_contingency(table)[0]
        n = table.sum().sum()
        total_sum = n * (np.prod(table.shape) - 1)
        return chi2 / total_sum if total_sum != 0 else 0

    @staticmethod
    def load_data(file_path):
        return pd.read_csv(file_path)

    @staticmethod
    def create_contingency_table(df, columns):
        if len(columns) < 2:
            raise ValueError("Необходимо выбрать минимум два столбца")
        index_cols = columns[:-1]
        column_col = columns[-1]
        return pd.crosstab(index=[df[c] for c in index_cols],
                           columns=df[column_col])

    @staticmethod
    def chi_square(table):
        chi2, p, dof, expected = chi2_contingency(table)
        return {'Хи-квадрат': chi2,
                'p-значение': p,
                'Степени свободы': dof,
                'Ожидаемые частоты': expected}

    @staticmethod
    def fishers_exact(table):
        if table.shape != (2, 2):
            return {'Ошибка': 'Метод применим только к таблицам 2x2'}
        or_val, p = fisher_exact(table)
        return {'Отношение шансов': or_val, 'p-значение': p}

    @staticmethod
    def cramers_v(table):
        return {'Коэффициент Крамера V': PracticeAnalysis._cramers_v(table)}

    @staticmethod
    def contingency_coefficient(table):
        return {'Коэффициент сопряженности': PracticeAnalysis._contingency_coefficient(table)}

    @staticmethod
    def phi_coefficient(table):
        if table.shape != (2, 2):
            return {'Ошибка': 'Метод применим только к таблицам 2x2'}
        return {'Коэффициент Фи': PracticeAnalysis._phi_coefficient(table)}

    @staticmethod
    def odds_ratio(table):
        if table.shape != (2, 2):
            return {'Ошибка': 'Метод применим только к таблицам 2x2'}
        return {'Отношение шансов': PracticeAnalysis._odds_ratio(table)}

    @staticmethod
    def goodman_kruskal_tau(table):
        return {'Тау-коэффициент': PracticeAnalysis._goodman_kruskal_tau(table)}
