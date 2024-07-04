import os
import pandas as pd
from analytical_functions.analysis_functions import determining_coefficient_without_bad_data, predict
import openpyxl
import time
import uuid
from data_class_communication.func_init import create_file_list, create_data_frame_strength, \
    create_data_strength_from_list, extract_basename, create_data_frame_temperature_from_list, \
    create_data_frame_temperature
import numpy as np
import pickle
import shelve


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
        """

        :rtype: object
        """
        self.material = material
        self.coating = coating
        self.tool = tool
        self.feed = feed
        self.spindle_speed = spindle_speed
        self.stage = stage
        if not from_files:
            list_file = create_file_list(path_strength)
            list_data = [create_data_frame_strength(path_s, min_strength) for path_s in list_file]
            self.data_frame = create_data_strength_from_list(list_data, min_strength)
            self.start_day = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(os.path.getmtime(list_file[0])))
            self.last_day = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(os.path.getmtime(list_file[-1])))
            self.unique_id = str(uuid.uuid4())
            self.filename_base = f'{tool};{material};{coating};{feed};{spindle_speed};{stage}'
            self.filename = self.filename_base
            self.passes = len(list_data)
            self.coefficient_mnk = determining_coefficient_without_bad_data(self.data_frame, percent)
            self.data_frame['Model_strength'] = predict(*self.coefficient_mnk, self.data_frame['Time'])
            self.equation_mnk = f"{self.coefficient_mnk[0]:.2f} + {self.coefficient_mnk[1]:.2f}\u00b7T = Fy"
            self.strength_mean = self.data_frame['Fy'].mean()
            self.processing_time = self.data_frame['Time'].iloc[-1]

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
            info_file.write(f'w0: {self.coefficient_mnk[0]}\n')
            info_file.write(f'w1: {self.coefficient_mnk[1]}\n')
            info_file.write(f'Unique ID: {self.unique_id}\n')
            info_file.write(f'Passes: {self.passes}\n')
            info_file.write(f'Processing time: {self.processing_time}\n')
            info_file.write(f'Start: {self.start_day}\n')
            info_file.write(f'End: {self.last_day}\n')

        self.data_frame.to_csv(f'{strength_dir}/{self.filename}_силы.csv', sep=';', decimal=',')
        with pd.ExcelWriter(f'{strength_dir}/{self.filename}.xlsx') as writer:
            self.data_frame.to_excel(writer, sheet_name='Data_strength')

    @classmethod
    def from_dir(cls, path_dir: str):
        """
        Создание объекта Strength из попки с проходами.
        """
        dir_name_with_suffix = extract_basename(os.path.basename(path_dir))
        basename = extract_basename(path_dir)
        tool, material, coating, feed, spindle_speed, stage = basename.split(';')
        data_frame = pd.read_csv(f'{path_dir}/{dir_name_with_suffix}_силы.csv', sep=';', decimal=',', index_col=0)

        with open(f'{path_dir}/{dir_name_with_suffix}_info.txt', 'r') as info_file:
            text = info_file.readlines()
            info_dict = {elem.split(':')[0]: elem.split(':')[1].strip() for elem in text}

        strength = cls(path_strength="",
                       material=material,
                       coating=coating, tool=tool,
                       feed=float(feed),
                       spindle_speed=float(spindle_speed),
                       stage=stage,
                       from_files=True)

        strength.data_frame = data_frame
        strength.start_day = info_dict['Start']
        strength.last_day = info_dict['End']
        strength.unique_id = info_dict['Unique ID']
        strength.passes = int(info_dict['Passes'])
        strength.strength_mean = float(info_dict['Strength mean'])
        strength.coefficient_mnk = float(info_dict['w0']), float(info_dict['w1'])
        strength.equation_mnk = info_dict['Equation']
        strength.processing_time = float(info_dict['Processing time'])
        strength.filename = os.path.basename(path_dir)
        return strength


