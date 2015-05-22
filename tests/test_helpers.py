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

import unittest
import sys

from fades.helpers import get_interpreter_version


class GetInterpreterVersionTestCase(unittest.TestCase):
    """Some tests for get_interpreter_version."""

    def setUp(self):
        major, minor, micro = sys.version_info[:3]
        self.current_with_major = 'python{}'.format(major)
        self.current_with_minor = 'python{}.{}'.format(major, minor)
        self.current_with_micro = 'python{}.{}.{}'.format(major, minor, micro)

    def test_none_requested(self):
        interpreter, is_current = get_interpreter_version(None)
        self.assertEqual(interpreter, self.current_with_major)
        self.assertEqual(is_current, True)

    def test_no_number_requested(self):
        interpreter, is_current = get_interpreter_version('python')
        self.assertEqual(interpreter, self.current_with_major)
        self.assertEqual(is_current, True)

    def test_no_number_with_path(self):
        interpreter, is_current = get_interpreter_version('/usr/bin/python')
        self.assertEqual(interpreter, self.current_with_major)
        self.assertEqual(is_current, True)

    def test_with_major(self):
        interpreter, is_current = get_interpreter_version(self.current_with_major)
        self.assertEqual(interpreter, self.current_with_major)
        self.assertEqual(is_current, True)

    def test_other_with_major(self):
        interpreter, is_current = get_interpreter_version('python2')
        self.assertEqual(interpreter, 'python2')
        self.assertEqual(is_current, False)

    def test_with_minor(self):
        interpreter, is_current = get_interpreter_version(self.current_with_minor)
        self.assertEqual(interpreter, self.current_with_minor)
        self.assertEqual(is_current, True)

    def test_other_with_minor(self):
        interpreter, is_current = get_interpreter_version('python2.8')
        self.assertEqual(interpreter, 'python2.8')
        self.assertEqual(is_current, False)

    def test_with_micro(self):
        interpreter, is_current = get_interpreter_version(self.current_with_micro)
        self.assertEqual(interpreter, self.current_with_micro)
        self.assertEqual(is_current, True)

    def test_other_with_micro(self):
        interpreter, is_current = get_interpreter_version('python3.1.1')
        self.assertEqual(interpreter, 'python3.1.1')
        self.assertEqual(is_current, False)

    def test_with_path(self):
        interpreter, is_current = get_interpreter_version(
            '/usr/bin/{}'.format(self.current_with_major))
        self.assertEqual(interpreter, self.current_with_major)
        self.assertEqual(is_current, True)

    def test_other_with_path(self):
        interpreter, is_current = get_interpreter_version('/usr/bin/python2')
        self.assertEqual(interpreter, 'python2')
        self.assertEqual(is_current, False)

    def test_with_path_and_major(self):
        interpreter, is_current = get_interpreter_version(
            '/usr/bin/{}'.format(self.current_with_major))
        self.assertEqual(interpreter, self.current_with_major)
        self.assertEqual(is_current, True)

    def test_other_with_path_and_major(self):
        interpreter, is_current = get_interpreter_version('/usr/bin/python1')
        self.assertEqual(interpreter, 'python1')
        self.assertEqual(is_current, False)

    def test_with_path_and_minor(self):
        interpreter, is_current = get_interpreter_version(
            '/usr/bin/{}'.format(self.current_with_minor))
        self.assertEqual(interpreter, self.current_with_minor)
        self.assertEqual(is_current, True)

    def test_other_with_path_and_minor(self):
        interpreter, is_current = get_interpreter_version('/usr/bin/python2.9')
        self.assertEqual(interpreter, 'python2.9')
        self.assertEqual(is_current, False)

    def test_with_path_and_micro(self):
        interpreter, is_current = get_interpreter_version(
            '/usr/bin/{}'.format(self.current_with_micro))
        self.assertEqual(interpreter, self.current_with_micro)
        self.assertEqual(is_current, True)

    def test_other_with_path_and_micro(self):
        interpreter, is_current = get_interpreter_version('/usr/bin/python3.1.0')
        self.assertEqual(interpreter, 'python3.1.0')
        self.assertEqual(is_current, False)
