from typing import List, Any
import numpy as np
import re
import pandas as pd
from analytical_functions.constant import dict_rename_coating, dict_rename_material
from typing import Optional
from pprint import pprint
import os


def processing_time(start_time: np.ndarray) -> np.ndarray:
    """
    :param start_time: np.ndarray: Необработанное время после соединения данных в один файл.
    :return: np.ndarray - Обработанное время, которое учитывает простои при фрезеровании
    """
    if any(elem < 0 for elem in start_time):
        raise ValueError("Некорректное время")
    start_time_shift: np.ndarray = np.insert(start_time, 0, start_time[0])
    start_time_shift: np.ndarray = np.delete(start_time_shift, start_time_shift.size - 1)
    new_time: np.ndarray = start_time - start_time_shift
    # Получаем новое время, которое будем складывать
    for i in range(new_time.size):
        if new_time[i] < 0:
            new_time[i] = 0
    processed_time = np.arange(new_time.size, dtype=float)
    for i in range(new_time.size):
        processed_time[i] = new_time[:i + 1].sum()
    return processed_time


def adding_time_in_temperature(arr: np.ndarray, processing_time_: Optional[float] = None) -> np.ndarray:
    """
    Изнанчально в данных о температуре нет времени, так как при фрезеровании время не записывалось в файл.
    Поэтому мы создаем столбец со временем, в зависимости от данных, которые записывались в файл сил.

    :param processing_time_: Время обработки
    :param arr: nd.ndarray[None],со временем из данных о температуре
    :return: np.ndarray со временем для температуры.
    """
    # Вычисляем время, берем суммарное время
    # обработки и делим на величину массива и умножаем на шаг

    if processing_time_:
        for i in range(arr.size):
            arr[i] = (processing_time_ / arr.size) * i
        return arr
    else:
        for i in range(arr.size):
            arr[i] = 0.28 * i
    return arr


def determination_zero_strength(strength_dataframe: pd.DataFrame, min_strength: float) -> List[pd.DataFrame]:
    """
    При записи разных проходов настроки устройства сбиваются, из-за чего силы в состоянии покоя показываются разные,
    данная функция вычисляет эту сила состояния покоя и прибавляет ее ко всем данным об этом проходе.
    :param list_strenght_dataframe: Список DataFrame с данными о силе
    :param min_strength: Минимальная сила, меньше которой мы считаем обработка не происходит.
    :return: Измененный DataFrame где к прибавлена константа нуля.
    """
    try:
        first_index = strength_dataframe.loc[strength_dataframe['Fy'] > min_strength].index.values[0]
        median_const = strength_dataframe['Fy'][:first_index].sort_values().median()
        strength_dataframe['Fy'] = strength_dataframe['Fy'] - median_const
        return strength_dataframe
    except IndexError:
        raise IndexError(f'В одном из файлов нет сил > {min_strength}')




def determination_zero_strength_list(list_strenght_dataframe: List[pd.DataFrame], min_strength: float) -> List[
    pd.DataFrame]:
    """
    При записи разных проходов настроки устройства сбиваются, из-за чего силы в состоянии покоя показываются разные,
    данная функция вычисляет эту сила состояния покоя и прибавляет ее ко всем данным об этом проходе.
    :param list_strenght_dataframe: Список DataFrame с данными о силе
    :param min_strength: Минимальная сила, меньше которой мы считаем обработка не происходит.
    :return: Новый список с измененными Таблицами DataFrame где к прибавлена константа нуля.
    """
    new_list_dataframe: list[pd.DataFrame] = []
    for data_frame_strength in list_strenght_dataframe:
        try:
            first_index = data_frame_strength.loc[data_frame_strength['Fy'] > min_strength].index.values[0]
            median_const = data_frame_strength['Fy'][:first_index].sort_values().median()
            data_frame_strength['Fy'] = data_frame_strength['Fy'] - median_const
            new_list_dataframe.append(data_frame_strength)
        except IndexError:
            raise IndexError(f'В одном из файлов нет сил > {min_strength}')
    return new_list_dataframe


def add_names_fields(data: pd.DataFrame) -> pd.DataFrame:
    data.columns = ['Time', 'Fx', 'Fy', 'Fz']
    data['Time'] = data['Time'].round(2)
    return data


def determining_coefficients(dataframe: pd.DataFrame) -> tuple[float, float]:
    """
    Определения функции для нахождения коэффициентов для функции
    прямой линии с помощью метода наименьших квадратов(МНК).
    :param dataframe: pd.DataFrame
    :return: tuple (w0, w1), коэффициенты для прямой.
    """
    x = dataframe[dataframe.columns[0]].to_numpy()
    y = dataframe[dataframe.columns[1]].to_numpy()
    size = len(x)
    avg_x = sum(x) / size
    avg_y = sum(y) / size
    avg_xy = sum(x[i] * y[i] for i in range(0, size)) / size

    std_x = (sum((x[i] - avg_x) ** 2 for i in range(0, size)) / size) ** 0.5
    std_y = (sum((y[i] - avg_y) ** 2 for i in range(0, size)) / size) ** 0.5

    corr_xy = (avg_xy - avg_x * avg_y) / (std_x * std_y)
    w1 = corr_xy * std_y / std_x
    w0 = avg_y - avg_x * w1

    return w0, w1


