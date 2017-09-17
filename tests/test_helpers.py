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

"""Tests for functions in helpers."""

import io
import os
import sys
import tempfile
import unittest

from unittest.mock import patch
from urllib.error import HTTPError

import logassert

from xdg import BaseDirectory

from fades import HTTP_STATUS_NOT_FOUND, HTTP_STATUS_OK, helpers
from fades import parsing


PATH_TO_EXAMPLES = "tests/examples/"


class GetInterpreterVersionTestCase(unittest.TestCase):
    """Some tests for get_interpreter_version."""

    def test_current_version(self):
        values = {None: ('/path/to/python1.0'), "/path/to/python": ('/path/to/python1.0')}

        def side_effect(arg=None):
            return values[arg]

        with patch.object(helpers, '_get_interpreter_info') as mock:
            mock.side_effect = side_effect
            interpreter, is_current = helpers.get_interpreter_version('/path/to/python')
        self.assertEqual(is_current, True)

    def test_other_version(self):
        values = {None: ('/path/to/python1.0'), "/path/to/python": ('/path/to/python9.8')}

        def side_effect(arg=None):
            return values[arg]

        with patch.object(helpers, '_get_interpreter_info') as mock:
            mock.side_effect = side_effect
            interpreter, is_current = helpers.get_interpreter_version('/path/to/python')
        self.assertEqual(is_current, False)

    def test_none_requested(self):
        values = {None: ('/path/to/python1.0'), "/path/to/python": ('/path/to/python9.8')}

        def side_effect(arg=None):
            return values[arg]

        with patch.object(helpers, '_get_interpreter_info') as mock:
            mock.side_effect = side_effect
            interpreter, is_current = helpers.get_interpreter_version(requested_interpreter=None)
        self.assertEqual(is_current, True)
        self.assertTrue(mock.call_count, 1)


