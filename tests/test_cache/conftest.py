import os
from pkg_resources import parse_requirements, Distribution

from pytest import fixture

from fades import cache


@fixture(scope="function")
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


def _get_python_filepaths(roots):
    """Helper to retrieve paths of Python files."""
    python_paths = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".py"):
                    python_paths.append(os.path.join(dirpath, filename))
    return python_paths
