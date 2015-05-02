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

import unittest

from unittest.mock import patch

import logassert

from pkg_resources import parse_requirements

from fades import REPO_PYPI, envbuilder


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

    def setUp(self):
        logassert.setup(self, 'fades.envbuilder')

    def test_create_simple(self):
        requested = {
            REPO_PYPI: [get_req('dep1 == v1'), get_req('dep2 == v2')]
        }
        with patch.object(envbuilder.FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = fake_manager = self.FakeManager()
                fake_manager.really_installed = {'dep1': 'v1', 'dep2': 'v2'}
                venv_data, installed = envbuilder.create_venv(requested)

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
        with patch.object(envbuilder.FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = self.FakeManager()
                envbuilder.create_venv(requested)

        self.assertLoggedWarning("Install from 'unknown' not implemented")

    def test_different_versions(self):
        requested = {
            REPO_PYPI: [get_req('dep1 == v1'), get_req('dep2 == v2')]
        }
        with patch.object(envbuilder.FadesEnvBuilder, 'create_env') as mock_create:
            with patch.object(envbuilder, 'PipManager') as mock_mgr_c:
                mock_create.return_value = ('env_path', 'env_bin_path', 'pip_installed')
                mock_mgr_c.return_value = fake_manager = self.FakeManager()
                fake_manager.really_installed = {'dep1': 'vX', 'dep2': 'v2'}
                _, installed = envbuilder.create_venv(requested)

        self.assertEqual(installed, {
            REPO_PYPI: {
                'dep1': 'vX',
                'dep2': 'v2',
            }
        })