def determining_coefficient_without_bad_data(data: pd.DataFrame, percent: float = 0.22) -> tuple[float, float]:
    """
    Определения функции для нахождения коэффициентов для
    функции прямой линии с помощью метода наименьших квадратов(МНК).
    Без наиболее худших данных.
    :param data: pd.DataFrame. DataFrame с данными с двумя столбцами временем и силой(температура) резания.
    :param percent: Процент отбрасываемых данных.
    :return: tuple (w0, w1), коэффициенты для прямой.
    """
    kol_minus = int(np.ceil(len(data) * percent))
    w1, w2 = determining_coefficients(data)

    x = data.iloc[:, 0]
    data = data.copy()
    data['Result'] = predict(w1, w2, x)

    y_1 = data.iloc[:, 1]
    y_2 = data.iloc[:, 2]
    data['fail'] = quadratic_error(y_1, y_2)

    for i in range(kol_minus):
        data = data.sort_values(by='fail', ascending=False).iloc[1:].copy()
        data = data.sort_values(by=data.columns[0], ascending=True)
        w1, w2 = determining_coefficients(data)
        x = data.iloc[:, 0]
        data['Result'] = predict(w1, w2, x)
        y_1 = data.iloc[:, 1]
        y_2 = data.iloc[:, 2]
        data['fail'] = quadratic_error(y_1, y_2)
    return w1, w2


def predict(w1: float, w2: float, x_scale: pd.Series) -> List[np.float64 | Any]:
    """
    Построение прямой в с помщью коэффициентов.
    :param w1: свободный коэффициент прямой.
    :param w2: коэффициент роста прямой.
    :param x_scale: list[np.float64], значения времени.
    :return: list[np.float64], список предсказанных значений.
    """
    x_scale = x_scale.to_numpy()
    y_pred = [w1 + x_scale[i] * w2 for i in range(len(x_scale))]
    return y_pred


def quadratic_error(x: pd.Series, y: pd.Series) -> np.ndarray:
    """
    Определение среднеквадратичной ошибки.
    :param x: pd.Series, значения времени.
    :param y: pd.Series, значения силы.
    :return: np.ndarray, значения ошибки.
    """

    y_1 = x.to_numpy()
    y_2 = y.to_numpy()
    y_fail = (y_1 - y_2) ** 2
    return y_fail


def rename_materials(string: str, dict_rename_materials: dict[str]) -> str:
    """
    Переименование материалов.
    :param string: str
    :param dict_rename_materials: dict[str]
    :return: Возвращает переименованный материал.
    """
    material_result = string
    for key, elem in dict_rename_materials.items():
        if key in string:
            material_result = elem
            break
    return material_result


def rename_coating(string: str, dict_rename_coatings: dict[str]) -> str:
    """
    Переименование покрытий.
    :param string: str
    :param dict_rename_coatings: dict[str]
    :return: str. Возвращает переименованное покрытие.

    """
    list_coat = [x.strip() for x in string.split('+')]
    for i in range(len(list_coat)):
        for key, elem in dict_rename_coatings.items():
            if key in list_coat[i].lower():
                list_coat[i] = elem
                break
    return '+'.join(list_coat)


def extract_param_path(path: str) -> tuple[str, str, str, str]:
    """
    Испльзуя регулярные выражения достаем занчения материала, покрытия и этапа из строки пути к папке с файлами сил.

    :param path: str -  Путь к папке в которой лежат силы.
    :return: tuple(str, str, str, str) - Возвращает кортеж из 4 знаечеий material, coating, 'Фреза 12', stage
    """
    pattern = r'\w:(?:/.*?/)*?(\d\s?этап)/(\w{2}\s?\d{2}\s?[uу]?).*?/((?:\w+?\s?\+?\s?\w+?\s?\d*?/)|(?:\w+?/))'
    match = re.match(pattern, path)
    if match:
        stage = match.groups()[0]
        material = match.groups()[1]
        coating = match.groups()[2]
        material = rename_materials(material, dict_rename_material)
        coating = rename_coating(coating, dict_rename_coating)
    else:
        material = 'Неизвестно'
        coating = 'Неизвестно'
        stage = 'Неизвестно'

    return material, coating, 'Фреза 12', stage


def data_with_out_nan(data: pd.DataFrame) -> pd.DataFrame:
    return data.dropna()


def list_all_path_strength_temperature(path: str):
    all_files_and_dirs = os.walk(path)
    list_path = []
    for path, dirs, files in all_files_and_dirs:
        if dirs == ['Силы', 'Температура']:
            strength = os.path.join(path, 'Силы').replace('\\', '/')
            temperature = os.path.join(path, 'Температура').replace('\\', '/')
            list_path.append((strength, temperature))
    return list_path


if __name__ == '__main__':
    #     df = pd.DataFrame({'1': [1, 2, 3, 4], '2': [5, 6, 7, 8]})
    #     df_np = df['1'].to_numpy()
    #     coefficients = determining_coefficients(df)
    #     new = quadratic_error(df['1'], df['2'])
    #     print(type(new))
    path = r"C:\Анализ данных\Пара Сила+температура"
    list_path = list_all_path_strength_temperature(path)
    list_strength = [elem[0] for elem in list_path]
    count = 0
    for strength in list_strength:
        material, coating, stage, temperature = extract_param_path(strength)
        if material == 'Неизвестно':
            print(strength)
            count += 1
            print(count)
