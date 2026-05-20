# Copyright 2015-2026 Facundo Batista, Nicolás Demarchi
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

import json
import os
import time
from pathlib import Path

from threading import Thread

from fades import cache


def test_missing_file(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    venvscache.remove("missing/path")

    lines = venvscache._read_cache()
    assert lines == []


def test_missing_env_in_cache(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    options = {"foo": "bar"}
    metadata = {"env_path": "some/path", "env_bin_path": "other/path"}
    venvscache.store("installed", metadata, "interpreter", options=options)
    lines = venvscache._read_cache()
    assert len(lines) == 1

    venvscache.remove(Path("some/path"))

    lines = venvscache._read_cache()
    assert lines == []


def test_preserve_cache_data_ordering(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    # store 3 venvs
    options = {"foo": "bar"}
    metadata1 = {"env_path": "path/env1", "env_bin_path": "other/path"}
    metadata2 = {"env_path": "path/env2", "env_bin_path": "other/path"}
    metadata3 = {"env_path": "path/env3", "env_bin_path": "other/path"}
    venvscache.store("installed1", metadata1, "interpreter", options=options)
    venvscache.store("installed2", metadata2, "interpreter", options=options)
    venvscache.store("installed3", metadata3, "interpreter", options=options)

    venvscache.remove(Path("path/env2"))

    lines = venvscache._read_cache()
    assert len(lines) == 2
    assert json.loads(lines[0]).get("metadata").get("env_path") == "path/env1"
    assert json.loads(lines[1]).get("metadata").get("env_path") == "path/env3"


def test_lock_cache_for_remove(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    # store 3 venvs
    options = {"foo": "bar"}
    metadata1 = {"env_path": "path/env1", "env_bin_path": "other/path"}
    metadata2 = {"env_path": "path/env2", "env_bin_path": "other/path"}
    metadata3 = {"env_path": "path/env3", "env_bin_path": "other/path"}
    venvscache.store("installed1", metadata1, "interpreter", options=options)
    venvscache.store("installed2", metadata2, "interpreter", options=options)
    venvscache.store("installed3", metadata3, "interpreter", options=options)

    # patch _write_cache so it emulates a slow write during which
    # another process managed to modify the cache file before the
    # first process finished writing the modified cache data
    original_write_cache = venvscache._write_cache

    other_process = Thread(target=venvscache.remove, args=(Path("path/env1"),))

    def slow_write_cache(*args, **kwargs):
        venvscache._write_cache = original_write_cache

        # start "other process" and wait a little to ensure it must wait
        # for the lock to be released
        other_process.start()
        time.sleep(0.01)

        original_write_cache(*args, **kwargs)

    venvscache._write_cache = slow_write_cache

    # just a sanity check
    assert not os.path.exists(venvscache.filepath.name + ".lock")
    # remove a virtualenv from the cache
    venvscache.remove(Path("path/env2"))
    other_process.join()

    # when cache file is properly locked both virtualenvs
    # will have been removed from the cache
    lines = venvscache._read_cache()
    assert len(lines) == 1
    assert json.loads(lines[0])["metadata"]["env_path"] == "path/env3"
    assert not os.path.exists(venvscache.filepath.name + ".lock")
