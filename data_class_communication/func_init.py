import pandas as pd
import os
from analytical_functions.analysis_functions import add_names_fields, determination_zero_strength, processing_time \
    , adding_time_in_temperature
import re
from typing import Optional
import numpy as np


def create_file_list(path: str) -> list[str]:
    try:
        list_file = [os.path.join(path, x) for x in os.listdir(path)]
        date_list = [[x, os.path.getmtime(x)] for x in list_file]
        sort_date_list = [elem[0] for elem in sorted(date_list, key=lambda x: x[1], reverse=False)]
        return sort_date_list
    except:
        raise FileNotFoundError


def create_data_frame_strength(path: str, min_strength: float | int) -> pd.DataFrame:
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


def create_data_frame_temperature(path: str) -> pd.DataFrame:
    data_frame = pd.read_csv(path,
                             encoding='windows-1251',
                             on_bad_lines='skip',
                             sep='\t',
                             header=11,
                             names=['Time', 'Voltage'],
                             decimal=',',
                             dtype='float')

    return data_frame


def create_data_strength_from_list(list_data_frame: list[pd.DataFrame], min_strength: float | int) -> pd.DataFrame:
    data_frame = pd.concat(list_data_frame, ignore_index=True)
    data_frame = data_frame.loc[data_frame['Fy'] > min_strength]
    time_field = data_frame['Time'].to_numpy()
    data_frame['Time'] = processing_time(time_field)
    data_frame['Time'] = data_frame['Time'].apply(np.ceil)
    df = data_frame.groupby(by='Time').mean().dropna().reset_index()
    df['Fy'] = df['Fy'].apply(lambda x: round(x, 2))
    return df


def create_data_frame_temperature_from_list(list_data_frame: list[pd.DataFrame],
                                            min_voltage: float | int,
                                            processing_time_: Optional[float] = None) -> pd.DataFrame:
    data_frame = pd.concat(list_data_frame, ignore_index=True)
    data_frame = data_frame.loc[data_frame['Voltage'] > min_voltage]
    time_field = data_frame['Time'].to_numpy()
    data_frame['Time'] = adding_time_in_temperature(time_field, processing_time_)
    data_frame['Time'] = data_frame['Time'].apply(np.ceil)
    df = data_frame.groupby(by='Time').mean().dropna().reset_index()
    df['Voltage']  = df['Voltage'].apply(lambda x: round(x, 2))
    return df


def extract_basename(filename):
    # Извлечение базового имени файла без суффикса
    match = re.match(r"^(.*?)(?:_\d+)?$", filename)
    return match.group(1)
