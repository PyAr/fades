# Copyright 2019-2024 Facundo Batista, Nicolás Demarchi
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

import uuid

from pytest import fixture


@fixture(scope="function")
def tmp_file(tmp_path):
    """Fixture for a unique tmpfile for each test."""
    yield str(tmp_path / "testfile")  # XXX Facundo 2024-04-17: remove str() after #435


@fixture(scope="function")
def create_tmpfile(tmp_path):

    def add_content(lines):
        """Fixture for a unique tmpfile for each test."""
        namefile = tmp_path / f"testfile_{uuid.uuid4()}"
        with open(namefile, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

        return namefile

    yield add_content


def pytest_addoption(parser):
    """Define new pytest command line argument to be used by integration tests."""
    parser.addoption("--integtest-pyversion", action="store")
