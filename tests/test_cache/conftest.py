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

import shutil

from pytest import fixture

from fades import cache


@fixture(scope="function")
def venvscache(tmpdir_factory):
    """Fixture for a cache file for virtualenvs."""
    dir_path = tmpdir_factory.mktemp("test")
    venvs_cache = cache.VEnvsCache(dir_path.join("test_venv_cache"))
    yield venvs_cache
    shutil.rmtree(str(dir_path))
