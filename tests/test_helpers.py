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

import sys
import unittest
from unittest.mock import patch

import logassert

from fades import helpers


class GetInterpreterVersionTestCase(unittest.TestCase):
    """Some tests for get_interpreter_version."""

    def test_current_version(self):
        values = {None: ('/path/to/python1', '1.0'),
                  "/path/to/python": ('/path/to/python1', '1.0')}

        def side_effect(arg=None):
            return values[arg]

        with patch.object(helpers, '_get_interpreter_info') as mock:
            mock.side_effect = side_effect
            interpreter, interpreter_version, is_current = helpers.get_interpreter_version(
                '/path/to/python')
        self.assertEqual(is_current, True)

    def test_other_version(self):
        values = {None: ('/path/to/python1', '1.0'),
                  "/path/to/python": ('/path/to/python9', '9.8')}

        def side_effect(arg=None):
            return values[arg]

        with patch.object(helpers, '_get_interpreter_info') as mock:
            mock.side_effect = side_effect
            interpreter, interpreter_version, is_current = helpers.get_interpreter_version(
                '/path/to/python')
        self.assertEqual(is_current, False)


class GetInterpreterInfoTestCase(unittest.TestCase):
    """Some tests for _get_interpreter_info."""

    def setUp(self):
        logassert.setup(self, 'fades.helpers')

    def test_none_requested(self):
        with patch.object(sys, 'version_info', (9, 8)), patch.object(sys,
                                                                     'executable',
                                                                     '/path/to/python'):
            interpreter, interpreter_version = helpers._get_interpreter_info(None)
        self.assertEqual(interpreter, '/path/to/python9.8')
        self.assertEqual(interpreter_version, '9.8')

    def test_requested_fullpath_nodigit(self):
        response = [('{"serial": 0,"path": "/path/to/python","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter, interpreter_version = helpers._get_interpreter_info('/path/to/python')
        self.assertEqual(interpreter, '/path/to/python9.8')
        self.assertEqual(interpreter_version, '9.8')

    def test_requested_fullpath_with_major(self):
        response = [('{"serial": 0,"path": "/path/to/python9","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter, interpreter_version = helpers._get_interpreter_info('/path/to/python9')
        self.assertEqual(interpreter, '/path/to/python9.8')
        self.assertEqual(interpreter_version, '9.8')

    def test_requested_fullpath_with_minor(self):
        response = [('{"serial": 0,"path": "/path/to/python9.8","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter, interpreter_version = helpers._get_interpreter_info('/path/to/python9.8')
        self.assertEqual(interpreter, '/path/to/python9.8')
        self.assertEqual(interpreter_version, '9.8')

    def test_requested_nodigit(self):
        response = [('{"serial": 0,"path": "/path/to/python","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter, interpreter_version = helpers._get_interpreter_info('python')
        self.assertEqual(interpreter, '/path/to/python9.8')
        self.assertEqual(interpreter_version, '9.8')

    def test_requested_with_major(self):
        response = [('{"serial": 0,"path": "/path/to/python9","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter, interpreter_version = helpers._get_interpreter_info('python9')
        self.assertEqual(interpreter, '/path/to/python9.8')
        self.assertEqual(interpreter_version, '9.8')

    def test_requested_with_minor(self):
        response = [('{"serial": 0,"path": "/path/to/python9.8","minor": 8,"major": 9,"micro": 0,'
                    '"releaselevel": "ultimate"}')]
        with patch.object(helpers, 'logged_exec', return_value=response):
            interpreter, interpreter_version = helpers._get_interpreter_info('python9.8')
        self.assertEqual(interpreter, '/path/to/python9.8')
        self.assertEqual(interpreter_version, '9.8')

    def test_requested_not_exists(self):
        side_effect = IOError("[Errno 2] No such file or directory: 'pythonME'")
        with patch.object(helpers, 'logged_exec',
                          side_effect=side_effect), self.assertRaises(SystemExit):
            interpreter, interpreter_version = helpers._get_interpreter_info('pythonME')
        self.assertLoggedError("Error getting requested interpreter version:"
                               " [Errno 2] No such file or directory: 'pythonME'")
