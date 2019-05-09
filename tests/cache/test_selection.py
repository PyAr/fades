import os
import json
import uuid

from fades import helpers, parsing
from tests.conftest import get_req


def test_empty(venvscache):
    resp = venvscache._select([], {}, 'pythonX.Y', 'options')
    assert resp is None


def test_nomatch_repo_dependency(venvscache):
    reqs = {"repoloco": get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_nomatch_pypi_dependency(venvscache):
    reqs = {'pypi': get_req('dep1 == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep2': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    resp is None


def test_nomatch_vcs_dependency(venvscache):
    reqs = {'vcs': [parsing.VCSDependency('someurl')]}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'vcs': {'otherurl': None}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_nomatch_version(venvscache):
    reqs = {'pypi': get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep': '7'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_simple_pypi_match(venvscache):
    reqs = {'pypi': get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp == 'foobar'


def test_simple_vcs_match(venvscache):
    reqs = {'vcs': [parsing.VCSDependency('someurl')]}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'vcs': {'someurl': None}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp == 'foobar'


def test_match_mixed_single(venvscache):
    reqs = {'vcs': [parsing.VCSDependency('someurl')], 'pypi': get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = json.dumps({
        'metadata': 'foobar1',
        'installed': {'vcs': {'someurl': None}, 'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    venv2 = json.dumps({
        'metadata': 'foobar2',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    venv3 = json.dumps({
        'metadata': 'foobar3',
        'installed': {'vcs': {'someurl': None}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select(
        [venv1, venv2, venv3], reqs, interpreter, uuid='', options=options)
    assert resp == 'foobar1'


def test_match_mixed_multiple(venvscache):
    reqs = {'vcs': [parsing.VCSDependency('url1'), parsing.VCSDependency('url2')],
            'pypi': get_req(['dep1 == 5', 'dep2'])}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {
            'vcs': {'url1': None, 'url2': None},
            'pypi': {'dep1': '5', 'dep2': '7'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp == 'foobar'


def test_match_noversion(venvscache):
    reqs = {'pypi': get_req('dep')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp == 'foobar'


def test_middle_match(venvscache):
    reqs = {'pypi': get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = json.dumps({
        'metadata': 'venv1',
        'installed': {'pypi': {'dep': '3'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    venv2 = json.dumps({
        'metadata': 'venv2',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    venv3 = json.dumps({
        'metadata': 'venv3',
        'installed': {'pypi': {'dep': '7'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv1, venv2, venv3], reqs, interpreter, uuid='',
                               options=options)
    assert resp == 'venv2'


def test_multiple_match_bigger_version(venvscache):
    reqs = {'pypi': get_req('dep')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = json.dumps({
        'metadata': 'venv1',
        'installed': {'pypi': {'dep': '3'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    venv2 = json.dumps({
        'metadata': 'venv2',
        'installed': {'pypi': {'dep': '7'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    venv3 = json.dumps({
        'metadata': 'venv3',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv1, venv2, venv3], reqs, interpreter, uuid='',
                               options=options)
    # matches venv2 because it has the bigger version for 'dep' (even if it's not the
    # latest virtualenv created)
    assert resp == 'venv2'


def test_multiple_deps_ok(venvscache):
    reqs = {'pypi': get_req(['dep1 == 5', 'dep2 == 7'])}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep1': '5', 'dep2': '7'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp == 'foobar'


def test_multiple_deps_just_one(venvscache):
    reqs = {'pypi': get_req(['dep1 == 5', 'dep2 == 7'])}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep1': '5', 'dep2': '2'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_not_too_crowded(venvscache):
    reqs = {'pypi': get_req(['dep1'])}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep1': '5', 'dep2': '2'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_same_quantity_different_deps(venvscache):
    reqs = {'pypi': get_req(['dep1', 'dep2'])}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep1': '5', 'dep3': '2'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_no_requirements_some_installed(venvscache):
    reqs = {}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep1': '5', 'dep3': '2'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_no_requirements_empty_venv(venvscache):
    reqs = {}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp == "foobar"


def test_simple_match_empty_options(venvscache):
    reqs = {'pypi': get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp == "foobar"


def test_no_match_due_to_options(venvscache):
    reqs = {'pypi': get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv = json.dumps({
        'metadata': 'foobar',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {}
    })
    resp = venvscache ._select([venv], reqs, interpreter, uuid='', options=options)
    assert resp is None


def test_match_due_to_options(venvscache):
    reqs = {'pypi': get_req('dep == 5')}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = json.dumps({
        'metadata': 'venv1',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {}
    })
    venv2 = json.dumps({
        'metadata': 'venv2',
        'installed': {'pypi': {'dep': '5'}},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv1, venv2], reqs, interpreter, uuid='', options=options)
    assert resp == "venv2"


def test_no_deps_but_options(venvscache):
    reqs = {}
    interpreter = 'pythonX.Y'
    options = {'foo': 'bar'}
    venv1 = json.dumps({
        'metadata': 'venv1',
        'installed': {},
        'interpreter': 'pythonX.Y',
        'options': {}
    })
    venv2 = json.dumps({
        'metadata': 'venv2',
        'installed': {},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv1, venv2], reqs, interpreter, uuid='', options=options)
    assert resp == "venv2"


def test_match_uuid(venvscache):
    venv_uuid = str(uuid.uuid4())
    metadata = {
        'env_path': os.path.join(helpers.get_basedir(), venv_uuid),
    }
    venv = json.dumps({
        'metadata': metadata,
        'installed': {},
        'interpreter': 'pythonX.Y',
        'options': {'foo': 'bar'}
    })
    resp = venvscache ._select([venv], uuid=venv_uuid)
    assert resp == metadata
