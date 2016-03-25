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
import unittest
from unittest.mock import patch

from pkg_resources import parse_requirements

import logassert

from fades import REPO_PYPI, envbuilder
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
        with patch.object(envbuilder.FadesEnvBuilder, 'create_env') as mock_create:
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
        with patch.object(envbuilder.FadesEnvBuilder, 'create_env') as mock_create:
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

        with patch.object(envbuilder.FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = self.FailInstallManager()
                with self.assertRaises(SystemExit):
                    envbuilder.create_venv(
                        requested,
                        interpreter,
                        is_current,
                        options,
                        pip_options)

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
        with patch.object(envbuilder.FadesEnvBuilder, 'create_env') as mock_create:
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
        env_builder = envbuilder.FadesEnvBuilder()
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
        env_builder = envbuilder.FadesEnvBuilder()
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
        env_builder = envbuilder.FadesEnvBuilder()
        interpreter = 'pythonX.Y'
        is_current = False
        options = {"virtualenv_options": ['--system-site-packages'],
                   "pyvenv_options": [],
                   }
        with patch.object(envbuilder.FadesEnvBuilder, 'create_with_virtualenv') as mock_create:
                env_builder.create_env(interpreter, is_current, options)
                mock_create.assert_called_with(interpreter, options['virtualenv_options'])

    def test_create_virtualenv(self):
        env_builder = envbuilder.FadesEnvBuilder()
        interpreter = 'pythonX.Y'
        is_current = False
        options = {"virtualenv_options": [],
                   "pyvenv_options": [],
                   }
        with patch.object(envbuilder.FadesEnvBuilder, 'create_with_virtualenv') as mock_create:
                env_builder.create_env(interpreter, is_current, options)
                mock_create.assert_called_with(interpreter, options['virtualenv_options'])

    def test_custom_env_path(self):
        builder = envbuilder.FadesEnvBuilder('some-path')
        self.assertEqual(builder.env_path, 'some-path')


class EnvDestructionTestCase(unittest.TestCase):

    def test_destroy_env(self):
        builder = envbuilder.FadesEnvBuilder()
        # make sure the virtualenv exists on disk
        options = {"virtualenv_options": [],
                   "pyvenv_options": ['--system-site-packages'],
                   "pip-options": [],
                   }
        builder.create_env('python', False, options=options)
        assert os.path.exists(builder.env_path)

        builder.destroy_env()
        self.assertFalse(os.path.exists(builder.env_path))

    def test_destroy_venv(self):
        builder = envbuilder.FadesEnvBuilder()
        # make sure the virtualenv exists on disk
        options = {"virtualenv_options": [],
                   "pyvenv_options": ['--system-site-packages'],
                   "pip-options": [],
                   }
        builder.create_env('python', False, options=options)
        assert os.path.exists(builder.env_path)

        envbuilder.destroy_venv(builder.env_path)
        self.assertFalse(os.path.exists(builder.env_path))

    def test_destroy_venv_if_env_path_not_found(self):
        builder = envbuilder.FadesEnvBuilder()
        assert not os.path.exists(builder.env_path)

        envbuilder.destroy_venv(builder.env_path)
        self.assertFalse(os.path.exists(builder.env_path))
