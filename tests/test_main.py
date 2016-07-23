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

import os
import sys
import tempfile
import unittest

from unittest.mock import patch

from fades import main, __version__, VERSION


class VirtualenvCheckingTestCase(unittest.TestCase):
    """Tests for the virtualenv checker."""

    def test_no_virtualenv(self):
        with patch.dict(os.environ, {}, clear=True):
            resp = main.detect_inside_virtualenv()
        self.assertIsNone(resp)

    def test_in_virtualenv(self):
        # set up a temp file
        _, fpath = tempfile.mkstemp(prefix="test-temp-file")
        self.addCleanup(os.remove, fpath)

        with patch.dict(os.environ, {'VIRTUAL_ENV': '/tmp/test-'}):
            with patch.object(sys, 'executable', fpath):
                resp = main.detect_inside_virtualenv()
        self.assertEqual(resp, fpath)

    def test_in_symlinked_virtualenv(self):
        # set up a temp file and a symlink to it
        _, fpath1 = tempfile.mkstemp(prefix="test1-temp-file")
        _, fpath2 = tempfile.mkstemp(prefix="test2-temp-file")
        os.remove(fpath2)
        os.symlink(fpath1, fpath2)
        self.addCleanup(os.remove, fpath1)
        self.addCleanup(os.remove, fpath2)

        with patch.dict(os.environ, {'VIRTUAL_ENV': '/tmp/test1-'}):
            with patch.object(sys, 'executable', fpath2):
                resp = main.detect_inside_virtualenv()
        self.assertEqual(resp, fpath1)


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
