import os
import shutil

from pytest import fixture


@fixture(scope="function")
def tmp_file(tmpdir_factory):
    """ Fixture for a unique tmpfile for each test."""
    dir_path = tmpdir_factory.mktemp("test")
    yield str(dir_path.join("testfile"))  # Converted to str to support python <3.6 versions
    shutil.rmtree(str(dir_path))


def get_python_filepaths(roots):
    """Helper to retrieve paths of Python files."""
    python_paths = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".py"):
                    python_paths.append(os.path.join(dirpath, filename))
    return python_paths
