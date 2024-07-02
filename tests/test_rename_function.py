import pytest
from analytical_functions.analysis_functions import rename_coating, rename_materials
from analytical_functions.constant import dict_rename_coating, dict_rename_material


def test_rename_materials_empty_string():
    assert (rename_materials('', dict_rename_material) == '')


def test_rename_materials_vt18ug():
    assert (rename_materials('VT18U', dict_rename_material) == 'ВТ18У')


def test_rename_materials_no_string():
    with pytest.raises(TypeError):
        rename_materials(123, dict_rename_material)


def test_rename_materials_vt41():
    assert (rename_materials('VT41', dict_rename_material) == 'ВТ41')


def test_rename_materials_hn50():
    assert (rename_materials('hN50', dict_rename_material) == 'ХН50')


def test_rename_materials_hn58():
    assert (rename_materials('N58', dict_rename_material) == 'ХН58')


def test_rename_coating_empty_string():
    assert (rename_coating('', dict_rename_coating) == '')


def test_rename_coating_altin_tib2():
    assert (rename_coating('ALTIN+TiB2 1 new', dict_rename_coating) == 'AlTiN3+TiB2')


def test_rename_coating_naco():
    assert (rename_coating('nACO3 2нов', dict_rename_coating) == 'nACo3')


def test_rename_coating_no_string():
    with pytest.raises(AttributeError):
        rename_coating(123, dict_rename_coating)


def test_rename_coating_naco3_tib2():
    assert (rename_coating('nACO3+TiB2', dict_rename_coating) == 'nACo3+TiB2')


if __name__ == '__main__':
    pytest.main()
