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
