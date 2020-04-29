# Copyright 2015-2019 Facundo Batista, Nicolás Demarchi
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

import os
import unittest
from unittest.mock import patch

from pkg_resources import Requirement

from fades import VERSION, FadesError, __version__, main, parsing, REPO_PYPI, REPO_VCS
from tests import create_tempfile


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
        child_program = 'tests/test_files/req_module.py'

        d = main.consolidate_dependencies(needs_ipython=False, child_program=child_program,
                                          requirement_files=None, manual_dependencies=None)

        self.assertDictEqual(d, {'pypi': {Requirement.parse('foo'), Requirement.parse('bar')}})

    def test_requirement_files(self):
        requirement_files = [create_tempfile(self, ['dep'])]

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
        requirement_files = [create_tempfile(self, ['1', '2'])]
        manual_dependencies = ['vcs::3', 'vcs::4']

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2')},
            'vcs': {parsing.VCSDependency('3'), parsing.VCSDependency('4')}
        })

    def test_two_same_repo(self):
        requirement_files = [create_tempfile(self, ['1', '2'])]
        manual_dependencies = ['3', '4']

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertDictEqual(d, {
            'pypi': {Requirement.parse('1'), Requirement.parse('2'), Requirement.parse('3'),
                     Requirement.parse('4')}
        })

    def test_complex_case(self):
        child_program = create_tempfile(self, ['"""fades:', '1', '2', '"""'])
        requirement_files = [create_tempfile(self, ['3', 'vcs::5'])]
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
        requirement_files = [create_tempfile(self, ['2', '2'])]
        manual_dependencies = None

        d = main.consolidate_dependencies(needs_ipython=False, child_program=None,
                                          requirement_files=requirement_files,
                                          manual_dependencies=manual_dependencies)

        self.assertDictEqual(d, {
            'pypi': {Requirement.parse('2')}
        })

    def test_two_different_with_dups(self):
        requirement_files = [create_tempfile(self, ['1', '2', '2', '2'])]
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


class ChildProgramDeciderTestCase(unittest.TestCase):
    """Check how the child program is decided."""

    def test_indicated_with_executable_flag(self):
        analyzable, child = main.decide_child_program(True, "foobar.py")
        self.assertIsNone(analyzable)
        self.assertEqual(child, "foobar.py")

    def test_no_child_at_all(self):
        analyzable, child = main.decide_child_program(False, None)
        self.assertIsNone(analyzable)
        self.assertIsNone(child)

    def test_normal_child_program(self):
        child_path = create_tempfile(self, "")
        analyzable, child = main.decide_child_program(False, child_path)
        self.assertEqual(analyzable, child_path)
        self.assertEqual(child, child_path)

    def test_normal_child_program_not_found(self):
        with self.assertRaises(FadesError):
            main.decide_child_program(False, 'does_not_exist.py')

    def test_normal_child_program_no_access(self):
        child_path = create_tempfile(self, "")
        os.chmod(child_path, 333)  # Remove read permission.
        self.addCleanup(os.chmod, child_path, 644)
        with self.assertRaises(FadesError):
            main.decide_child_program(False, 'does_not_exist.py')

    def test_remote_child_program_simple(self):
        with patch('fades.helpers.download_remote_script') as mock:
            mock.return_value = "new_path_script"
            analyzable, child = main.decide_child_program(False, "http://scripts.com/foobar.py")
            mock.assert_called_with("http://scripts.com/foobar.py")

        # check that analyzable and child are the same, and that its content is the remote one
        self.assertEqual(analyzable, "new_path_script")
        self.assertEqual(child, "new_path_script")

    def test_remote_child_program_ssl(self):
        with patch('fades.helpers.download_remote_script') as mock:
            mock.return_value = "new_path_script"
            analyzable, child = main.decide_child_program(False, "https://scripts.com/foobar.py")
            mock.assert_called_with("https://scripts.com/foobar.py")

        # check that analyzable and child are the same, and that its content is the remote one
        self.assertEqual(analyzable, "new_path_script")
        self.assertEqual(child, "new_path_script")

    def test_indicated_with_executable_flag_with_relative_path(self):
        """Relative paths not allowed when using --exec."""
        with self.assertRaises(FadesError):
            main.decide_child_program(True, os.path.join("path", "../foobar.py"))

    def test_indicated_with_executable_flag_with_absolute_path(self):
        """Absolute paths are allowed when using --exec."""
        analyzable, child = main.decide_child_program(True, "/tmp/foo/bar.py")
        self.assertIsNone(analyzable)
        self.assertEqual(child, "/tmp/foo/bar.py")


# ---------------------------------------
# autoimport tests

def _autoimport_safe_call(*args, **kwargs):
    """Call the tested function and always remove the tempfile after the test."""
    fpath = main.get_autoimport_scriptname(*args, **kwargs)

    with open(fpath, "rt", encoding='utf8') as fh:
        content = fh.read()
    os.unlink(fpath)

    return content


def test_autoimport_simple():
    """Simplest autoimport call."""
    dependencies = {
        REPO_PYPI: {Requirement.parse('mymod')},
    }
    content = _autoimport_safe_call(dependencies, is_ipython=False)

    assert content.startswith(main.AUTOIMPORT_HEADER)
    assert main.AUTOIMPORT_MOD_IMPORTER.format(module='mymod') in content


def test_autoimport_several_dependencies():
    """Indicate several dependencies."""
    dependencies = {
        REPO_PYPI: {Requirement.parse('mymod1'), Requirement.parse('mymod2')},
    }
    content = _autoimport_safe_call(dependencies, is_ipython=False)

    assert content.startswith(main.AUTOIMPORT_HEADER)
    assert main.AUTOIMPORT_MOD_IMPORTER.format(module='mymod1') in content
    assert main.AUTOIMPORT_MOD_IMPORTER.format(module='mymod2') in content


def test_autoimport_including_ipython():
    """Call with ipython modifier."""
    dependencies = {
        REPO_PYPI: {
            Requirement.parse('mymod'),
            Requirement.parse('ipython'),  # this one is automatically added
        },
    }
    content = _autoimport_safe_call(dependencies, is_ipython=True)

    assert main.AUTOIMPORT_HEADER not in content
    assert main.AUTOIMPORT_MOD_IMPORTER.format(module='mymod') in content
    assert 'ipython' not in content


def test_autoimport_no_pypi_dep():
    """Case with no pypi dependencies."""
    dependencies = {
        REPO_PYPI: {Requirement.parse('my_pypi_mod')},
        REPO_VCS: {'my_vcs_dependency'},
    }
    content = _autoimport_safe_call(dependencies, is_ipython=False)

    assert main.AUTOIMPORT_MOD_IMPORTER.format(module='my_pypi_mod') in content
    assert main.AUTOIMPORT_MOD_SKIPPING.format(dependency='my_vcs_dependency') in content


def test_autoimport_importer_mod_ok(capsys):
    """Check the generated code to import a module when works fine."""
    code = main.AUTOIMPORT_MOD_IMPORTER.format(module='time')  # something from stdlib, always ok
    exec(code)
    assert capsys.readouterr().out == "::fades:: automatically imported 'time'\n"


def test_autoimport_importer_mod_fail(capsys):
    """Check the generated code to import a module when works fine."""
    code = main.AUTOIMPORT_MOD_IMPORTER.format(module='not_there_should_explode')
    exec(code)
    assert capsys.readouterr().out == "::fades:: FAILED to autoimport 'not_there_should_explode'\n"
