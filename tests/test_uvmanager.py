# Copyright 2024-2026 Facundo Batista, Nicolás Demarchi
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

"""Tests for uv related code."""

import pytest
from pathlib import Path
from unittest.mock import patch

from fades.uvmanager import UvManager
from fades import helpers

BIN_PATH = Path("somepath")
UV = "uv"
PYTHON_PATH = str(Path(BIN_PATH) / "python")


def get_manager():
    return UvManager(BIN_PATH, uv_exe=UV)


def test_uv_exe_autodetected():
    with patch.object(helpers, "get_uv_exe", return_value="/path/to/uv"):
        mgr = UvManager(BIN_PATH)
    assert mgr.uv_exe == "/path/to/uv"


def test_get_parsing_ok():
    mocked_stdout = [
        "Name: foo",
        "Version: 2.0.0",
        "Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages",
        "Requires: ",
    ]
    mgr = get_manager()
    with patch.object(helpers, "logged_exec", return_value=mocked_stdout) as mock:
        version = mgr.get_version("foo")
    assert version == "2.0.0"
    mock.assert_called_with(
        [UV, "pip", "show", "--python", PYTHON_PATH, "foo"])


def test_get_parsing_error(logs):
    mocked_stdout = [
        "Name: foo",
        "Release: 2.0.0",
        "Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages",
        "Requires: ",
    ]
    mgr = get_manager()
    with patch.object(helpers, "logged_exec", return_value=mocked_stdout):
        version = mgr.get_version("foo")

    assert version == ""
    assert (
        'Fades is having problems getting the installed version. '
        'Run with -v or check the logs for details'
    ) in logs.error


def test_install():
    mgr = get_manager()
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo")
    mock.assert_called_with([UV, "pip", "install", "--python", PYTHON_PATH, "foo"])


def test_install_multiword_dependency():
    mgr = get_manager()
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo bar")
    mock.assert_called_with([UV, "pip", "install", "--python", PYTHON_PATH, "foo", "bar"])


def test_install_with_options():
    mgr = UvManager(BIN_PATH, options=["--bar baz"], uv_exe=UV)
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo")
    mock.assert_called_with(
        [UV, "pip", "install", "--python", PYTHON_PATH, "foo", "--bar", "baz"])


def test_install_with_options_using_equal():
    mgr = UvManager(BIN_PATH, options=["--bar=baz"], uv_exe=UV)
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo")
    mock.assert_called_with(
        [UV, "pip", "install", "--python", PYTHON_PATH, "foo", "--bar=baz"])


def test_install_raise_error(logs):
    mgr = get_manager()
    with patch.object(helpers, "logged_exec", side_effect=Exception("Kapow!")):
        with pytest.raises(Exception):
            mgr.install("foo")

    assert "Error installing foo: Kapow!" in logs.error


def test_python_exe_resolves_windows_exe(tmp_path):
    # on Windows the venv interpreter is 'python.exe' (no extension-less 'python'); UvManager
    # must point uv's --python at the file that actually exists
    (tmp_path / "python.exe").touch()
    mgr = UvManager(tmp_path, uv_exe=UV)
    assert mgr.python_exe == tmp_path / "python.exe"


def test_python_exe_defaults_to_python(tmp_path):
    # POSIX (and the mocked tests above): plain 'python' is used
    (tmp_path / "python").touch()
    mgr = UvManager(tmp_path, uv_exe=UV)
    assert mgr.python_exe == tmp_path / "python"
