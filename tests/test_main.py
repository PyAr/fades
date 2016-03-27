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

"""Tests for some code in main."""

import unittest

from fades import main, __version__, VERSION


class DepsMergingTestCase(unittest.TestCase):
    """Some tests for the dependency merger."""

    def test_two_different(self):
        d1 = dict(foo=[1, 2])
        d2 = dict(bar=[3, 4])
        d = main._merge_deps(d1, d2)
        self.assertDictEqual(d, {
            'foo': [1, 2],
            'bar': [3, 4],
        })

    def test_two_same_repo(self):
        d1 = dict(foo=[1, 2])
        d2 = dict(foo=[3, 4])
        d = main._merge_deps(d1, d2)
        self.assertDictEqual(d, {
            'foo': [1, 2, 3, 4],
        })

    def test_complex_case(self):
        d1 = dict(foo=[1, 2])
        d2 = dict(foo=[3], bar=[5])
        d3 = dict(bar=[4, 6])
        d = main._merge_deps(d1, d2, d3)
        self.assertDictEqual(d, {
            'foo': [1, 2, 3],
            'bar': [5, 4, 6],
        })

    def test_version_show(self):
        self.assertEqual(
            __version__,
            '.'.join([str(v) for v in VERSION]),
        )
