# Copyright 2017 Facundo Batista, Nicolás Demarchi
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

"""Tests for infrastructure stuff."""

import io
import os
import logging
import docutils.core
import pep257
import rst2html5_

from flake8.api.legacy import get_style_guide
from pyuca import Collator

FLAKE8_ROOTS = ['fades', 'tests']
FLAKE8_OPTIONS = ['--max-line-length=99', '--select=E,W,F,C,N']
PEP257_ROOTS = ['fades']

# avoid seeing all DEBUG logs if the test fails
pep257.log.setLevel(logging.WARNING)
for logger_name in ('flake8.plugins', 'flake8.api', 'flake8.checker', 'flake8.main'):
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)


def _get_python_filepaths(roots):
    """Helper to retrieve paths of Python files."""
    python_paths = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".py"):
                    python_paths.append(os.path.join(dirpath, filename))
    return python_paths


def test_flake8_pytest(mocker):
    python_filepaths = _get_python_filepaths(FLAKE8_ROOTS)
    style_guide = get_style_guide(paths=FLAKE8_OPTIONS)
    fake_stdout = io.StringIO()
    mocker.patch('sys.stdout', fake_stdout)
    report = style_guide.check_files(python_filepaths)
    assert report.total_errors == 0, "There are issues!\n" + fake_stdout.getvalue()


def test_pep257_pytest():
    python_filepaths = _get_python_filepaths(PEP257_ROOTS)
    result = list(pep257.check(python_filepaths))
    assert len(result) == 0, "There are issues!\n" + '\n'.join(map(str, result))


def test_readme_sanity(mocker):
    fake_stdout = io.StringIO()  # just to ignore the output
    fake_stderr = io.StringIO()  # will have content if there are problems
    with open('README.rst', 'rt', encoding='utf8') as fh:
        mocker.patch('sys.stdout', fake_stdout)
        mocker.patch('sys.stderr', fake_stderr)
        docutils.core.publish_file(source=fh, writer=rst2html5_.HTML5Writer())

    errors = fake_stderr.getvalue()
    assert not bool(errors), "There are issues!\n" + errors


def test_authors_ordering():
    with open('AUTHORS', 'rt', encoding='utf8') as fh:
        authors = fh.readlines()
    ordered_authors = sorted(authors, key=Collator().sort_key)
    assert authors == ordered_authors
