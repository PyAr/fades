# Copyright 2015-2026 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

import uuid

from fades import helpers, parsing
from tests import get_reqs


def test_empty(venvscache):
    resp = venvscache._select([], {}, 'pythonX.Y', 'options')
    assert resp is None


def test_nomatch_repo_dependency(venvscache, fake_venv):
    reqs = {"repoloco": get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'pypi': {'dep': '5'}})
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_nomatch_pypi_dependency(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep1 == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'pypi': {'dep2': '5'}})
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    resp is None


def test_nomatch_vcs_dependency(venvscache, fake_venv):
    reqs = {'vcs': [parsing.VCSDependency('someurl')]}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'vcs': {'otherurl': None}})
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_nomatch_version(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'pypi': {'dep': '7'}})
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_simple_pypi_match(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv("foobar", installed={'pypi': {'dep': '5'}})
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == 'foobar'


def test_simple_vcs_match(venvscache, fake_venv):
    reqs = {'vcs': [parsing.VCSDependency('someurl')]}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv("foobar", installed={'vcs': {'someurl': None}})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == 'foobar'


def test_match_mixed_single(venvscache, fake_venv):
    reqs = {'vcs': [parsing.VCSDependency('someurl')], 'pypi': get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = fake_venv("foobar1", installed={'vcs': {'someurl': None}, 'pypi': {'dep': '5'}})
    venv2 = fake_venv("foobar2", installed={'pypi': {'dep': '5'}})
    venv3 = fake_venv("foobar3", installed={'vcs': {'someurl': None}})
    resp = venvscache ._select(
        [venv1, venv2, venv3], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == 'foobar1'


def test_match_mixed_multiple(venvscache, fake_venv):
    reqs = {'vcs': [parsing.VCSDependency('url1'), parsing.VCSDependency('url2')],
            'pypi': get_reqs('dep1 == 5', 'dep2')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv("foobar", installed={
        'vcs': {'url1': None, 'url2': None},
        'pypi': {'dep1': '5', 'dep2': '7'},
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == 'foobar'


def test_match_noversion(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv("foobar", installed={'pypi': {'dep': '5'}})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == 'foobar'


def test_middle_match(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = fake_venv("venv1", installed={'pypi': {'dep': '3'}})
    venv2 = fake_venv("venv2", installed={'pypi': {'dep': '5'}})
    venv3 = fake_venv("venv3", installed={'pypi': {'dep': '7'}})
    resp = venvscache ._select([venv1, venv2, venv3], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == 'venv2'


def test_multiple_match_bigger_version(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = fake_venv("venv1", installed={'pypi': {'dep': '3'}})
    venv2 = fake_venv("venv2", installed={'pypi': {'dep': '7'}})
    venv3 = fake_venv("venv3", installed={'pypi': {'dep': '5'}})
    resp = venvscache ._select([venv1, venv2, venv3], reqs, interpreter, uuid='',
                               options=options)
    # matches venv2 because it has the bigger version for 'dep' (even if it's not the
    # latest virtualenv created)
    assert resp["extra"] == 'venv2'


def test_multiple_deps_ok(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep1 == 5', 'dep2 == 7')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv("foobar", installed={'pypi': {'dep1': '5', 'dep2': '7'}})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == 'foobar'


def test_multiple_deps_just_one(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep1 == 5', 'dep2 == 7')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'pypi': {'dep1': '5', 'dep2': '2'}})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_not_too_crowded(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep1')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'pypi': {'dep1': '5', 'dep2': '2'}})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_same_quantity_different_deps(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep1', 'dep2')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'pypi': {'dep1': '5', 'dep3': '2'}})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_no_requirements_some_installed(venvscache, fake_venv):
    reqs = {}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv(installed={'pypi': {'dep1': '5', 'dep3': '2'}})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_no_requirements_empty_venv(venvscache, fake_venv):
    reqs = {}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv("foobar", installed={})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == "foobar"


def test_simple_match_empty_options(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {}
    venv = fake_venv("foobar", installed={'pypi': {'dep': '5'}}, options={})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == "foobar"


def test_no_match_due_to_options(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = fake_venv("foobar", installed={'pypi': {'dep': '5'}}, options={})
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_match_due_to_options(venvscache, fake_venv):
    reqs = {'pypi': get_reqs('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = fake_venv("venv1", installed={'pypi': {'dep': '5'}}, options={})
    venv2 = fake_venv("venv2", installed={'pypi': {'dep': '5'}}, options={'foo': 'bar'})
    resp = venvscache ._select([venv1, venv2], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == "venv2"


def test_no_deps_but_options(venvscache, fake_venv):
    reqs = {}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = fake_venv("venv1", installed={}, options={})
    venv2 = fake_venv("venv2", installed={}, options={'foo': 'bar'})
    resp = venvscache ._select([venv1, venv2], reqs, interpreter, uuid='', options=options)
    assert resp["extra"] == "venv2"


def test_match_uuid(venvscache, fake_venv):
    venv_uuid = str(uuid.uuid4())
    metadata = {
        "env_path": str(helpers.get_basedir() / venv_uuid),
        "env_bin_path": str(helpers.get_basedir() / "other"),
        "extra": "foobar",
    }
    venv = fake_venv(metadata=metadata, installed={})
    resp = venvscache ._select([venv], uuid=venv_uuid)
    assert resp["extra"] == "foobar"
