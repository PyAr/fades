# Copyright 2014-2026 Facundo Batista, Nicolás Demarchi
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

"""Check the PEP 723 inline script metadata parsing."""

from unittest.mock import patch

import pytest

from fades import FadesError, parsing, REPO_PYPI

from tests import get_reqs


def test_no_block():
    deps, requires_python = parsing._parse_pep723("import time\nprint('hi')\n")
    assert deps == {}
    assert requires_python is None


def test_simple_dependencies():
    content = (
        "# /// script\n"
        "# dependencies = [\n"
        '#   "requests<3",\n'
        '#   "rich",\n'
        "# ]\n"
        "# ///\n"
        "import requests\n"
    )
    deps, requires_python = parsing._parse_pep723(content)
    assert deps == {REPO_PYPI: get_reqs("requests<3", "rich")}
    assert requires_python is None


def test_requires_python():
    content = (
        "# /// script\n"
        '# requires-python = ">=3.11"\n'
        "# dependencies = []\n"
        "# ///\n"
    )
    deps, requires_python = parsing._parse_pep723(content)
    assert deps == {}
    assert requires_python == ">=3.11"


def test_requires_python_bounded_range():
    content = (
        "# /// script\n"
        '# requires-python = ">=3.10,<3.12"\n'
        "# dependencies = []\n"
        "# ///\n"
    )
    deps, requires_python = parsing._parse_pep723(content)
    assert deps == {}
    assert requires_python == ">=3.10,<3.12"


def test_empty_dependencies():
    content = (
        "# /// script\n"
        "# dependencies = []\n"
        "# ///\n"
    )
    deps, requires_python = parsing._parse_pep723(content)
    assert deps == {}
    assert requires_python is None


def test_non_script_block_is_ignored():
    content = (
        "# /// pyproject\n"
        "# dependencies = [\n"
        '#   "requests",\n'
        "# ]\n"
        "# ///\n"
    )
    deps, requires_python = parsing._parse_pep723(content)
    assert deps == {}
    assert requires_python is None


def test_comment_prefix_stripping():
    # a bare '#' line (no trailing space) must be stripped of just one char, while
    # '# ' lines are stripped of two
    content = (
        "# /// script\n"
        "#\n"
        "# dependencies = [\n"
        '#   "requests",\n'
        "# ]\n"
        "# ///\n"
    )
    deps, requires_python = parsing._parse_pep723(content)
    assert deps == {REPO_PYPI: get_reqs("requests")}


def test_multiple_script_blocks_error(logs):
    content = (
        "# /// script\n"
        "# dependencies = []\n"
        "# ///\n"
        "\n"
        "import sys\n"
        "\n"
        "# /// script\n"
        "# dependencies = []\n"
        "# ///\n"
    )
    with pytest.raises(FadesError):
        parsing._parse_pep723(content)
    assert "only one is allowed" in logs.error


def test_invalid_toml(logs):
    content = (
        "# /// script\n"
        '# dependencies = ["unclosed\n'
        "# ///\n"
    )
    with pytest.raises(FadesError):
        parsing._parse_pep723(content)
    assert "Invalid TOML in the PEP 723 metadata block" in logs.error


def test_invalid_dependency(logs):
    content = (
        "# /// script\n"
        "# dependencies = [\n"
        '#   "not a valid requirement!!",\n'
        "# ]\n"
        "# ///\n"
    )
    with pytest.raises(FadesError):
        parsing._parse_pep723(content)
    assert "Invalid dependency in the PEP 723 metadata block" in logs.error


def test_dependencies_not_a_list(logs):
    content = (
        "# /// script\n"
        '# dependencies = "requests"\n'
        "# ///\n"
    )
    with pytest.raises(FadesError):
        parsing._parse_pep723(content)
    assert "must be a list" in logs.error


def test_no_toml_parser_available(logs):
    content = (
        "# /// script\n"
        "# dependencies = [\n"
        '#   "requests",\n'
        "# ]\n"
        "# ///\n"
    )
    with patch.object(parsing, "tomllib", None):
        deps, requires_python = parsing._parse_pep723(content)
    assert deps == {}
    assert requires_python is None
    assert "no TOML parser is available" in logs.warning


def test_parse_pep723_none():
    assert parsing.parse_pep723(None) == ({}, None)


def test_parse_pep723_file_basic():
    deps, requires_python = parsing.parse_pep723("tests/test_files/pep723_basic.py")
    assert deps == {REPO_PYPI: get_reqs("requests<3", "rich")}
    assert requires_python is None


def test_parse_pep723_file_requires_python():
    deps, requires_python = parsing.parse_pep723(
        "tests/test_files/pep723_requires_python.py")
    assert deps == {REPO_PYPI: get_reqs("requests<3")}
    assert requires_python == ">=3.11"
