# Copyright 2017-2024 Facundo Batista, Nicolás Demarchi
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
import logging
from unittest.mock import patch

import docutils.core
import pydocstyle
import pytest
import rst2html5_
from flake8.api.legacy import get_style_guide
from pyuca import Collator

from tests import get_python_filepaths

FLAKE8_ROOTS = ['fades', 'tests']
FLAKE8_OPTIONS = {'max_line_length': 99, 'select': ['E', 'W', 'F', 'C', 'N']}
PEP257_ROOTS = ['fades']

# avoid seeing all DEBUG logs if the test fails
for logger_name in ('flake8.plugins', 'flake8.api', 'flake8.checker', 'flake8.main'):
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)


def test_flake8_pytest(capsys):
    python_filepaths = get_python_filepaths(FLAKE8_ROOTS)
    style_guide = get_style_guide(**FLAKE8_OPTIONS)
    report = style_guide.check_files(python_filepaths)
    if report.total_errors != 0:
        out, _ = capsys.readouterr()
        pytest.fail(f"There are {report.total_errors} issues!\n{''.join(out)}")


def test_pep257_pytest():
    python_filepaths = get_python_filepaths(PEP257_ROOTS)
    to_ignore = {
        "D105",  # Missing docstring in magic method
        "D107",  # Missing docstring in __init__
    }
    to_include = pydocstyle.violations.conventions.pep257 - to_ignore
    result = list(pydocstyle.check(python_filepaths, select=to_include))
    assert len(result) == 0, "There are issues!\n" + '\n'.join(map(str, result))


def test_readme_sanity():
    fake_stdout = io.StringIO()  # just to ignore the output
    fake_stderr = io.StringIO()  # will have content if there are problems
    with open('README.rst', 'rt', encoding='utf8') as fh:
        with patch('sys.stdout', fake_stdout):
            with patch('sys.stderr', fake_stderr):
                docutils.core.publish_file(source=fh, writer=rst2html5_.HTML5Writer())

    errors = fake_stderr.getvalue()
    assert not bool(errors), "There are issues!\n" + errors


def test_authors_ordering():
    with open('AUTHORS', 'rt', encoding='utf8') as fh:
        authors = fh.readlines()
    ordered_authors = sorted(authors, key=Collator().sort_key)
    assert authors == ordered_authors
