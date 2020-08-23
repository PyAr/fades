import shutil
import uuid

from pytest import fixture


@fixture(scope="function")
def tmp_file(tmpdir_factory):
    """Fixture for a unique tmpfile for each test."""
    dir_path = tmpdir_factory.mktemp("test")
    yield str(dir_path.join("testfile"))  # Converted to str to support python <3.6 versions
    shutil.rmtree(str(dir_path))


@fixture(scope="function")
def create_tmpfile(tmpdir_factory):
    dir_path = tmpdir_factory.mktemp("test")

    def add_content(lines):
        """Fixture for a unique tmpfile for each test."""
        namefile = str(
            dir_path.join("testfile_{}".format(uuid.uuid4()))
        )  # Converted to str to support python <3.6 versions
        with open(namefile, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")

        return namefile

    yield add_content
    shutil.rmtree(str(dir_path))
