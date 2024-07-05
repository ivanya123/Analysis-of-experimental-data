import pytest
from analytical_functions.analysis_functions import extract_param_path


def test_extract_param_path_1():
    path = r"D:\Пара Сила+температура\5 этап\HN58\AlTiCrN3\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('ХН58', 'AlTiCrN3', 'Фреза 12', '5 этап')


def test_extract_param_path_2():
    path = r"F:\Пара Сила+температура\4 этап\HN58\ALTIN\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('ХН58', 'AlTiN3', 'Фреза 12', '4 этап')


def test_extract_param_path_3():
    path = r"D:\Пара Сила+температура\4 этап\VT18U\nACo3\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('ВТ18У', 'nACo3', 'Фреза 12', '4 этап')


def test_extract_param_path_4():
    path = r"D:\Пара Сила+температура\4 этап\VT18U\nACO3+TiB2\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('ВТ18У', 'nACo3+TiB2', 'Фреза 12', '4 этап')


def test_extract_param_path_5():
    path = r"D:\Пара Сила+температура\5 этап\HN58\AlTiCrN3 2\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('ХН58', 'AlTiCrN3', 'Фреза 12', '5 этап')


def test_extract_param_path_6():
    path = r"D:\Пара Сила+температура\5 этап\HN58\AlTiCrN3----2\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('Неизвестно', 'Неизвестно', 'Фреза 12', 'Неизвестно')


def test_extract_param_path_7():
    path = r"C:\Анализ данных\Пара Сила+температура\6 этап\Хн 58\Хн 58 нью\nACo3 1\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('ХН58', 'nACo3', 'Фреза 12', '6 этап')


def test_extract_param_path_8():
    path = r"C:\Анализ данных\Пара Сила+температура\6 этап\ХН 50 new\nACo3+TiB2 13\Силы".replace("\\", "/")
    result = extract_param_path(path)
    assert result == ('ХН50', 'nACo3+TiB2', 'Фреза 12', '6 этап')




if __name__ == "__main__":
    pytest.main()
