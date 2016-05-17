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

"""Tests for the venv builder module."""

import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from pkg_resources import parse_requirements

import logassert

from fades import REPO_PYPI, cache, envbuilder
from venv import EnvBuilder


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))[0]


class EnvCreationTestCase(unittest.TestCase):
    """Check all the new venv creation."""

    class FakeManager:
        """A fake repo manager."""
        def __init__(self):
            self.req_installed = []
            self.really_installed = {}

        def install(self, dependency):
            self.req_installed.append(dependency)

        def get_version(self, dependency):
            return self.really_installed[dependency]

    class FailInstallManager(FakeManager):
        def install(self, dependency):
            raise Exception("Kapow!")

    def setUp(self):
        logassert.setup(self, 'fades.envbuilder')

    def test_create_simple(self):
        requested = {
            REPO_PYPI: [get_req('dep1 == v1'), get_req('dep2 == v2')]
        }
        interpreter = 'python3'
        is_current = True
        options = {"virtualenv_options": [],
                   "pyvenv_options": [],
                   }
        pip_options = []
        with patch.object(envbuilder._FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = fake_manager = self.FakeManager()
                fake_manager.really_installed = {'dep1': 'v1', 'dep2': 'v2'}
                venv_data, installed = envbuilder.create_venv(requested, interpreter, is_current,
                                                              options, pip_options)

        self.assertEqual(venv_data, {
            'env_bin_path': 'env_bin_path',
            'env_path': 'env_path',
            'pip_installed': 'pip_installed',
        })
        self.assertDictEqual(installed, {
            REPO_PYPI: {
                'dep1': 'v1',
                'dep2': 'v2',
            }
        })

    def test_unknown_repo(self):
        requested = {
            'unknown': {'dep': ''}
        }
        interpreter = 'python3'
        is_current = True
        options = {"virtualenv_options": [],
                   "pyvenv_options": [],
                   }
        pip_options = []
        with patch.object(envbuilder._FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = self.FakeManager()
                envbuilder.create_venv(requested, interpreter, is_current, options, pip_options)

        self.assertLoggedWarning("Install from 'unknown' not implemented")

    def test_non_existing_dep(self):
        requested = {
            REPO_PYPI: [get_req('dep1 == 1000')]
        }
        interpreter = 'python3'
        is_current = True
        options = {'virtualenv_options': [],
                   'pyvenv_options': [],
                   }
        pip_options = []

        with patch.object(envbuilder._FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = self.FailInstallManager()
                with patch.object(envbuilder, 'destroy_venv', spec=True) as mock_destroy:
                    with self.assertRaises(SystemExit):
                        envbuilder.create_venv(
                            requested,
                            interpreter,
                            is_current,
                            options,
                            pip_options)
                    mock_destroy.assert_called_once_with('env_path')

        self.assertLoggedDebug("Installation Step failed, removing virtualenv")

    def test_different_versions(self):
        requested = {
            REPO_PYPI: [get_req('dep1 == v1'), get_req('dep2 == v2')]
        }
        interpreter = 'python3'
        is_current = True
        options = {"virtualenv_options": [],
                   "pyvenv_options": [],
                   }
        pip_options = []
        with patch.object(envbuilder._FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = fake_manager = self.FakeManager()
                fake_manager.really_installed = {'dep1': 'vX', 'dep2': 'v2'}
                _, installed = envbuilder.create_venv(requested, interpreter, is_current, options,
                                                      pip_options)

        self.assertEqual(installed, {
            REPO_PYPI: {
                'dep1': 'vX',
                'dep2': 'v2',
            }
        })

    def test_create_system_site_pkgs_pyvenv(self):
        env_builder = envbuilder._FadesEnvBuilder()
        interpreter = 'python3'
        is_current = True
        options = {"virtualenv_options": [],
                   "pyvenv_options": ['--system-site-packages'],
                   }
        with patch.object(EnvBuilder, 'create') as mock_create:
                env_builder.create_env(interpreter, is_current, options)
                self.assertTrue(env_builder.system_site_packages)
                self.assertTrue(mock_create.called)

    def test_create_pyvenv(self):
        env_builder = envbuilder._FadesEnvBuilder()
        interpreter = 'python3'
        is_current = True
        options = {"virtualenv_options": [],
                   "pyvenv_options": [],
                   }
        with patch.object(EnvBuilder, 'create') as mock_create:
                env_builder.create_env(interpreter, is_current, options)
                self.assertFalse(env_builder.system_site_packages)
                self.assertTrue(mock_create.called)

    def test_create_system_site_pkgs_virtualenv(self):
        env_builder = envbuilder._FadesEnvBuilder()
        interpreter = 'pythonX.Y'
        is_current = False
        options = {"virtualenv_options": ['--system-site-packages'],
                   "pyvenv_options": [],
                   }
        with patch.object(envbuilder._FadesEnvBuilder, 'create_with_virtualenv') as mock_create:
                env_builder.create_env(interpreter, is_current, options)
                mock_create.assert_called_with(interpreter, options['virtualenv_options'])

    def test_create_virtualenv(self):
        env_builder = envbuilder._FadesEnvBuilder()
        interpreter = 'pythonX.Y'
        is_current = False
        options = {"virtualenv_options": [],
                   "pyvenv_options": [],
                   }
        with patch.object(envbuilder._FadesEnvBuilder, 'create_with_virtualenv') as mock_create:
                env_builder.create_env(interpreter, is_current, options)
                mock_create.assert_called_with(interpreter, options['virtualenv_options'])

    def test_custom_env_path(self):
        builder = envbuilder._FadesEnvBuilder('some-path')
        self.assertEqual(builder.env_path, 'some-path')


class EnvDestructionTestCase(unittest.TestCase):

    def test_destroy_venv(self):
        builder = envbuilder._FadesEnvBuilder()
        # make sure the virtualenv exists on disk
        options = {"virtualenv_options": [],
                   "pyvenv_options": ['--system-site-packages'],
                   "pip-options": [],
                   }
        builder.create_env('python', False, options=options)
        assert os.path.exists(builder.env_path)

        cache_mock = Mock()
        envbuilder.destroy_venv(builder.env_path, cache_mock)
        self.assertFalse(os.path.exists(builder.env_path))
        cache_mock.remove.assert_called_with(builder.env_path)

    def test_destroy_venv_if_env_path_not_found(self):
        builder = envbuilder._FadesEnvBuilder()
        assert not os.path.exists(builder.env_path)

        cache_mock = Mock()
        envbuilder.destroy_venv(builder.env_path, cache_mock)
        self.assertFalse(os.path.exists(builder.env_path))
        cache_mock.remove.assert_called_with(builder.env_path)


class UsageManagerTestCase(unittest.TestCase):

    def setUp(self):
        _, self.tempfile = tempfile.mkstemp(prefix="test-temp-file")
        self.temp_folder = tempfile.mkdtemp()
        self.file_path = os.path.join(self.temp_folder, 'usage_stats')
        self.addCleanup(lambda: os.path.exists(self.tempfile) and os.remove(self.tempfile))

        self.uuids = ['env1', 'env2', 'env3']

        self.venvscache = cache.VEnvsCache(self.tempfile)
        for uuid in self.uuids:
            self.venvscache.store('', {'env_path': os.path.join(self.temp_folder, uuid)}, '', '')

    def get_usage_lines(self, manager):
        self.assertTrue(os.path.exists(self.file_path), msg="File usage exists")
        lines = []
        for line in open(self.file_path).readlines():
            uuid, d = line.split()
            d = manager._str_to_datetime(d)
            lines.append((uuid, d))
        return lines

    def test_file_usage_dont_exists_then_it_is_created_and_initialized(self):
        self.assertFalse(os.path.exists(self.file_path), msg="First file doesn't exists")
        manager = envbuilder.UsageManager(self.file_path, self.venvscache)
        lines = self.get_usage_lines(manager)
        self.assertEqual(len(lines), len(self.uuids), msg="File have one line per venv")

        pending_uuids = self.uuids[:]
        for uuid, dt in lines:
            self.assertTrue(uuid in pending_uuids, msg="Every uuid is in file")
            pending_uuids.remove(uuid)

    def test_usage_record_is_recorded(self):
        manager = envbuilder.UsageManager(self.file_path, self.venvscache)
        lines = self.get_usage_lines(manager)
        self.assertEqual(len(lines), len(self.uuids), msg="File have one line per venv")

        venv = self.venvscache.get_venv(uuid=self.uuids[0])
        manager.store_usage_stat(venv, self.venvscache)

        lines = self.get_usage_lines(manager)
        self.assertEqual(2, len([1 for u, d in lines if u == self.uuids[0]]),
                         msg="Selected uuid is two times in file")

    def test_usage_file_is_compacted_when_though_no_venv_is_removed(self):
        old_date = datetime.utcnow()
        new_date = old_date + timedelta(days=1)

        with patch('fades.envbuilder.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = old_date
            mock_datetime.strptime.side_effect = lambda *args, **kw: datetime.strptime(*args, **kw)
            mock_datetime.strftime.side_effect = lambda *args, **kw: datetime.strftime(*args, **kw)

            manager = envbuilder.UsageManager(self.file_path, self.venvscache)
            lines = self.get_usage_lines(manager)
            for u, d in lines:
                self.assertEqual(old_date, d, msg="All records have the same date")

            venv = self.venvscache.get_venv(uuid=self.uuids[0])
            manager.store_usage_stat(venv, self.venvscache)

            mock_datetime.utcnow.return_value = new_date
            manager.store_usage_stat(venv, self.venvscache)

            lines = self.get_usage_lines(manager)
            self.assertEqual(len(self.uuids) + 2, len(lines))

            manager.clean_unused_venvs(4)
            lines = self.get_usage_lines(manager)
            self.assertEqual(len(self.uuids), len(lines))

            for u, d in lines:
                if u == self.uuids[0]:
                    self.assertEqual(new_date, d, msg="Selected env have new date")
                else:
                    self.assertEqual(old_date, d, msg="Others envs have old date")

    def test_when_a_venv_is_removed_it_is_removed_from_everywhere(self):
        old_date = datetime.utcnow()
        new_date = old_date + timedelta(days=5)

        with patch('fades.envbuilder.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = old_date
            mock_datetime.strptime.side_effect = lambda *args, **kw: datetime.strptime(*args, **kw)
            mock_datetime.strftime.side_effect = lambda *args, **kw: datetime.strftime(*args, **kw)

            manager = envbuilder.UsageManager(self.file_path, self.venvscache)
            lines = self.get_usage_lines(manager)
            for u, d in lines:
                self.assertEqual(old_date, d, msg="All records have the same date")

            venv = self.venvscache.get_venv(uuid=self.uuids[0])
            manager.store_usage_stat(venv, self.venvscache)

            mock_datetime.utcnow.return_value = new_date
            manager.store_usage_stat(venv, self.venvscache)

            lines = self.get_usage_lines(manager)
            self.assertEqual(len(self.uuids) + 2, len(lines))

            with patch('fades.envbuilder.destroy_venv') as destroy_venv_mock:
                manager.clean_unused_venvs(4)
                lines = self.get_usage_lines(manager)
                self.assertEqual(1, len(lines), msg="Only one venv remains alive")
                uuid, d = lines[0]

                self.assertEqual(self.uuids[0], uuid,
                                 msg="The env who survive is the last used one.")

                # destroy_env and cache.remove was called for the others
                for uuid in self.uuids[1:]:
                    env_path = self.venvscache.get_venv(uuid=uuid)['env_path']
                    destroy_venv_mock.assert_any_call(env_path, self.venvscache)
