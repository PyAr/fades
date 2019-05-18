import json
import pytest

from fades import parsing

from conftest import get_req, get_distrib


@pytest.mark.parametrize("req,installed,expected", [
    ("==5", "5", "ok"),
    ("==5", "2", None),
    (">5", "4", None),
    (">5", "5", None),
    (">5", "6", "ok"),
    (">=5", "4", None),
    (">=5", "5", "ok"),
    (">=5", "6", "ok"),
    ("<5", "4", "ok"),
    ("<5", "5", None),
    ("<5", "6", None),
    ("<=5", "4", "ok"),
    ("<=5", "5", "ok"),
    ("<=5", "6", None),
    ("== 2.5", "2.5.0", "ok"),
    ("> 2.7", "2.12", "ok"),
    ("> 2.7a0", "2.7", "ok"),
    ("> 2.7", "2.7a0", None),
    (">1.6,<1.9,!=1.9.6", "1.5.0", None),
    (">1.6,<1.9,!=1.9.6", "1.6.7", "ok"),
    (">1.6,<1.9,!=1.8.6", "1.8.7", "ok"),
    (">1.6,<1.9,!=1.9.6", "1.9.6", None),
])
def test_check_versions(venvscache, req, installed, expected):
    """The comparison in the selection."""
    reqs = {"pypi": get_req("dep" + req)}
    interpreter = "pythonX.Y"
    options = {"foo": "bar"}
    venv = json.dumps({
        "metadata": "ok",
        "installed": {"pypi": {"dep": installed}},
        "interpreter": "pythonX.Y",
        "options": {"foo": "bar"}
    })
    resp = venvscache._select([venv], reqs, interpreter, uuid="", options=options)
    assert resp == expected


@pytest.mark.parametrize("possible_venvs", [
    [
        (get_distrib(('dep', '3')), 'venv_best_fit'),
    ],
    [
        (get_distrib(('dep1', '3'), ('dep2', '3')), 'venv_best_fit'),
    ],
    [
        (get_distrib(('dep', '5')), 'venv_best_fit'),
        (get_distrib(('dep', '3')), 'venv_1'),
    ],
    [
        (get_distrib(('dep1', '5'), ('dep2', '7')), 'venv_best_fit'),
        (get_distrib(('dep1', '3'), ('dep2', '6')), 'venv_1'),
    ],
    [
        (get_distrib(('dep1', '3'), ('dep2', '9')), 'venv_1'),
        (get_distrib(('dep1', '5'), ('dep2', '7')), 'venv_best_fit'),
    ],
    [
        (get_distrib(('dep1', '5'), ('dep2', '7')), 'venv_1'),
        (get_distrib(('dep1', '3'), ('dep2', '9')), 'venv_best_fit'),
    ],
    [
        (get_distrib(('dep1', '3'), ('dep2', '9'), ('dep3', '4')), 'venv_best_fit'),
        (get_distrib(('dep1', '5'), ('dep2', '7'), ('dep3', '2')), 'venv_1'),
    ],
    [
        (get_distrib(('dep2', '3'), ('dep1', '2'), ('dep3', '8')), 'venv_best_fit'),
        (get_distrib(('dep1', '7'), ('dep3', '5'), ('dep2', '2')), 'venv_1'),
    ],
    [
        (get_distrib(('dep1', '3'), ('dep2', '2')), 'venv_1'),
        (get_distrib(('dep1', '4'), ('dep2', '2')), 'venv_2'),
        (get_distrib(('dep1', '5'), ('dep2', '7')), 'venv_best_fit'),
        (get_distrib(('dep1', '5'), ('dep2', '6')), 'venv_3'),
    ],
    [
        ([parsing.VCSDependency('someurl')], 'venv_best_fit'),
    ],
    [
        ([parsing.VCSDependency('someurl')] + get_distrib(('dep', '3')), 'venv_best_fit'),
    ],
    [
        ([parsing.VCSDependency('someurl')] + get_distrib(('dep', '3')), 'venv_best_fit'),
        ([parsing.VCSDependency('someurl')] + get_distrib(('dep', '1')), 'venv_1'),
    ],
])
def test_best_fit(venvscache, possible_venvs):
    """Check the venv best fitting decissor."""
    assert venvscache._select_better_fit(possible_venvs) == 'venv_best_fit'
