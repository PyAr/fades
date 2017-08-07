# Copyright 2015-2017 Facundo Batista, Nicolás Demarchi
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

"""Tests for pip related code."""

import os
import io
import unittest

from unittest.mock import patch

import logassert

from fades.pipmanager import PipManager
from fades import pipmanager
from fades import helpers
from tests import get_tempfile

BIN_PATH = "somepath"


class PipManagerTestCase(unittest.TestCase):
    """Check parsing for `pip show`."""

    def setUp(self):
        logassert.setup(self, 'fades.pipmanager')

    def test_get_parsing_ok(self):
        mocked_stdout = ['Name: foo',
                         'Version: 2.0.0',
                         'Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages',
                         'Requires: ']
        mgr = PipManager(BIN_PATH, pip_installed=True)
        with patch.object(helpers, 'logged_exec') as mock:
            mock.return_value = mocked_stdout
            version = mgr.get_version('foo')
        self.assertEqual(version, '2.0.0')

    def test_get_parsing_error(self):
        mocked_stdout = ['Name: foo',
                         'Release: 2.0.0',
                         'Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages',
                         'Requires: ']
        mgr = PipManager(BIN_PATH, pip_installed=True)
        with patch.object(helpers, 'logged_exec') as mock:
            version = mgr.get_version('foo')
            mock.return_value = mocked_stdout
        self.assertEqual(version, '')
        self.assertLoggedError('Fades is having problems getting the installed version. '
                               'Run with -v or check the logs for details')

    def test_real_case_levenshtein(self):
        mocked_stdout = [
            'Metadata-Version: 1.1',
            'Name: python-Levenshtein',
            'Version: 0.12.0',
            'License: GPL',
        ]
        mgr = PipManager(BIN_PATH, pip_installed=True)
        with patch.object(helpers, 'logged_exec') as mock:
            mock.return_value = mocked_stdout
            version = mgr.get_version('foo')
        self.assertEqual(version, '0.12.0')

    def test_install(self):
        mgr = PipManager(BIN_PATH, pip_installed=True)
        pip_path = os.path.join(BIN_PATH, 'pip')
        with patch.object(helpers, 'logged_exec') as mock:
            mgr.install('foo')
            mock.assert_called_with([pip_path, 'install', 'foo'])

    def test_install_multiword_dependency(self):
        mgr = PipManager(BIN_PATH, pip_installed=True)
        pip_path = os.path.join(BIN_PATH, 'pip')
        with patch.object(helpers, 'logged_exec') as mock:
            mgr.install('foo bar')
            mock.assert_called_with([pip_path, 'install', 'foo', 'bar'])

    def test_install_with_options(self):
        mgr = PipManager(BIN_PATH, pip_installed=True, options=['--bar baz'])
        pip_path = os.path.join(BIN_PATH, 'pip')
        with patch.object(helpers, 'logged_exec') as mock:
            mgr.install('foo')
            mock.assert_called_with([pip_path, 'install', 'foo', '--bar', 'baz'])

    def test_install_with_options_using_equal(self):
        mgr = PipManager(BIN_PATH, pip_installed=True, options=['--bar=baz'])
        pip_path = os.path.join(BIN_PATH, 'pip')
        with patch.object(helpers, 'logged_exec') as mock:
            mgr.install('foo')
            mock.assert_called_with([pip_path, 'install', 'foo', '--bar=baz'])

    def test_install_raise_error(self):
        mgr = PipManager(BIN_PATH, pip_installed=True)
        with patch.object(helpers, 'logged_exec') as mock:
            mock.side_effect = Exception("Kapow!")
            with self.assertRaises(Exception):
                mgr.install('foo')
        self.assertLoggedError("Error installing foo: Kapow!")

    def test_install_without_pip(self):
        mgr = PipManager(BIN_PATH, pip_installed=False)
        pip_path = os.path.join(BIN_PATH, 'pip')
        with patch.object(helpers, 'logged_exec') as mocked_exec:
            with patch.object(mgr, '_brute_force_install_pip') as mocked_install_pip:
                mgr.install('foo')
                self.assertEqual(mocked_install_pip.call_count, 1)
            mocked_exec.assert_called_with([pip_path, 'install', 'foo'])

    def test_say_hi_on_first_install(self):
        mgr = PipManager(BIN_PATH, pip_installed=True, options=['--bar=baz'])
        with patch.object(helpers, 'logged_exec'):
            mgr.install('foo')
            self.assertLoggedInfo("Hi! This is fades")
            logassert.setup(self, 'fades.pipmanager')
            mgr.install('bar')
            self.assertNotLoggedInfo("Hi! This is fades")

    def test_brute_force_install_pip_installer_exists(self):
        mgr = PipManager(BIN_PATH, pip_installed=False)
        python_path = os.path.join(BIN_PATH, 'python')
        with patch.object(helpers, 'logged_exec') as mocked_exec, \
                patch.object(mgr, '_download_pip_installer') as download_installer:

            # get the tempfile but leave it there to be found
            mgr.pip_installer_fname = get_tempfile(self)
            mgr._brute_force_install_pip()

            self.assertEqual(download_installer.call_count, 0)
            mocked_exec.assert_called_with([python_path, mgr.pip_installer_fname, '-I'])
        self.assertTrue(mgr.pip_installed)

    def test_brute_force_install_pip_no_installer(self):
        mgr = PipManager(BIN_PATH, pip_installed=False)
        python_path = os.path.join(BIN_PATH, 'python')
        with patch.object(helpers, 'logged_exec') as mocked_exec, \
                patch.object(mgr, '_download_pip_installer') as download_installer:

            # get the tempfile and remove it so then it's not found
            tempfile = get_tempfile(self)
            os.remove(tempfile)

            mgr.pip_installer_fname = tempfile
            mgr._brute_force_install_pip()

            download_installer.assert_called_once_with()
        mocked_exec.assert_called_with([python_path, mgr.pip_installer_fname, '-I'])
        self.assertTrue(mgr.pip_installed)

    def test_download_pip_installer(self):
        mgr = PipManager(BIN_PATH, pip_installed=False)

        # get a tempfile and remove it, so later the installer is downloaded there
        tempfile = get_tempfile(self)
        os.remove(tempfile)

        mgr.pip_installer_fname = tempfile
        with patch('fades.pipmanager.request.urlopen') as urlopen:
            urlopen.return_value = io.BytesIO(b'hola')
            mgr._download_pip_installer()
        self.assertTrue(os.path.exists(mgr.pip_installer_fname))
        urlopen.assert_called_once_with(pipmanager.PIP_INSTALLER)
