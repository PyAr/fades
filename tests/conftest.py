import os
import pytest

from pkg_resources import parse_requirements, Distribution

from fades import cache


@pytest.fixture(scope="function")
def tmp_file(tmpdir_factory):
    # Converted to str to support python <3.6 versions
    path = str(tmpdir_factory.mktemp("test").join("foo.bar"))
    yield path
    if os.path.isfile(path):
        os.remove(path)


@pytest.fixture(scope="function")
def venvscache(tmpdir_factory):
    path = tmpdir_factory.mktemp("test").join("foo.bar")
    venvs_cache = cache.VEnvsCache(path)
    yield venvs_cache
    del venvs_cache


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))


def get_distrib(*dep_ver_pairs):
    """Build some Distributions with indicated info."""
    return [Distribution(project_name=dep, version=ver) for dep, ver in dep_ver_pairs]
