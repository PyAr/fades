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
import json
import os
import sys
import tempfile
import unittest

from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

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

        with patch('fades.helpers.logged_exec') as mock_lexec:
            mock_lexec.side_effect = side_effect

            with self.assertRaises(Exception):
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
        self.assertEqual(last_version, '2.8.1')

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
                self.assertEqual(dep_request.specs, [('==', '2.1')])
                self.assertEqual(dep_django.specs, [('==', '1.7.5')])
                self.assertLoggedInfo("The latest version of 'requests' is 2.1 and will use it.")

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
        self.assertLogged("exists in PyPI")

    def test_all_exists(self):
        dependencies = parsing.parse_manual(['foo', 'bar', 'baz'])

        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.status = HTTP_STATUS_OK
                mock_urlopen.side_effect = [mock_http_response] * 3

                exists = helpers.check_pypi_exists(dependencies)
        self.assertTrue(exists)
        self.assertLogged("exists in PyPI")

    def test_doesnt_exists(self):
        dependency = parsing.parse_manual(["foo"])

        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_http_error = HTTPError("url", HTTP_STATUS_NOT_FOUND, "mgs", {}, io.BytesIO())
            mock_urlopen.side_effect = mock_http_error

            exists = helpers.check_pypi_exists(dependency)

        self.assertFalse(exists)
        self.assertLoggedError("foo doesn't exists in PyPI.")

    def test_one_doesnt_exists(self):
        dependencies = parsing.parse_manual(["foo", "bar"])

        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_error = HTTPError("url", HTTP_STATUS_NOT_FOUND, "mgs", {}, io.BytesIO())
                mock_http_response.status = HTTP_STATUS_OK
                mock_urlopen.side_effect = [mock_http_response, mock_http_error]

                exists = helpers.check_pypi_exists(dependencies)

        self.assertFalse(exists)
        self.assertLoggedError("bar doesn't exists in PyPI.")

    def test_error_hitting_pypi(self):
        dependency = parsing.parse_manual(["foo"])

        with self.assertRaises(Exception):
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_urlopen.side_effect = ValueError("cabum!!")

                helpers.check_pypi_exists(dependency)

    def test_status_code_error(self):
        dependency = parsing.parse_manual(["foo"])

        with self.assertRaises(Exception):
            with patch('urllib.request.urlopen') as mock_urlopen:
                mock_http_error = HTTPError("url", 400, "mgs", {}, io.BytesIO())
                mock_urlopen.side_effect = mock_http_error

                helpers.check_pypi_exists(dependency)

    def test_redirect_response(self):
        deps = parsing.parse_manual(["foo"])

        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.status = 302  # redirect
                mock_urlopen.return_value = mock_http_response

                exists = helpers.check_pypi_exists(deps)
        self.assertTrue(exists)
        self.assertLoggedWarning("Got a (unexpected) HTTP_STATUS")


