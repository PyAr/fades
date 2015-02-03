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

"""Tests for the helpers."""

import unittest

from fades import helpers


class VersionComparingTestCase(unittest.TestCase):
    """Compare versions helper."""

    def test_simple(self):
        self.assertFalse(helpers.is_version_satisfied('2', '1'))
        self.assertTrue(helpers.is_version_satisfied('2', '2'))
        self.assertFalse(helpers.is_version_satisfied('2', '3'))

    def test_with_none(self):
        self.assertFalse(helpers.is_version_satisfied(None, '1'))
        self.assertTrue(helpers.is_version_satisfied(None, None))
        self.assertTrue(helpers.is_version_satisfied('2', None))

    def test_with_equal(self):
        self.assertTrue(helpers.is_version_satisfied('1.3', '==1.3'))
        self.assertTrue(helpers.is_version_satisfied('1.3', '==  1.3'))
        self.assertTrue(helpers.is_version_satisfied('1.3', ' == 1.3'))
        self.assertFalse(helpers.is_version_satisfied('1.3', '==1.2'))
        self.assertFalse(helpers.is_version_satisfied('1.3', '==2.0'))

    def test_with_greaterequal(self):
        self.assertTrue(helpers.is_version_satisfied('1.3', '>=1.3'))
        self.assertTrue(helpers.is_version_satisfied('1.3', '>= 1.2'))
        self.assertFalse(helpers.is_version_satisfied('1.3', '>=2.0'))

    def test_with_greater(self):
        self.assertFalse(helpers.is_version_satisfied('1.3', '>1.3'))
        self.assertTrue(helpers.is_version_satisfied('1.3', '> 1.2'))
        self.assertFalse(helpers.is_version_satisfied('1.3', '> 2.0'))
