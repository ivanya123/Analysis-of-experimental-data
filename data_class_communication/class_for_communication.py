import os
import pandas as pd
from analytical_functions.analysis_functions import add_names_fields, determination_zero_strength, processing_time
import time


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
        data_frame = pd.read_csv(path, sep=';', header=2, decimal=',', dtype='float')
        data_frame = add_names_fields(data_frame)
        data_frame = determination_zero_strength(data_frame, min_strength)
        return data_frame
    except:
        data_frame = pd.read_csv(path, sep=';', header=2, decimal=',', dtype='float')
        data_frame = add_names_fields(data_frame)
        data_frame = determination_zero_strength(data_frame, min_strength)
        return data_frame


def create_data_strength_from_list(list_data_frame: list[pd.DataFrame], min_strength: float | int) -> pd.DataFrame:
    data_frame = pd.concat(list_data_frame, ignore_index=True)
    data_frame = data_frame.loc[data_frame['Fy'] > min_strength]
    time_field = data_frame['Time'].to_numpy()
    data_frame['Time'] = processing_time(time_field)
    return data_frame


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
                 from_files: bool = False):
        self.material = material
        self.coating = coating
        self.tool = tool
        self.feed = feed
        self.spindle_speed = spindle_speed
        self.stage = stage
        self.list_file = create_file_list(path_strength)
        self.list_data = [create_data_frame(path_s, min_strength) for path_s in self.list_file]
        self.data_frame = create_data_strength_from_list(self.list_data, min_strength)

        self.start_day = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(os.path.getmtime(self.list_file[0])))
        self.last_day = time.strftime('%Y.%m.%d-%H:%M:%S', time.localtime(os.path.getmtime(self.list_file[-1])))


if __name__ == '__main__':
    path_ = r"C:\Анализ данных\Пара Сила+температура\4 этап\HN58\ALTIN\Силы"
    print(create_file_list(path_))