class GetInterpreterInfoTestCase(unittest.TestCase):
    """Some tests for _get_interpreter_info."""

    def setUp(self):
        logassert.setup(self, 'fades.helpers')

    def test_none_requested(self):
        with patch.object(sys, 'version_info', (9, 8)), patch.object(sys,
                                                                     'executable',
                                                                     '/path/to/python'):
            interpreter = helpers._get_interpreter_info(None)
        self.assertEqual(interpreter, '/path/to/python9.8')

    def test_requested_fullpath_nodigit(self):
        response = [('{"serial": 0,"path": "/path/to/python","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter = helpers._get_interpreter_info('/path/to/python')
        self.assertEqual(interpreter, '/path/to/python9.8')

    def test_requested_fullpath_with_major(self):
        response = [('{"serial": 0,"path": "/path/to/python9","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter = helpers._get_interpreter_info('/path/to/python9')
        self.assertEqual(interpreter, '/path/to/python9.8')

    def test_requested_fullpath_with_minor(self):
        response = [('{"serial": 0,"path": "/path/to/python9.8","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter = helpers._get_interpreter_info('/path/to/python9.8')
        self.assertEqual(interpreter, '/path/to/python9.8')

    def test_requested_nodigit(self):
        response = [('{"serial": 0,"path": "/path/to/python","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter = helpers._get_interpreter_info('python')
        self.assertEqual(interpreter, '/path/to/python9.8')

    def test_requested_with_major(self):
        response = [('{"serial": 0,"path": "/path/to/python9","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter = helpers._get_interpreter_info('python9')
        self.assertEqual(interpreter, '/path/to/python9.8')

    def test_requested_with_minor(self):
        response = [('{"serial": 0,"path": "/path/to/python9.8","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter = helpers._get_interpreter_info('python9.8')
        self.assertEqual(interpreter, '/path/to/python9.8')

    def test_requested_not_exists(self):
        side_effect = IOError("[Errno 2] No such file or directory: 'pythonME'")
        with patch.object(helpers, 'logged_exec',
                          side_effect=side_effect), self.assertRaises(SystemExit):
            helpers._get_interpreter_info('pythonME')
        self.assertLoggedError("Error getting requested interpreter version:"
                               " [Errno 2] No such file or directory: 'pythonME'")


class GetLatestVersionNumberTestCase(unittest.TestCase):
    """Some tests for get_latest_version_number."""

    def setUp(self):
        logassert.setup(self, 'fades.helpers')

    def test_get_version_correct(self):
        with open(os.path.join(PATH_TO_EXAMPLES, 'pypi_get_version_ok.json'), "rb") as fh:
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.return_value = fh
                last_version = helpers.get_latest_version_number("some_package")
        mock_urlopen.assert_called_once_with(helpers.BASE_PYPI_URL.format(name="some_package"))
        self.assertEquals(last_version, '2.8.1')

    def test_get_version_wrong(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.side_effect = HTTPError("url",
                                                                500,
                                                                "mgs",
                                                                {},
                                                                io.BytesIO())
                mock_urlopen.return_value = mock_http_response
                self.assertRaises(Exception, helpers.get_latest_version_number, "some_package")
                self.assertLoggedWarning("Network error.")

    def test_get_version_fail(self):
        with open(os.path.join(PATH_TO_EXAMPLES, 'pypi_get_version_fail.json'), "rb") as fh:
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.return_value = fh
                self.assertRaises(KeyError, helpers.get_latest_version_number, "some_package")
                self.assertLoggedError("Could not get the version of the package. Error:")


class CheckPyPIUpdatesTestCase(unittest.TestCase):
    """Some tests for check_pypi_updates."""

    def setUp(self):
        logassert.setup(self, 'fades.helpers')
        self.deps = parsing.parse_manual(["django==1.7.5", "requests"])
        self.deps_higher = parsing.parse_manual(["django==100.1.1"])
        self.deps_same_than_latest = parsing.parse_manual(["django==1.9"])

    def test_check_pypi_updates_with_and_without_version(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.side_effect = [b'{"info": {"version": "1.9"}}',
                                                       b'{"info": {"version": "2.1"}}']
                mock_urlopen.return_value = mock_http_response
                dependencies = helpers.check_pypi_updates(self.deps)
                dep_django = dependencies['pypi'][0]
                dep_request = dependencies['pypi'][1]
                self.assertLoggedInfo('There is a new version of django: 1.9')
                self.assertEquals(dep_request.specs, [('==', '2.1')])
                self.assertEquals(dep_django.specs, [('==', '1.7.5')])
                self.assertLoggedInfo('There is a new version of requests: 2.1 and will use it.')

    def test_check_pypi_updates_with_a_higher_version_of_a_package(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.side_effect = [b'{"info": {"version": "1.9"}}']
                mock_urlopen.return_value = mock_http_response
                helpers.check_pypi_updates(self.deps_higher)
                self.assertLoggedWarning(
                    "The requested version for django is greater than latest found in PyPI: 1.9")

    def test_check_pypi_updates_with_the_latest_version_of_a_package(self):
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.side_effect = [b'{"info": {"version": "1.9"}}']
                mock_urlopen.return_value = mock_http_response
                helpers.check_pypi_updates(self.deps_same_than_latest)
                self.assertLoggedInfo(
                    "The requested version for django is the latest one in PyPI: 1.9")


class GetDirsTestCase(unittest.TestCase):
    """Utilities to get dir."""

    _home = os.path.expanduser("~")

    def test_basedir_xdg(self):
        direct = helpers.get_basedir()
        self.assertEqual(direct, os.path.join(BaseDirectory.xdg_data_home, 'fades'))

    def _fake_snap_env_dir(self, direct):
        """Fake Snap's environment variable."""
        os.environ[helpers.SNAP_BASEDIR_NAME] = direct
        self.addCleanup(os.environ.pop, helpers.SNAP_BASEDIR_NAME)

    def test_basedir_snap(self):
        with tempfile.TemporaryDirectory() as dirname:
            self._fake_snap_env_dir(dirname)
            direct = helpers.get_basedir()
            self.assertEqual(direct, os.path.join(dirname, 'data'))

    def test_basedir_default(self):
        with patch.object(helpers, "_get_basedirectory") as mock:
            mock.side_effect = ImportError()
            direct = helpers.get_basedir()
            self.assertEqual(direct, os.path.join(self._home, '.fades'))

    def test_basedir_xdg_nonexistant(self):
        with patch("xdg.BaseDirectory") as mock:
            with tempfile.TemporaryDirectory() as dirname:
                mock.xdg_data_home = dirname
                direct = helpers.get_basedir()
                self.assertTrue(os.path.exists(direct))

    def test_basedir_snap_nonexistant(self):
        with tempfile.TemporaryDirectory() as dirname:
            self._fake_snap_env_dir(dirname)
            direct = helpers.get_basedir()
            self.assertTrue(os.path.exists(direct))

    def test_confdir_xdg(self):
        direct = helpers.get_confdir()
        self.assertEqual(direct, os.path.join(BaseDirectory.xdg_config_home, 'fades'))

    def test_confdir_snap(self):
        with tempfile.TemporaryDirectory() as dirname:
            self._fake_snap_env_dir(dirname)
            direct = helpers.get_confdir()
            self.assertEqual(direct, os.path.join(dirname, 'config'))

    def test_confdir_default(self):
        with patch.object(helpers, "_get_basedirectory") as mock:
            mock.side_effect = ImportError()
            direct = helpers.get_confdir()
            self.assertEqual(direct, os.path.join(self._home, '.fades'))

    def test_confdir_xdg_nonexistant(self):
        with patch("xdg.BaseDirectory") as mock:
            with tempfile.TemporaryDirectory() as dirname:
                mock.xdg_config_home = dirname
                direct = helpers.get_confdir()
                self.assertTrue(os.path.exists(direct))

    def test_confdir_snap_nonexistant(self):
        with tempfile.TemporaryDirectory() as dirname:
            self._fake_snap_env_dir(dirname)
            direct = helpers.get_confdir()
            self.assertTrue(os.path.exists(direct))


class CheckPackageExistenceTestCase(unittest.TestCase):
    """Test for check_pypi_exists."""

    def setUp(self):
        logassert.setup(self, 'fades.helpers')

    def test_exists(self):
        deps = parsing.parse_manual(["foo"])

        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.status = HTTP_STATUS_OK
                mock_urlopen.return_value = mock_http_response

                exists = helpers.check_pypi_exists(deps)
        self.assertTrue(exists)
        self.assertLogged("exists in Pypi")

    def test_all_exists(self):
        dependencies = parsing.parse_manual(['foo', 'bar', 'baz'])

        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.status = HTTP_STATUS_OK
                mock_urlopen.side_effect = [mock_http_response] * 3

                exists = helpers.check_pypi_exists(dependencies)
        self.assertTrue(exists)
        self.assertLogged("exists in Pypi")

    def test_doesnt_exists(self):
        dependency = parsing.parse_manual(["foo"])

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_http_error = HTTPError("url", HTTP_STATUS_NOT_FOUND, "mgs", {}, io.BytesIO())
            mock_urlopen.side_effect = mock_http_error

            exists = helpers.check_pypi_exists(dependency)

        self.assertFalse(exists)
        self.assertLoggedInfo("foo doesn't exists in PyPi.")

    def test_one_doesnt_exists(self):
        dependencies = parsing.parse_manual(["foo", "bar"])

        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_error = HTTPError("url", HTTP_STATUS_NOT_FOUND, "mgs", {}, io.BytesIO())
                mock_http_response.status = HTTP_STATUS_OK
                mock_urlopen.side_effect = [mock_http_response, mock_http_error]

                exists = helpers.check_pypi_exists(dependencies)

        self.assertFalse(exists)
        self.assertLoggedInfo("bar doesn't exists in PyPi.")

    def test_error_hitting_pypi(self):
        dependency = parsing.parse_manual(["foo"])

        with patch('sys.exit') as mocked_exit:
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = ValueError("cabum!!")

                helpers.check_pypi_exists(dependency)

        self.assertTrue(mocked_exit.called)
        mocked_exit.assert_called_once_with(1)

    def test_status_code_error(self):
        dependency = parsing.parse_manual(["foo"])

        with patch('sys.exit') as mocked_exit:
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_http_error = HTTPError("url", 400, "mgs", {}, io.BytesIO())
                mock_urlopen.side_effect = mock_http_error

                helpers.check_pypi_exists(dependency)

        self.assertTrue(mocked_exit.called)
        mocked_exit.assert_called_once_with(1)
