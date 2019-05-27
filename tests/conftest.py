import shutil

from pytest import fixture


@fixture(scope="function")
def tmp_file(tmpdir_factory):
    """ Fixture for a unique tmpfile for each test."""
    dir_path = tmpdir_factory.mktemp("test")
    yield str(dir_path.join("testfile"))  # Converted to str to support python <3.6 versions
    shutil.rmtree(str(dir_path))
