import os
import pandas as pd
from analytical_functions.analysis_functions import add_names_fields, determination_zero_strength, processing_time, \
    determining_coefficient_without_bad_data, predict
import time
import uuid
import openpyxl
import uuid
import re
import time
import numpy as np


def create_file_list(path: str) -> list[str]:
    try:
        list_file = [os.path.join(path, x) for x in os.listdir(path)]
        date_list = [[x, os.path.getmtime(x)] for x in list_file]
        sort_date_list = [elem[0] for elem in sorted(date_list, key=lambda x: x[1], reverse=False)]
        return sort_date_list
    except:
        raise FileNotFoundError


def create_data_frame(path: str, min_strength: float | int) -> pd.DataFrame:
    try:
        data_frame = pd.read_csv(path.replace('\\', '/'), sep=';', header=2, decimal=',', dtype='float')
        data_frame = add_names_fields(data_frame)
        data_frame = determination_zero_strength(data_frame, min_strength)
        return data_frame.drop(['Fx', 'Fz'], axis=1)
    except:
        data_frame = pd.read_csv(path, sep=';', header=19, decimal=',', dtype='float', encoding="windows-1251")
        data_frame = add_names_fields(data_frame)
        data_frame = determination_zero_strength(data_frame, min_strength)
        return data_frame.drop(['Fx', 'Fz'], axis=1)


def create_data_strength_from_list(list_data_frame: list[pd.DataFrame], min_strength: float | int) -> pd.DataFrame:
    data_frame = pd.concat(list_data_frame, ignore_index=True)
    data_frame = data_frame.loc[data_frame['Fy'] > min_strength]
    time_field = data_frame['Time'].to_numpy()
    data_frame['Time'] = processing_time(time_field)
    data_frame['Time'] = data_frame['Time'].apply(np.ceil)
    df = data_frame.groupby(by='Time').mean().dropna().reset_index()
    df['Fy'] = df['Fy'].apply(lambda x: round(x, 2))
    return df


def extract_basename(filename):
    # Извлечение базового имени файла без суффикса
    match = re.match(r"^(.*?)(?:_\d+)?$", filename)
    return match.group(1)


class Strength:
    """
    ...
    """

    def __init__(self,
                 path_strength: str,
                 material: str,
                 coating: str,
                 tool: str,
                 feed: float | int,
                 spindle_speed: float | int,
                 stage: str,
                 min_strength: float | int = 12,
                 from_files: bool = False,
                 percent: float | int = 0.22):
        self.material = material
        self.coating = coating
        self.tool = tool
        self.feed = feed
        self.spindle_speed = spindle_speed
        self.stage = stage
        if not from_files:
            self.list_file = create_file_list(path_strength)
            self.list_data = [create_data_frame(path_s, min_strength) for path_s in self.list_file]
            self.data_frame = create_data_strength_from_list(self.list_data, min_strength)
            self.start_day = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(os.path.getmtime(self.list_file[0])))
            self.last_day = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(os.path.getmtime(self.list_file[-1])))
            self.unique_id = str(uuid.uuid4())
            self.filename_base = f'{tool};{material};{coating};{feed};{spindle_speed};{stage}'
            self.passes = len(self.list_data)
            self.coefficient_mnk = determining_coefficient_without_bad_data(self.data_frame, percent)
            self.data_frame['Model'] = predict(*self.coefficient_mnk, self.data_frame['Time'])
            self.equation_mnk = f"{self.coefficient_mnk[0]:.2f} + {self.coefficient_mnk[1]:.2f}\u00b7T = Fy"
            self.strength_mean = self.data_frame['Fy'].mean()

    def save_file(self, path_dir: str) -> None:
        strength_dir = os.path.join(path_dir, self.filename_base)
        counter = 1
        while os.path.exists(strength_dir):
            strength_dir = os.path.join(path_dir, f'{self.filename_base}_{counter}')
            counter += 1

        self.filename = os.path.basename(strength_dir)
        os.makedirs(strength_dir)

        # Сохранение информации в текстовый файл
        with open(f'{strength_dir}/{self.filename}_info.txt', 'w') as info_file:
            info_file.write(f'Material: {self.material}\n')
            info_file.write(f'Coating: {self.coating}\n')
            info_file.write(f'Tool: {self.tool}\n')
            info_file.write(f'Feed: {self.feed}\n')
            info_file.write(f'Spindle Speed: {self.spindle_speed}\n')
            info_file.write(f'Stage: {self.stage}\n')
            info_file.write(f'Strength mean: {self.strength_mean}\n')
            info_file.write(f'Equation: {self.equation_mnk}\n')
            info_file.write(f'Delta strength: {self.coefficient_mnk[1]}\n')
            info_file.write(f'Unique ID: {self.unique_id}\n')
            info_file.write(f'Passes: {self.passes}\n')

            # info_file.write(f'Plot Info: {self.plot_info}\n')
            info_file.write(f'Start: {self.start_day}\n')
            info_file.write(f'End: {self.last_day}\n')

        with pd.ExcelWriter(f'{strength_dir}/{self.filename}.xlsx') as writer:
            self.data_frame.to_excel(writer, sheet_name='Data_strength')

    @classmethod
    def from_dir(cls, path_dir: str) -> Strength:
        """
        Создание объекта Strength из директории с данными
        """
        pass



if __name__ == '__main__':
    # path_ = r"C:\Анализ данных\Пара Сила+температура\4 этап\HN58\ALTIN\Силы"
    path_ = r"D:\Пара Сила+температура\4 этап\HN58\new party\ALTIN\Силы"
    new_strength = Strength(path_strength=path_,
                            material='ХН58',
                            coating='AlTiN3',
                            tool='Фреза 12',
                            feed=58,
                            spindle_speed=800,
                            stage='4')

    new_path = "files"
    new_strength.save_file(new_path)
