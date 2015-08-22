# Copyright 2015 Facundo Batista, Nicolás Demarchi
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

"""Tests for the helpers."""

import json
import os
import tempfile
import time
import unittest
from threading import Thread
from unittest.mock import patch

from pkg_resources import parse_requirements

from fades import cache


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))


class TempfileTestCase(unittest.TestCase):
    """Basic functionality tests."""

    def setUp(self):
        _, self.tempfile = tempfile.mkstemp(prefix="test-temp-file")
        self.addCleanup(lambda: os.path.exists(self.tempfile) and os.remove(self.tempfile))


class GetTestCase(TempfileTestCase):
    """A shallow 'get'."""

    def test_missing_file(self):
        os.remove(self.tempfile)
        venvscache = cache.VEnvsCache(self.tempfile)
        with patch.object(venvscache, '_select') as mock:
            mock.return_value = None
            resp = venvscache.get_venv('requirements', 'interpreter')
        mock.assert_called_with([], 'requirements', 'interpreter')
        self.assertEqual(resp, None)

    def test_empty_file(self):
        open(self.tempfile, 'wt', encoding='utf8').close()
        venvscache = cache.VEnvsCache(self.tempfile)
        with patch.object(venvscache, '_select') as mock:
            mock.return_value = None
            resp = venvscache.get_venv('requirements', 'interpreter')
        mock.assert_called_with([], 'requirements', 'interpreter')
        self.assertEqual(resp, None)

    def test_some_file_content(self):
        with open(self.tempfile, 'wt', encoding='utf8') as fh:
            fh.write('foo\nbar\n')
        venvscache = cache.VEnvsCache(self.tempfile)
        with patch.object(venvscache, '_select') as mock:
            mock.return_value = 'resp'
            resp = venvscache.get_venv('requirements', 'interpreter')
        mock.assert_called_with(['foo', 'bar'], 'requirements', 'interpreter')
        self.assertEqual(resp, 'resp')


class StoreTestCase(TempfileTestCase):
    """Store what received."""

    def test_missing_file(self):
        venvscache = cache.VEnvsCache(self.tempfile)
        venvscache.store('installed', 'metadata', 'interpreter')

        with open(self.tempfile, 'rt', encoding='utf8') as fh:
            data = json.loads(fh.readline())
            self.assertTrue('timestamp' in data)
            self.assertEqual(data['installed'], 'installed')
            self.assertEqual(data['metadata'], 'metadata')
            self.assertEqual(data['interpreter'], 'interpreter')

    def test_with_previous_content(self):
        with open(self.tempfile, 'wt', encoding='utf8') as fh:
            fh.write(json.dumps({'foo': 'bar'}) + '\n')

        venvscache = cache.VEnvsCache(self.tempfile)
        venvscache.store('installed', 'metadata', 'interpreter')

        with open(self.tempfile, 'rt', encoding='utf8') as fh:
            data = json.loads(fh.readline())
            self.assertEqual(data, {'foo': 'bar'})

            data = json.loads(fh.readline())
            self.assertTrue('timestamp' in data)
            self.assertEqual(data['installed'], 'installed')
            self.assertEqual(data['metadata'], 'metadata')
            self.assertEqual(data['interpreter'], 'interpreter')


class RemoveTestCase(TempfileTestCase):
    """Remove virtualenv from cache."""

    def test_missing_file(self):
        venvscache = cache.VEnvsCache(self.tempfile)
        venvscache.remove('missing/path')

        lines = venvscache._read_cache()
        self.assertEqual(lines, [])

    def test_missing_env_in_cache(self):
        venvscache = cache.VEnvsCache(self.tempfile)
        venvscache.store('installed', {'env_path': 'some/path'}, 'interpreter')
        lines = venvscache._read_cache()
        assert len(lines) == 1

        venvscache.remove('some/path')

        lines = venvscache._read_cache()
        self.assertEqual(lines, [])

    def test_preserve_cache_data_ordering(self):
        venvscache = cache.VEnvsCache(self.tempfile)
        # store 3 venvs
        venvscache.store('installed1', {'env_path': 'path/env1'}, 'interpreter')
        venvscache.store('installed2', {'env_path': 'path/env2'}, 'interpreter')
        venvscache.store('installed3', {'env_path': 'path/env3'}, 'interpreter')

        venvscache.remove('path/env2')

        lines = venvscache._read_cache()
        self.assertEqual(len(lines), 2)
        self.assertEqual(
            json.loads(lines[0]).get('metadata').get('env_path'), 'path/env1')
        self.assertEqual(
            json.loads(lines[1]).get('metadata').get('env_path'), 'path/env3')

    def test_lock_cache_for_remove(self):
        venvscache = cache.VEnvsCache(self.tempfile)
        # store 3 venvs
        venvscache.store('installed1', {'env_path': 'path/env1'}, 'interpreter')
        venvscache.store('installed2', {'env_path': 'path/env2'}, 'interpreter')
        venvscache.store('installed3', {'env_path': 'path/env3'}, 'interpreter')

        # patch _write_cache so it emulates a slow write during which
        # another process managed to modify the cache file before the
        # first process finished writing the modified cache data
        original_write_cache = venvscache._write_cache
        p = patch('fades.cache.VEnvsCache._write_cache')
        mock_write_cache = p.start()

        t1 = Thread(target=venvscache.remove, args=('path/env1',))

        def slow_write_cache(*args, **kwargs):
            p.stop()
            t1.start()
            # wait to ensure t1 thread must wait for lock to be released
            time.sleep(0.01)
            original_write_cache(*args, **kwargs)

        mock_write_cache.side_effect = slow_write_cache

        # just a sanity check
        assert not os.path.exists(venvscache.filepath + '.lock')
        # remove a virtualenv from the cache
        venvscache.remove('path/env2')
        t1.join()

        # when cache file is properly locked both virtualenvs
        # will have been removed from the cache
        lines = venvscache._read_cache()
        self.assertEqual(len(lines), 1)
        self.assertEqual(
            json.loads(lines[0]).get('metadata').get('env_path'), 'path/env3')
        self.assertFalse(os.path.exists(venvscache.filepath + '.lock'))


