from typing import List, Any
import numpy as np
import re
import pandas as pd


def processing_time(start_time: np.ndarray) -> np.ndarray:
    '''
    :param start_time: Необработанное время после соединения данных в один файл.
    :return: Обработанное время, которое учитывает простои при фрезеровании
    '''
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


def adding_time_in_temperature(arr: np.ndarray, data_strength: pd.DataFrame) -> np.ndarray:
    '''
    Изнанчально в данных о температуре нет времени, так как при фрезеровании время не записывалось в файл.
    Поэтому мы создаем время, в зависимости от данных, которые записывались в файл сил.

    :param arr: nd.ndarray[None],со временем из данных о температуре
    :param data_strength: DataFrame с данными о силе, в котором есть столбец "Time"
    :return: np.ndarray со временем для температуры.
    '''
    # Вычисляем время, берем суммарное время
    # обработки и делим на величину массива и умножаем на шаг
    for i in range(arr.size):
        arr[i] = ((data_strength['Time'].iloc[-1]) / arr.size) * i
    return arr


def determination_zero_strength(list_strenght_dataframe: List[pd.DataFrame], min_strength: float) -> List[pd.DataFrame]:
    '''
    При записи разных проходов настроки устройства сбиваются, из-за чего силы в состоянии покоя показываются разные,
    данная функция вычисляет эту сила состояния покоя и прибавляет ее ко всем данным об этом проходе.
    :param list_strenght_dataframe: Список DataFrame с данными о силе
    :param min_strength: Минимальная сила, меньше которой мы считаем обработка не происходит.
    :return: Новый список с измененными Таблицами DataFrame где к прибавлена константа нуля.
    '''
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


def add_names_fields(data: pd.DataFrame):
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


def determining_koeff_without_bad_data(data, percent=0.22):
    """
    Определения функции для нахождения коэффициентов для функции прямой линии с помощью метода наименьших квадратов(МНК).
    Без наиболее худших данных.
    :param data:
    :param percent:
    :return:
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
    :param x_scale: list[np.float64], список предсказанных значений.
    :return:
    """
    x_scale = x_scale.to_numpy()
    y_pred = [w1 + x_scale[i] * w2 for i in range(len(x_scale))]
    return y_pred


def quadratic_error(x: pd.Series, y: pd.Series) -> np.ndarray:
    y_1 = x.to_numpy()
    y_2 = y.to_numpy()
    y_fail = (y_1 - y_2) ** 2
    return y_fail


def rename_materials(string: str) -> str:
    dictionary_material = {
        "50": "ХН50",
        "58": "ХН58",
        "41": "ВТ41",
        "18": "ВТ18У"
    }
    material_result = string
    for key, elem in dictionary_material.items():
        if key in string:
            material_result = elem
            break
    return material_result


def rename_coating(string: str) -> str:
    dict_coating = {
        'naco': 'nACo3',
        'tib': 'TiB2',
        'altin': 'AlTiN3',
        'nacro': 'nACRo',
        'altincrn': 'AlTiCrN3',
    }
    list_coat = [x.strip() for x in string.split('+')]
    for i in range(len(list_coat)):
        for key, elem in dict_coating.items():
            if key in list_coat[i].lower():
                list_coat[i] = elem
                break
    return '+'.join(list_coat)



def extract_param_path(path):
    """
    Испльзуя регулярные выражения достаем занчения материала, покрытия и этапа из строки пути файла.

    :param path: Путь к папке в которой лежат силы.
    :return: Возвращает кортеж из 4 знаечеий material, coating, 'Фреза 12', stage
    """
    pattern = r'\w:(?:/.*?/)*?(\d\s?этап)/(\w{2}\s?\d{2}\s?[uу]?).*?/(\w+?\s?\+?\s?\w+)\s?\d+/'
    match = re.match(pattern, path)
    stage = match.groups()[0]
    material = match.groups()[1]
    coating = match.groups()[2]
    material = rename_materials(material)
    coating = rename_coating(coating)

    return material, coating, 'Фреза 12', stage

if __name__ == '__main__':
    df = pd.DataFrame({'1': [1, 2, 3, 4], '2': [5, 6, 7, 8]})
    df_np = df['1'].to_numpy()
    coefficients = determining_coefficients(df)
    new = quadratic_error(df['1'], df['2'])
    print(type(new))
