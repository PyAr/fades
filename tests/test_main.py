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

from fades import main, __version__, VERSION, parsing
from pkg_resources import Requirement


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


class DepsMergingTestCase(unittest.TestCase):
    """Some tests for the dependency merger."""

    def test_needs_ipython(self):
        d = main.consolidate_dependencies(needs_ipython=True)

        self.assertDictEqual(d, {'pypi': {Requirement.parse('ipython')}})

    def test_child_program(self):
        child_path = 'tests/test_files/main_test_child_program.py'

        d = main.consolidate_dependencies(child_program=child_path)

        self.assertDictEqual(d, {'pypi': {Requirement.parse('dep')}})

    def test_requirement_files(self):
        req_path = 'tests/test_files/main_test_requirement_files.txt'

        d = main.consolidate_dependencies(requirement_files=[req_path])

        self.assertDictEqual(d, {'pypi': {Requirement.parse('dep')}})

    def test_manual_dependencies(self):
        d = main.consolidate_dependencies(manual_dependencies=['dep'])

        self.assertDictEqual(d, {'pypi': {Requirement.parse('dep')}})

    def test_two_different(self):
        req_path = 'tests/test_files/main_test_two_different.txt'
        manual_deps = ['vcs::3', 'vcs::4']

        d = main.consolidate_dependencies(requirement_files=[req_path],
                                          manual_dependencies=manual_deps)

        self.assertEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2')},
            'vcs': {parsing.VCSDependency('3'), parsing.VCSDependency('4')}
        })

    def test_two_same_repo(self):
        req_path = 'tests/test_files/main_test_two_same_repo.txt'
        manual_deps = ['pypi::3', 'pypi::4']

        d = main.consolidate_dependencies(requirement_files=[req_path],
                                          manual_dependencies=manual_deps)

        self.assertDictEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2'), Requirement.parse('3'),
                     Requirement.parse('4')}
        })

    def test_complex_case(self):
        child_path = 'tests/test_files/main_test_complex_case.py'
        req_path = 'tests/test_files/main_test_complex_case.txt'
        manual_deps = ['vcs::4', 'vcs::6']

        d = main.consolidate_dependencies(child_program=child_path,
                                          requirement_files=[req_path],
                                          manual_dependencies=manual_deps)

        self.assertEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2'), Requirement.parse('3')},
            'vcs': {parsing.VCSDependency('5'), parsing.VCSDependency('4'),
                    parsing.VCSDependency('6')}
        })

    def test_one_duplicated(self):
        req_path = 'tests/test_files/main_test_one_duplicated.txt'
        manual_deps = []

        d = main.consolidate_dependencies(requirement_files=[req_path],
                                          manual_dependencies=manual_deps)

        self.assertDictEqual(d, {
            'pypi': {Requirement.parse('2')}
        })

    def test_two_different_with_dups(self):
        req_path = 'tests/test_files/main_test_two_different_with_dups.txt'
        manual_deps = ['vcs::3', 'vcs::4', 'vcs::1', 'vcs::2']

        d = main.consolidate_dependencies(requirement_files=[req_path],
                                          manual_dependencies=manual_deps)

        self.assertEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2')},
            'vcs': {parsing.VCSDependency('1'), parsing.VCSDependency('2'),
                    parsing.VCSDependency('3'), parsing.VCSDependency('4')}
        })

    def test_version_show(self):
        self.assertEqual(
            __version__,
            '.'.join([str(v) for v in VERSION]),
        )
