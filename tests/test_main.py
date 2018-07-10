# Copyright 2015-2016 Facundo Batista, Nicolás Demarchi
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

from pkg_resources import Requirement

from fades import main, parsing, __version__, VERSION
from tests import generate_test_file


class VirtualenvCheckingTestCase(unittest.TestCase):
    """Tests for the virtualenv checker."""

    def test_have_realprefix(self):
        resp = main.detect_inside_virtualenv('prefix', 'real_prefix', 'base_prefix')
        self.assertTrue(resp)

    def test_no_baseprefix(self):
        resp = main.detect_inside_virtualenv('prefix', None, None)
        self.assertFalse(resp)

    def test_prefix_is_baseprefix(self):
        resp = main.detect_inside_virtualenv('prefix', None, 'prefix')
        self.assertFalse(resp)

    def test_prefix_is_not_baseprefix(self):
        resp = main.detect_inside_virtualenv('prefix', None, 'other prefix')
        self.assertTrue(resp)


class DepsGatheringTestCase(unittest.TestCase):
    """Tests for the gathering stage of consolidate_dependencies."""

    def test_needs_ipython(self):
        d = main.consolidate_dependencies(needs_ipython=True, child_program=None,
                                          requirement_files=None, manual_dependencies=None)

        self.assertDictEqual(d, {'pypi': {Requirement.parse('ipython')}})

    def test_child_program(self):
        child_program = generate_test_file(self, ['"""fades:', 'dep', '"""'])

        d = main.consolidate_dependencies(needs_ipython=False, child_program=child_program,
                                          requirement_files=None, manual_dependencies=None)

        self.assertDictEqual(d, {'pypi': {Requirement.parse('dep')}})

    def test_requirement_files(self):
        requirement_files = [generate_test_file(self, ['dep'])]

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=None)

        self.assertDictEqual(d, {'pypi': {Requirement.parse('dep')}})

    def test_manual_dependencies(self):
        manual_dependencies = ['dep']

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=None,
                                          manual_dependencies=manual_dependencies)

        self.assertDictEqual(d, {'pypi': {Requirement.parse('dep')}})


class DepsMergingTestCase(unittest.TestCase):
    """Tests for the merging stage of consolidate_dependencies."""

    def test_two_different(self):
        requirement_files = [generate_test_file(self, ['1', '2'])]
        manual_dependencies = ['vcs::3', 'vcs::4']

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2')},
            'vcs': {parsing.VCSDependency('3'), parsing.VCSDependency('4')}
        })

    def test_two_same_repo(self):
        requirement_files = [generate_test_file(self, ['1', '2'])]
        manual_dependencies = ['3', '4']

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertDictEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2'), Requirement.parse('3'),
                     Requirement.parse('4')}
        })

    def test_complex_case(self):
        child_program = generate_test_file(self, ['"""fades:', '1', '2', '"""'])
        requirement_files = [generate_test_file(self, ['3', 'vcs::5'])]
        manual_dependencies = ['vcs::4', 'vcs::6']

        d = main.consolidate_dependencies(needs_ipython=False, child_program=child_program,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2'), Requirement.parse('3')},
            'vcs': {parsing.VCSDependency('5'), parsing.VCSDependency('4'),
                    parsing.VCSDependency('6')}
        })

    def test_one_duplicated(self):
        requirement_files = [generate_test_file(self, ['2', '2'])]
        manual_dependencies = None

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertDictEqual(d, {
            'pypi': {Requirement.parse('2')}
        })

    def test_two_different_with_dups(self):
        requirement_files = [generate_test_file(self, ['1', '2', '2', '2'])]
        manual_dependencies = ['vcs::3', 'vcs::4', 'vcs::1', 'vcs::2']

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2')},
            'vcs': {parsing.VCSDependency('1'), parsing.VCSDependency('2'),
                    parsing.VCSDependency('3'), parsing.VCSDependency('4')}
        })


class MiscTestCase(unittest.TestCase):
    """Miscellaneous tests."""

    def test_version_show(self):
        self.assertEqual(
            __version__,
            '.'.join([str(v) for v in VERSION]),
        )
