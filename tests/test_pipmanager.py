# Copyright 2015-2022 Facundo Batista, Nicolás Demarchi
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
from unittest.mock import patch, call

from fades.pipmanager import PipManager
from fades import pipmanager
from fades import helpers

BIN_PATH = "somepath"


def test_get_parsing_ok_pytest():
    mocked_stdout = [
        "Name: foo",
        "Version: 2.0.0",
        "Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages",
        "Requires: ",
    ]
    mgr = PipManager(BIN_PATH, pip_installed=True)
    with patch.object(helpers, "logged_exec", return_value=mocked_stdout):
        version = mgr.get_version("foo")
    assert version, "2.0.0"


def test_get_parsing_error(logs):
    mocked_stdout = [
        "Name: foo",
        "Release: 2.0.0",
        "Location: ~/.local/share/fades/86cc492/lib/python3.4/site-packages",
        "Requires: ",
    ]
    mgr = PipManager(BIN_PATH, pip_installed=True)
    with patch.object(helpers, "logged_exec", return_value=mocked_stdout):
        version = mgr.get_version("foo")

    assert version == ""
    assert (
        'Fades is having problems getting the installed version. '
        'Run with -v or check the logs for details'
    ) in logs.error


def test_real_case_levenshtein():
    mocked_stdout = [
        "Metadata-Version: 1.1",
        "Name: python-Levenshtein",
        "Version: 0.12.0",
        "License: GPL",
    ]
    mgr = PipManager(BIN_PATH, pip_installed=True)
    with patch.object(helpers, "logged_exec", return_value=mocked_stdout):
        version = mgr.get_version("foo")
    assert version == "0.12.0"


def test_install():
    mgr = PipManager(BIN_PATH, pip_installed=True)
    pip_path = os.path.join(BIN_PATH, "pip")
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo")

    # check it always upgrades pip, and then the proper install
    python_path = os.path.join(BIN_PATH, "python")
    c1 = call([python_path, "-m", "pip", "install", "pip", "--upgrade"])
    c2 = call([pip_path, "install", "foo"])
    assert mock.call_args_list == [c1, c2]


def test_install_without_pip_upgrade():
    mgr = PipManager(BIN_PATH, pip_installed=True, avoid_pip_upgrade=True)
    pip_path = os.path.join(BIN_PATH, "pip")
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo")
    mock.assert_called_with([pip_path, "install", "foo"])


def test_install_multiword_dependency():
    mgr = PipManager(BIN_PATH, pip_installed=True)
    pip_path = os.path.join(BIN_PATH, "pip")
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo bar")
    mock.assert_called_with([pip_path, "install", "foo", "bar"])


def test_install_with_options():
    mgr = PipManager(BIN_PATH, pip_installed=True, options=["--bar baz"])
    pip_path = os.path.join(BIN_PATH, "pip")
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo")
    mock.assert_called_with([pip_path, "install", "foo", "--bar", "baz"])


def test_install_with_options_using_equal():
    mgr = PipManager(BIN_PATH, pip_installed=True, options=["--bar=baz"])
    pip_path = os.path.join(BIN_PATH, "pip")
    with patch.object(helpers, "logged_exec") as mock:
        mgr.install("foo")
    mock.assert_called_with([pip_path, "install", "foo", "--bar=baz"])


def test_install_raise_error(logs):
    mgr = PipManager(BIN_PATH, pip_installed=True)
    with patch.object(helpers, "logged_exec", side_effect=['ok', Exception("Kapow!")]):
        with pytest.raises(Exception):
            mgr.install("foo")

    assert "Error installing foo: Kapow!" in logs.error


def test_install_without_pip():
    mgr = PipManager(BIN_PATH, pip_installed=False)
    pip_path = os.path.join(BIN_PATH, "pip")
    with patch.object(helpers, "logged_exec") as mocked_exec:
        with patch.object(mgr, "_brute_force_install_pip") as mocked_install_pip:
            mgr.install("foo")
    assert mocked_install_pip.call_count == 1
    mocked_exec.assert_called_with([pip_path, "install", "foo"])


def test_brute_force_install_pip_installer_exists(tmp_path):
    tmp_file = str(tmp_path / "hello.txt")
    mgr = PipManager(BIN_PATH, pip_installed=False)
    python_path = os.path.join(BIN_PATH, "python")

    # get the tempfile but leave it there to be found
    open(tmp_file, 'wt', encoding='utf8').close()
    mgr.pip_installer_fname = tmp_file

    with patch.object(helpers, "logged_exec") as mocked_exec:
        with patch.object(mgr, "_download_pip_installer") as download_installer:
            mgr._brute_force_install_pip()

    assert not download_installer.called
    mocked_exec.assert_called_with([python_path, mgr.pip_installer_fname, "-I"])
    assert mgr.pip_installed


def test_brute_force_install_pip_no_installer(tmp_path):
    tmp_file = str(tmp_path / "hello.txt")
    mgr = PipManager(BIN_PATH, pip_installed=False)
    python_path = os.path.join(BIN_PATH, "python")

    mgr.pip_installer_fname = tmp_file
    with patch.object(helpers, "logged_exec") as mocked_exec:
        with patch.object(mgr, "_download_pip_installer") as download_installer:
            mgr._brute_force_install_pip()

    download_installer.assert_called_once_with()
    mocked_exec.assert_called_with([python_path, mgr.pip_installer_fname, "-I"])
    assert mgr.pip_installed


def test_download_pip_installer(tmp_path):
    tmp_file = str(tmp_path / "hello.txt")
    mgr = PipManager(BIN_PATH, pip_installed=False)

    mgr.pip_installer_fname = tmp_file
    with patch("fades.pipmanager.request.urlopen", return_value=io.BytesIO(b"hola")) as urlopen:
        mgr._download_pip_installer()
    assert os.path.exists(mgr.pip_installer_fname)
    urlopen.assert_called_once_with(pipmanager.PIP_INSTALLER)


def test_freeze(tmp_path):
    tmp_file = str(tmp_path / "reqtest.txt")

    # call and check pip was executed ok
    mgr = PipManager(BIN_PATH)
    with patch.object(helpers, "logged_exec") as mock:
        mock.return_value = ['moño>11', 'foo==1.2']  # "bad" order, on purpose
        mgr.freeze(tmp_file)

    pip_path = os.path.join(BIN_PATH, "pip")
    mock.assert_called_with([pip_path, "freeze", "--all", "--local"])

    # check results were stored properly
    with open(tmp_file, 'rt', encoding='utf8') as fh:
        stored = fh.read()
    assert stored == 'foo==1.2\nmoño>11\n'