class SelectionTestCase(TempfileTestCase):
    """The venv selection."""

    def setUp(self):
        super().setUp()
        self.venvscache = cache.VEnvsCache(self.tempfile)

    def test_empty(self):
        resp = self.venvscache._select([], {}, 'pythonX.Y')
        self.assertEqual(resp, None)

    def test_nomatch_repo(self):
        reqs = {'repoloco': get_req('dep == 5')}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '5'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, None)

    def test_nomatch_dependency(self):
        reqs = {'pypi': get_req('dep1 == 5')}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep2': '5'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, None)

    def test_nomatch_version(self):
        reqs = {'pypi': get_req('dep == 5')}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '7'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, None)

    def test_simple_match(self):
        reqs = {'pypi': get_req('dep == 5')}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '5'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, 'foobar')

    def test_match_noversion(self):
        reqs = {'pypi': get_req('dep')}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep': '5'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, 'foobar')

    def test_middle_match(self):
        reqs = {'pypi': get_req('dep == 5')}
        interpreter = 'pythonX.Y'
        venv1 = json.dumps({
            'metadata': 'venv1',
            'installed': {'pypi': {'dep': '3'}},
            'interpreter': 'pythonX.Y',
        })
        venv2 = json.dumps({
            'metadata': 'venv2',
            'installed': {'pypi': {'dep': '5'}},
            'interpreter': 'pythonX.Y',
        })
        venv3 = json.dumps({
            'metadata': 'venv3',
            'installed': {'pypi': {'dep': '5'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv1, venv2, venv3], reqs, interpreter)
        self.assertEqual(resp, 'venv2')

    def test_multiple_deps_ok(self):
        reqs = {'pypi': get_req(['dep1 == 5', 'dep2 == 7'])}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep2': '7'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, 'foobar')

    def test_multiple_deps_just_one(self):
        reqs = {'pypi': get_req(['dep1 == 5', 'dep2 == 7'])}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep2': '2'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, None)

    def test_not_too_crowded(self):
        reqs = {'pypi': get_req(['dep1'])}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep2': '2'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, None)

    def test_same_quantity_different_deps(self):
        reqs = {'pypi': get_req(['dep1', 'dep2'])}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep3': '2'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, None)

    def test_no_requirements_some_installed(self):
        reqs = {}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {'pypi': {'dep1': '5', 'dep3': '2'}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, None)

    def test_no_requirements_empty_venv(self):
        reqs = {}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'foobar',
            'installed': {},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        self.assertEqual(resp, 'foobar')


class ComparisonsTestCase(TempfileTestCase):
    """The comparison in the selection."""

    def setUp(self):
        super().setUp()
        self.venvscache = cache.VEnvsCache(self.tempfile)

    def check(self, req, installed):
        """Check if the requirement is satisfied with what is installed."""
        reqs = {'pypi': get_req('dep' + req)}
        interpreter = 'pythonX.Y'
        venv = json.dumps({
            'metadata': 'ok',
            'installed': {'pypi': {'dep': installed}},
            'interpreter': 'pythonX.Y',
        })
        resp = self.venvscache._select([venv], reqs, interpreter)
        return resp

    def test_comp_eq(self):
        self.assertEqual(self.check('==5', '5'), 'ok')
        self.assertEqual(self.check('==5', '2'), None)

    def test_comp_gt(self):
        self.assertEqual(self.check('>5', '4'), None)
        self.assertEqual(self.check('>5', '5'), None)
        self.assertEqual(self.check('>5', '6'), 'ok')

    def test_comp_ge(self):
        self.assertEqual(self.check('>=5', '4'), None)
        self.assertEqual(self.check('>=5', '5'), 'ok')
        self.assertEqual(self.check('>=5', '6'), 'ok')

    def test_comp_lt(self):
        self.assertEqual(self.check('<5', '4'), 'ok')
        self.assertEqual(self.check('<5', '5'), None)
        self.assertEqual(self.check('<5', '6'), None)

    def test_comp_le(self):
        self.assertEqual(self.check('<=5', '4'), 'ok')
        self.assertEqual(self.check('<=5', '5'), 'ok')
        self.assertEqual(self.check('<=5', '6'), None)

    def test_complex_cases(self):
        self.assertEqual(self.check('== 2.5', '2.5.0'), 'ok')
        self.assertEqual(self.check('> 2.7', '2.12'), 'ok')
        self.assertEqual(self.check('> 2.7a0', '2.7'), 'ok')
        self.assertEqual(self.check('> 2.7', '2.7a0'), None)

    def test_crazy_picky(self):
        self.assertEqual(self.check('>1.6,<1.9,!=1.9.6', '1.5.0'), None)
        self.assertEqual(self.check('>1.6,<1.9,!=1.9.6', '1.6.7'), 'ok')
        self.assertEqual(self.check('>1.6,<1.9,!=1.8.6', '1.8.7'), 'ok')
        self.assertEqual(self.check('>1.6,<1.9,!=1.9.6', '1.9.6'), None)