class ScriptDownloaderTestCase(unittest.TestCase):
    """Check the script downloader."""

    def setUp(self):
        logassert.setup(self, 'fades.helpers')

    def test_external_public_function(self):
        test_url = "http://scripts.com/foobar.py"
        test_content = "test content of the remote script ññ"
        with patch('fades.helpers._ScriptDownloader') as mock_downloader_class:
            mock_downloader = mock_downloader_class()
            mock_downloader.get.return_value = test_content
            mock_downloader.name = 'mock downloader'
            filepath = helpers.download_remote_script(test_url)

        # plan to remove the downloaded content (so test remains clean)
        self.addCleanup(os.unlink, filepath)

        # checks
        mock_downloader_class.assert_called_with(test_url)
        self.assertLoggedInfo(
            "Downloading remote script from {!r}".format(test_url),
            repr(filepath), "(using 'mock downloader' downloader)")
        with open(filepath, "rt", encoding='utf8') as fh:
            self.assertEqual(fh.read(), test_content)

    def test_decide_linkode(self):
        url = "http://linkode.org/#02c5nESQBLEjgBRhUwJK74"
        downloader = helpers._ScriptDownloader(url)
        name = downloader._decide()
        self.assertEqual(name, 'linkode')

    def test_decide_pastebin(self):
        url = "https://pastebin.com/sZGwz7SL"
        downloader = helpers._ScriptDownloader(url)
        name = downloader._decide()
        self.assertEqual(name, 'pastebin')

    def test_decide_gist(self):
        url = "https://gist.github.com/facundobatista/6ff4f75760a9acc35e68bae8c1d7da1c"
        downloader = helpers._ScriptDownloader(url)
        name = downloader._decide()
        self.assertEqual(name, 'gist')

    def test_downloader_raw(self):
        test_url = "http://scripts.com/foobar.py"
        raw_service_response = b"test content of the remote script"
        downloader = helpers._ScriptDownloader(test_url)
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.return_value = raw_service_response
                mock_urlopen.return_value = mock_http_response
                mock_http_response.geturl.return_value = test_url

            content = downloader.get()

        # check urlopen was called with the proper url, and passing correct headers
        headers = {
            'Accept': 'text/plain',
            'User-agent': helpers._ScriptDownloader.USER_AGENT,
        }
        (call,) = mock_urlopen.mock_calls
        (called_request,) = call[1]
        self.assertIsInstance(called_request, Request)
        self.assertEqual(called_request.full_url, test_url)
        self.assertEqual(called_request.headers, headers)
        self.assertEqual(content, raw_service_response.decode("utf8"))

    def test_downloader_linkode(self):
        test_url = "http://linkode.org/#02c5nESQBLEjgBRhUwJK74"
        test_content = "test content of the remote script áéíóú"
        raw_service_response = json.dumps({
            'content': test_content,
            'morestuff': 'whocares',
        }).encode("utf8")

        downloader = helpers._ScriptDownloader(test_url)
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.return_value = raw_service_response
                mock_urlopen.return_value = mock_http_response

            content = downloader.get()

        # check urlopen was called with the proper url, and passing correct headers
        headers = {
            'Accept': 'application/json',
            'User-agent': helpers._ScriptDownloader.USER_AGENT,
        }
        (call,) = mock_urlopen.mock_calls
        (called_request,) = call[1]
        self.assertIsInstance(called_request, Request)
        self.assertEqual(
            called_request.full_url, "https://linkode.org/api/1/linkodes/02c5nESQBLEjgBRhUwJK74")
        self.assertEqual(called_request.headers, headers)
        self.assertEqual(content, test_content)

    def test_downloader_pastebin(self):
        test_url = "http://pastebin.com/sZGwz7SL"
        real_url = "https://pastebin.com/raw/sZGwz7SL"
        test_content = "test content of the remote script áéíóú"
        raw_service_response = test_content.encode("utf8")

        downloader = helpers._ScriptDownloader(test_url)
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.return_value = raw_service_response
                mock_urlopen.return_value = mock_http_response
                mock_http_response.geturl.return_value = real_url

            content = downloader.get()

        # check urlopen was called with the proper url, and passing correct headers
        headers = {
            'Accept': 'text/plain',
            'User-agent': helpers._ScriptDownloader.USER_AGENT,
        }
        (call,) = mock_urlopen.mock_calls
        (called_request,) = call[1]
        self.assertIsInstance(called_request, Request)
        self.assertEqual(called_request.full_url, real_url)
        self.assertEqual(called_request.headers, headers)
        self.assertEqual(content, test_content)

    def test_downloader_gist(self):
        test_url = "http://gist.github.com/facundobatista/6ff4f75760a9acc35e68bae8c1d7da1c"
        real_url = "https://gist.github.com/facundobatista/6ff4f75760a9acc35e68bae8c1d7da1c/raw"
        test_content = "test content of the remote script áéíóú"
        raw_service_response = test_content.encode("utf8")

        downloader = helpers._ScriptDownloader(test_url)
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.return_value = raw_service_response
                mock_urlopen.return_value = mock_http_response
                mock_http_response.geturl.return_value = real_url

            content = downloader.get()

        # check urlopen was called with the proper url, and passing correct headers
        headers = {
            'Accept': 'text/plain',
            'User-agent': helpers._ScriptDownloader.USER_AGENT,
        }
        (call,) = mock_urlopen.mock_calls
        (called_request,) = call[1]
        self.assertIsInstance(called_request, Request)
        self.assertEqual(called_request.full_url, real_url)
        self.assertEqual(called_request.headers, headers)
        self.assertEqual(content, test_content)

    def test_downloader_raw_with_redirection(self):
        test_url = "http://bit.ly/will-redirect"
        final_url = "http://real-service.com/"
        raw_service_response = b"test content of the remote script"
        downloader = helpers._ScriptDownloader(test_url)
        response_contents = [
            b"whatever; we don't care as we are redirectect",
            raw_service_response,
        ]
        with patch('urllib.request.urlopen') as mock_urlopen:
            with patch('http.client.HTTPResponse') as mock_http_response:
                mock_http_response.read.side_effect = lambda: response_contents.pop()
                mock_http_response.geturl.return_value = final_url
                mock_urlopen.return_value = mock_http_response

                content = downloader.get()

        # two calls, first to the service that will redirect us, second to the final one
        call1, call2 = mock_urlopen.mock_calls

        (called_request,) = call1[1]
        self.assertEqual(called_request.full_url, test_url)

        (called_request,) = call2[1]
        self.assertEqual(called_request.full_url, final_url)
        self.assertEqual(content, raw_service_response.decode("utf8"))

        self.assertLoggedInfo("Download redirect detect, now downloading from", final_url)
