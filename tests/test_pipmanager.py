# Copyright 2015-2018 Facundo Batista, Nicolás Demarchi
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

"""Tests for pip related code."""

import os
import io
import pytest

from fades.pipmanager import PipManager
from fades import pipmanager
from fades import helpers

BIN_PATH = "somepath"


def test_get_parsing_ok_pytest(mocker):
    mocked_stdout = [
        "Name: foo",
        "Version: 2.0.0",
        "Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages",
        "Requires: ",
    ]
    mgr = PipManager(BIN_PATH, pip_installed=True)
    mocker.patch.object(helpers, "logged_exec", return_value=mocked_stdout)
    version = mgr.get_version("foo")
    assert version, "2.0.0"


def test_get_parsing_error(mocker, logged):
    mocked_stdout = [
        "Name: foo",
        "Release: 2.0.0",
        "Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages",
        "Requires: ",
    ]
    mgr = PipManager(BIN_PATH, pip_installed=True)
    mocker.patch.object(helpers, "logged_exec", return_value=mocked_stdout)
    version = mgr.get_version("foo")

    assert version == ""
    logged.assert_error(
        'Fades is having problems getting the installed version. '
        'Run with -v or check the logs for details'
    )


def test_real_case_levenshtein(mocker):
    mocked_stdout = [
        "Metadata-Version: 1.1",
        "Name: python-Levenshtein",
        "Version: 0.12.0",
        "License: GPL",
    ]
    mgr = PipManager(BIN_PATH, pip_installed=True)
    mocker.patch.object(helpers, "logged_exec", return_value=mocked_stdout)
    version = mgr.get_version("foo")
    assert version == "0.12.0"


def test_install(mocker):
    mgr = PipManager(BIN_PATH, pip_installed=True)
    pip_path = os.path.join(BIN_PATH, "pip")
    mock = mocker.patch.object(helpers, "logged_exec")
    mgr.install("foo")
    mock.assert_called_with([pip_path, "install", "foo"])


def test_install_multiword_dependency(mocker):
    mgr = PipManager(BIN_PATH, pip_installed=True)
    pip_path = os.path.join(BIN_PATH, "pip")
    mock = mocker.patch.object(helpers, "logged_exec")
    mgr.install("foo bar")
    mock.assert_called_with([pip_path, "install", "foo", "bar"])


def test_install_with_options(mocker):
    mgr = PipManager(BIN_PATH, pip_installed=True, options=["--bar baz"])
    pip_path = os.path.join(BIN_PATH, "pip")
    mock = mocker.patch.object(helpers, "logged_exec")
    mgr.install("foo")
    mock.assert_called_with([pip_path, "install", "foo", "--bar", "baz"])


def test_install_with_options_using_equal(mocker):
    mgr = PipManager(BIN_PATH, pip_installed=True, options=["--bar=baz"])
    pip_path = os.path.join(BIN_PATH, "pip")
    mock = mocker.patch.object(helpers, "logged_exec")
    mgr.install("foo")
    mock.assert_called_with([pip_path, "install", "foo", "--bar=baz"])


def test_install_raise_error(mocker, logged):
    mgr = PipManager(BIN_PATH, pip_installed=True)
    mocker.patch.object(helpers, "logged_exec", side_effect=Exception("Kapow!"))
    with pytest.raises(Exception):
        mgr.install("foo")

    logged.assert_error("Error installing foo: Kapow!")


def test_install_without_pip(mocker):
    mgr = PipManager(BIN_PATH, pip_installed=False)
    pip_path = os.path.join(BIN_PATH, "pip")
    mocked_exec = mocker.patch.object(helpers, "logged_exec")
    mocked_install_pip = mocker.patch.object(mgr, "_brute_force_install_pip")
    mgr.install("foo")
    assert mocked_install_pip.call_count == 1
    mocked_exec.assert_called_with([pip_path, "install", "foo"])


def test_brute_force_install_pip_installer_exists(mocker, tmp_path):
    tmp_file = str(tmp_path / "hello.txt")
    mgr = PipManager(BIN_PATH, pip_installed=False)
    python_path = os.path.join(BIN_PATH, "python")
    mocked_exec = mocker.patch.object(helpers, "logged_exec")
    download_installer = mocker.patch.object(mgr, "_download_pip_installer")

    # get the tempfile but leave it there to be found
    open(tmp_file, 'wt', encoding='utf8').close()
    mgr.pip_installer_fname = tmp_file
    mgr._brute_force_install_pip()

    assert not download_installer.called
    mocked_exec.assert_called_with([python_path, mgr.pip_installer_fname, "-I"])
    assert mgr.pip_installed


def test_brute_force_install_pip_no_installer(mocker, tmp_path):
    tmp_file = str(tmp_path / "hello.txt")
    mgr = PipManager(BIN_PATH, pip_installed=False)
    python_path = os.path.join(BIN_PATH, "python")
    mocked_exec = mocker.patch.object(helpers, "logged_exec")
    download_installer = mocker.patch.object(mgr, "_download_pip_installer")

    mgr.pip_installer_fname = tmp_file
    mgr._brute_force_install_pip()

    download_installer.assert_called_once_with()
    mocked_exec.assert_called_with([python_path, mgr.pip_installer_fname, "-I"])
    assert mgr.pip_installed


def test_download_pip_installer(mocker, tmp_path):
    tmp_file = str(tmp_path / "hello.txt")
    mgr = PipManager(BIN_PATH, pip_installed=False)

    mgr.pip_installer_fname = tmp_file
    urlopen = mocker.patch("fades.pipmanager.request.urlopen", return_value=io.BytesIO(b"hola"))
    mgr._download_pip_installer()
    assert os.path.exists(mgr.pip_installer_fname)
    urlopen.assert_called_once_with(pipmanager.PIP_INSTALLER)
