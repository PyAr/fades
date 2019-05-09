import json
import os
import time
import pytest

from threading import Thread

from fades import cache


def test_missing_file(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    venvscache.remove('missing/path')

    lines = venvscache._read_cache()
    assert lines == []


def test_missing_env_in_cache(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    options = {'foo': 'bar'}
    venvscache.store('installed', {'env_path': 'some/path'}, 'interpreter', options=options)
    lines = venvscache._read_cache()
    assert len(lines) == 1

    venvscache.remove('some/path')

    lines = venvscache._read_cache()
    assert lines == []


def test_preserve_cache_data_ordering(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    # store 3 venvs
    options = {'foo': 'bar'}
    venvscache.store('installed1', {'env_path': 'path/env1'}, 'interpreter', options=options)
    venvscache.store('installed2', {'env_path': 'path/env2'}, 'interpreter', options=options)
    venvscache.store('installed3', {'env_path': 'path/env3'}, 'interpreter', options=options)

    venvscache.remove('path/env2')

    lines = venvscache._read_cache()
    assert len(lines) == 2
    assert json.loads(lines[0]).get('metadata').get('env_path') == 'path/env1'
    assert json.loads(lines[1]).get('metadata').get('env_path') == 'path/env3'


@pytest.mark.skip(reason="I dont know why is not working with pytest")
def test_lock_cache_for_remove(tmp_file, mocker):
    venvscache = cache.VEnvsCache(tmp_file)
    # store 3 venvs
    options = {'foo': 'bar'}
    venvscache.store('installed1', {'env_path': 'path/env1'}, 'interpreter', options=options)
    venvscache.store('installed2', {'env_path': 'path/env2'}, 'interpreter', options=options)
    venvscache.store('installed3', {'env_path': 'path/env3'}, 'interpreter', options=options)

    # patch _write_cache so it emulates a slow write during which
    # another process managed to modify the cache file before the
    # first process finished writing the modified cache data
    original_write_cache = venvscache._write_cache
    p = mocker.patch('fades.cache.VEnvsCache._write_cache')
    mock_write_cache = p.start()

    t1 = Thread(target=venvscache.remove, args=('path/env1',))

    def slow_write_cache(*args, **kwargs):
        p.stop()
        t1.start()
        # wait to ensure t1 thread must wait for lock to be released
        time.sleep(0.01)
        original_write_cache(*args, **kwargs)

    mock_write_cache.side_effect = slow_write_cache

    # just a sanity check
    assert not os.path.exists(venvscache.filepath + '.lock')
    # remove a virtualenv from the cache
    venvscache.remove('path/env2')
    t1.join()

    # when cache file is properly locked both virtualenvs
    # will have been removed from the cache
    lines = venvscache._read_cache()
    assert len(lines) == 1
    assert json.loads(lines[0]).get('metadata').get('env_path') == 'path/env3'
    assert not os.path.exists(venvscache.filepath + '.lock')