class Temperature:
    """
    Создание объекта Temperature из директории с данными.
    """

    def __init__(self, path_temperature: str,
                 material: str,
                 coating: str,
                 tool: str,
                 feed: float | int,
                 spindle_speed: float | int,
                 stage: str,
                 min_voltage: float | int = 6,
                 from_files: bool = False,
                 percent: float | int = 0.22,
                 couple_strength: Strength = None):
        self.material = material
        self.coating = coating
        self.tool = tool
        self.feed = feed
        self.spindle_speed = spindle_speed
        self.stage = stage
        if not from_files:
            list_file = create_file_list(path_temperature)
            list_data = [create_data_frame_temperature(path_t) for path_t in list_file]
            self.data_frame = create_data_frame_temperature_from_list(list_data, min_voltage,
                                                                      couple_strength.processing_time)
            self.couple_strength_data = couple_strength.data_frame
            self.unique_id = str(uuid.uuid4())
            self.filename_base = f'{tool};{material};{coating};{feed};{spindle_speed};{stage}'
            self.filename = self.filename_base
            self.passes = len(list_data)
            self.data_frame['Temperature'] = round(self.data_frame['Voltage'] * 24.08, 2)
            self.coefficient_mnk = determining_coefficient_without_bad_data(self.data_frame[["Time", "Temperature"]],
                                                                            percent=percent)
            self.data_frame['Model_temp'] = predict(*self.coefficient_mnk, self.data_frame['Time'])
            self.temperature_mean = self.data_frame['Temperature'].mean()
            self.equation_mnk = f"{self.coefficient_mnk[0]:.2f}  +  {self.coefficient_mnk[1]:.2f}\u00b7t = T"

            if couple_strength:
                self.processing_time = couple_strength.processing_time
            else:
                self.processing_time = self.data_frame['Time'].iloc[-1]

    def save_file(self, path_dir: str, couple_strength: Strength = None) -> None:
        """
        Сохранение информации в текстовый файл, excel файл
        """
        if couple_strength:
            filename = couple_strength.filename
            with open(f'{path_dir}/{filename}/{filename}_info.txt', 'a') as info_file:
                info_file.write(f'Temperature_mean: {self.temperature_mean}\n')
                info_file.write(f'w0_t: {self.coefficient_mnk[0]}\n')
                info_file.write(f'w1_t: {self.coefficient_mnk[1]}\n')
                info_file.write(f'Equation_temperature: {self.equation_mnk}\n')
                info_file.write(f'Unique_temperature ID: {self.unique_id}\n')

            self.data_frame.to_csv(f'{path_dir}/{filename}/{filename}_temperature.csv', sep=';', decimal=',')
            with pd.ExcelWriter(f'{path_dir}/{filename}/{filename}.xlsx') as writer:
                self.couple_strength_data.to_excel(writer, sheet_name='Data_strength')
                self.data_frame.to_excel(writer, sheet_name='Data_temperature')

        else:
            temperature_dir = os.path.join(path_dir, self.filename_base)
            counter = 1
            while os.path.exists(temperature_dir):
                temperature_dir = os.path.join(path_dir, f'{self.filename_base}_{counter}')
                counter += 1

            self.filename = os.path.basename(temperature_dir)
            os.makedirs(temperature_dir)

            # Сохранение информации в текстовый файл
            with open(f'{temperature_dir}/{self.filename}_info.txt', 'w') as info_file:
                info_file.write(f'Material: {self.material}\n')
                info_file.write(f'Coating: {self.coating}\n')
                info_file.write(f'Tool: {self.tool}\n')
                info_file.write(f'Feed: {self.feed}\n')
                info_file.write(f'Spindle Speed: {self.spindle_speed}\n')
                info_file.write(f'Stage: {self.stage}\n')
                info_file.write(f'Temperature mean: {self.temperature_mean}\n')
                info_file.write(f'Equation_temperature: {self.equation_mnk}\n')
                info_file.write(f'w0_t: {self.coefficient_mnk[0]}\n')
                info_file.write(f'w1_t: {self.coefficient_mnk[1]}\n')
                info_file.write(f'Unique_temperature ID: {self.unique_id}\n')
                info_file.write(f'Passes: {self.passes}\n')
                info_file.write(f'Processing time: {self.processing_time}\n')

            self.data_frame.to_csv(f'{temperature_dir}/{self.filename}_temperature.csv', sep=';', decimal=',')
            with pd.ExcelWriter(f'{temperature_dir}/{self.filename}.xlsx') as writer:
                self.data_frame.to_excel(writer, sheet_name='Data_temperature')

    @classmethod
    def from_dir(cls, path_dir: str):
        """
        Создание объекта Temperature из директории с данными
        """
        dir_name_with_suffix = extract_basename(os.path.basename(path_dir))
        basename = extract_basename(path_dir)
        tool, material, coating, feed, spindle_speed, stage = basename.split(';')
        data_frame = pd.read_csv(f'{path_dir}/{dir_name_with_suffix}_temperature.csv', sep=';', decimal=',',
                                 index_col=0)

        with open(f'{path_dir}/{dir_name_with_suffix}_info.txt', 'r') as info_file:
            text = info_file.readlines()
            info_dict = {elem.split(':')[0]: elem.split(':')[1].strip() for elem in text}

        temperature = cls(path_temperature="",
                          material=material,
                          coating=coating,
                          tool=tool,
                          feed=float(feed),
                          spindle_speed=float(spindle_speed),
                          stage=stage,
                          from_files=True)

        temperature.data_frame = data_frame
        temperature.unique_id = info_dict['Unique_temperature ID']
        temperature.passes = int(info_dict['Passes'])
        temperature.temperature_mean = float(info_dict['Temperature_mean'])
        temperature.coefficient_mnk = float(info_dict['w0_t']), float(info_dict['w1_t'])
        temperature.equation_mnk = info_dict['Equation_temperature']
        temperature.processing_time = float(info_dict['Processing time'])
        return temperature


