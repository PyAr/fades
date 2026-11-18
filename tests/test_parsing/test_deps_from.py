# Copyright 2026 Facundo Batista, Nicolás Demarchi
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

"""Check the parsing of the files indicated with --deps-from."""

from pathlib import Path

import pytest

from fades import FadesError, parsing, REPO_PYPI, REPO_VCS

from tests import get_reqs


def test_missing_file(tmp_path):
    path = tmp_path / "nonexistent.txt"
    with pytest.raises(FadesError):
        parsing.parse_deps_from(path)


def test_unsupported_file(tmp_path):
    for name in ("deps.toml", "deps.in", "deps.md", "deps"):
        path = tmp_path / name
        path.write_text("whatever", encoding="utf8")
        with pytest.raises(FadesError):
            parsing.parse_deps_from(path)


def test_txt(tmp_path):
    path = tmp_path / "reqs.txt"
    path.write_text("requests<3\n# a comment\nvcs::foo\n", encoding="utf8")

    deps, requires_python = parsing.parse_deps_from(path)

    assert deps == {
        REPO_PYPI: get_reqs("requests<3"),
        REPO_VCS: [parsing.VCSDependency("foo")],
    }
    assert requires_python is None


def test_txt_uppercase_suffix(tmp_path):
    path = tmp_path / "reqs.TXT"
    path.write_text("rich\n", encoding="utf8")

    deps, requires_python = parsing.parse_deps_from(path)

    assert deps == {REPO_PYPI: get_reqs("rich")}
    assert requires_python is None


def test_py():
    path = Path("tests/test_files/pep723_and_comment.py")

    deps, requires_python = parsing.parse_deps_from(path)

    assert deps == {REPO_PYPI: set(get_reqs("requests", "requests<3", "rich"))}
    assert requires_python == ">=3.11"


def test_py_with_requires_python():
    path = Path("tests/test_files/pep723_requires_python.py")

    deps, requires_python = parsing.parse_deps_from(path)

    assert deps == {REPO_PYPI: set(get_reqs("requests<3"))}
    assert requires_python == ">=3.11"


def _write_pyproject(tmp_path, content):
    path = tmp_path / "pyproject.toml"
    path.write_text(content, encoding="utf8")
    return path


def test_pyproject_basic(tmp_path):
    path = _write_pyproject(tmp_path, """
[project]
name = "test"
dependencies = [
    "requests<3",
    "rich",
]
""")

    deps, requires_python = parsing.parse_deps_from(path)

    assert deps == {REPO_PYPI: get_reqs("requests<3", "rich")}
    assert requires_python is None


def test_pyproject_url_dependency(tmp_path):
    path = _write_pyproject(tmp_path, """
[project]
dependencies = ["foo @ git+https://github.com/bar/foo"]
""")

    deps, _ = parsing.parse_deps_from(path)

    assert deps == {REPO_VCS: [parsing.VCSDependency("foo @ git+https://github.com/bar/foo")]}


def test_pyproject_invalid_dependency(tmp_path):
    path = _write_pyproject(tmp_path, """
[project]
dependencies = ["foo bar!!"]
""")

    with pytest.raises(FadesError):
        parsing.parse_deps_from(path)


def test_pyproject_no_project_table(tmp_path):
    path = _write_pyproject(tmp_path, """
[tool.poetry.dependencies]
requests = "*"
""")

    with pytest.raises(FadesError):
        parsing.parse_deps_from(path)


def test_pyproject_no_dependencies(tmp_path):
    path = _write_pyproject(tmp_path, """
[project]
name = "test"
""")

    deps, requires_python = parsing.parse_deps_from(path)

    assert deps == {}
    assert requires_python is None


def test_pyproject_dynamic_dependencies(tmp_path):
    path = _write_pyproject(tmp_path, """
[project]
name = "test"
dynamic = ["dependencies"]
""")

    deps, _ = parsing.parse_deps_from(path)

    assert deps == {}


def test_pyproject_dependencies_not_a_list(tmp_path):
    path = _write_pyproject(tmp_path, """
[project]
dependencies = "requests"
""")

    with pytest.raises(FadesError):
        parsing.parse_deps_from(path)


def test_pyproject_invalid_toml(tmp_path):
    path = _write_pyproject(tmp_path, "[project\ndependencies = []\n")

    with pytest.raises(FadesError):
        parsing.parse_deps_from(path)


def test_pyproject_optional_dependencies_not_included(tmp_path):
    path = _write_pyproject(tmp_path, """
[project]
dependencies = ["rich"]

[project.optional-dependencies]
dev = ["pytest"]
""")

    deps, _ = parsing.parse_deps_from(path)

    assert deps == {REPO_PYPI: get_reqs("rich")}


def test_merge_requires_python_nothing():
    assert parsing.merge_requires_python([]) is None
    assert parsing.merge_requires_python([None, None]) is None
    assert parsing.merge_requires_python([None, ""]) is None


def test_merge_requires_python_single():
    assert parsing.merge_requires_python([">=3.11"]) == ">=3.11"


def test_merge_requires_python_several():
    assert parsing.merge_requires_python([">=3.11", None, "<4", ""]) == ">=3.11, <4"
