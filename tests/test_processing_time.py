import numpy as np
import pytest
from analytical_functions.analysis_functions import processing_time


def test_processing_time_main_case():
    start_time = np.array([1, 3, 6, 10, 32, 1, 4])
    result = processing_time(start_time)
    expected = np.array([0, 2, 5, 9, 31, 31, 34])
    np.testing.assert_array_equal(result, expected)


def test_processing_time_zero_case():
    start_time = np.array([0, 0, 0, 0, 0, 0, 0])
    result = processing_time(start_time)
    expected = np.array([0, 0, 0, 0, 0, 0, 0])
    np.testing.assert_array_equal(result, expected)


def test_processing_time_mixed_time():
    start_time = np.array([0, 2, -1, 3])
    with pytest.raises(ValueError, match="Некорректное время"):
        processing_time(start_time)



if __name__ == '__main__':
    pytest.main()