class Couple:
    def __init__(self, strength: Strength, temperature: Temperature) -> None:
        """
        Класс для хранения информации о силе и температуре
        """
        self.couple_data: pd.DataFrame = pd.DataFrame()
        self.strength = strength
        self.temperature = temperature
        self.merge_file()

    def merge_file(self):
        self.couple_data = pd.merge(self.strength.data_frame,
                                    self.temperature.data_frame,
                                    how='outer',
                                    on='Time').sort_values(by='Time', ascending=True).reset_index(drop=True)
        return self.couple_data

    def save_file(self, path_dir: str) -> None:
        """
        Сохранение информации в текстовый файл, excel файл
        """
        self.strength.save_file(path_dir)
        self.temperature.save_file(path_dir, self.strength)

        with pd.ExcelWriter(f'{path_dir}/{self.temperature.filename}/{self.temperature.filename}.xlsx') as writer:
            self.temperature.data_frame.to_excel(writer, sheet_name='Data_temperature')
            self.strength.data_frame.to_excel(writer, sheet_name='Data_strength')
            self.couple_data.to_excel(writer, sheet_name='Couple_data')

        data_base = shelve.open(f'{path_dir}/data_base/shelve_db')
        data_base[self.strength.filename] = self
        data_base.close()

    @classmethod
    def from_dir(cls, path_dir: str):
        return cls(Strength.from_dir(path_dir), Temperature.from_dir(path_dir))

    def __str__(self):
        return f"{self.strength.filename}"


if __name__ == '__main__':

    # path_s = r"C:\Анализ данных\Пара Сила+температура\4 этап\HN50\nACo3\Силы"
    # # path_ = r"D:\Пара Сила+температура\4 этап\HN58\new party\ALTIN\Силы"
    # strength_ = Strength(path_strength=path_s,
    #                      material='ХН50',
    #                      coating='nACo3',
    #                      tool='Фреза 12',
    #                      feed=58,
    #                      spindle_speed=800,
    #                      stage='4')
    #
    # path_ = r"C:\Анализ данных\Пара Сила+температура\4 этап\HN50\nACo3\Температура"
    # temperature_ = Temperature(path_temperature=path_,
    #                            material='ХН50',
    #                            coating='nACo3',
    #                            tool='Фреза 12',
    #                            feed=58,
    #                            spindle_speed=800,
    #                            stage='4',
    #                            couple_strength=strength_)
    # # temperature_.save_file(new_path, couple_strength=strength_)
    #
    # couple_ = Couple(strength=strength_, temperature=temperature_)
    # couple_.save_file(r"C:\Users\aples\PycharmProjects\AnaliticData\files")

    # couple_ = Couple.from_dir(r"C:\Users\aples\PycharmProjects\AnaliticData\files\Фреза 12;ХН50;nACo3;58;800;4")
    # db = shelve.open(r"C:\Users\aples\PycharmProjects\AnaliticData\Shelve_db\data_base")
    # db[couple_.strength.filename] = couple_
    # db.close()

    db = shelve.open(r"C:\Users\aples\PycharmProjects\AnaliticData\files\data_base\shelve_db")
    couple_ = db['Фреза 12;ХН50;nACo3;58;800;4']
    keys = db.keys()
    db.close()
    print(keys)

