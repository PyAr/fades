# Copyright 2014-2015 Facundo Batista, Nicolás Demarchi
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

"""Tests for the main module."""

import unittest

from unittest.mock import Mock

from fades import main


class ArgvParsingTestCase(unittest.TestCase):
    """Check the parsing of sys argv."""

    def test_empty(self):
        fo, cp, co = main._parse_argv(["fades"])
        self.assertEqual(fo, [])
        self.assertEqual(cp, "")
        self.assertEqual(co, [])

    def test_simple_child(self):
        fo, cp, co = main._parse_argv(["fades", "foo.py"])
        self.assertEqual(fo, [])
        self.assertEqual(cp, "foo.py")
        self.assertEqual(co, [])

    def test_child_with_parameters(self):
        fo, cp, co = main._parse_argv(["fades", "foo.py", "-p", "--rock"])
        self.assertEqual(fo, [])
        self.assertEqual(cp, "foo.py")
        self.assertEqual(co, ["-p", "--rock"])

    def test_fadesparam_simple(self):
        fo, cp, co = main._parse_argv(["fades", "--cronos"])
        self.assertEqual(fo, ["--cronos"])
        self.assertEqual(cp, "")
        self.assertEqual(co, [])

    def test_fadesparam_double_separated(self):
        fo, cp, co = main._parse_argv(["fades", "-foo", "-bar"])
        self.assertEqual(fo, ["-foo", "-bar"])
        self.assertEqual(cp, "")
        self.assertEqual(co, [])

    def test_fadesparam_double_together(self):
        fo, cp, co = main._parse_argv(["fades", "--foo -n"])
        self.assertEqual(fo, ["--foo", "-n"])
        self.assertEqual(cp, "")
        self.assertEqual(co, [])

    def test_big_complex_case(self):
        fo, cp, co = main._parse_argv(["fades", "-v", "bar.py", "-k", "--p=3"])
        self.assertEqual(fo, ["-v"])
        self.assertEqual(cp, "bar.py")
        self.assertEqual(co, ["-k", "--p=3"])


class ManagingDepsTestCase(unittest.TestCase):
    """Check all the dependency management."""

    def test_new_dependency(self):
        mgr_mock = Mock()
        mgr_mock.get_version.return_value = '9'
        requested_dep = {
            'testdep': {'version': '7'},
        }
        previous_dep = {}
        main._manage_dependencies(mgr_mock, requested_dep, previous_dep)
        self.assertEqual(requested_dep, {
            'testdep': {'version': '9'},
        })
        mgr_mock.install.assert_called_with('testdep', '7')
        mgr_mock.get_version.assert_called_with('testdep')

    def test_dependency_different_version(self):
        mgr_mock = Mock()
        mgr_mock.get_version.return_value = '9'
        requested_dep = {
            'testdep': {'version': '9'},
        }
        previous_dep = {
            'testdep': {'version': '7'},
        }
        main._manage_dependencies(mgr_mock, requested_dep, previous_dep)
        self.assertEqual(requested_dep, {
            'testdep': {'version': '9'},
        })
        mgr_mock.update.assert_called_with('testdep', '9')
        mgr_mock.get_version.assert_called_with('testdep')

    def test_dependency_removed(self):
        mgr_mock = Mock()
        requested_dep = {}
        previous_dep = {
            'testdep': {'version': '7'},
        }
        main._manage_dependencies(mgr_mock, requested_dep, previous_dep)
        self.assertEqual(requested_dep, {})
        mgr_mock.remove.assert_called_with('testdep')
        self.assertEqual(mgr_mock.get_version.call_count, 0)
