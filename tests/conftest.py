import shutil
import uuid

from logassert import logassert
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


@fixture()
def logged():
    """Fixture to assert on loggings."""

    class FixtureLogChecker(logassert.SetupLogChecker):

        _translation = [
            ("assertLogged", "assert_logged"),
            ("assertLoggedError", "assert_error"),
            ("assertLoggedWarning", "assert_warning"),
            ("assertLoggedInfo", "assert_info"),
            ("assertLoggedDebug", "assert_debug"),
            ("assertNotLogged", "assert_not_logged"),
            ("assertNotLoggedError", "assert_not_error"),
            ("assertNotLoggedWarning", "assert_not_warning"),
            ("assertNotLoggedInfo", "assert_not_info"),
            ("assertNotLoggedDebug", "assert_not_debug"),
        ]

        def __init__(self, logpath):
            super().__init__(self, logpath)

            # old testing API translation
            for old_name, new_name in self._translation:
                setattr(self, new_name, getattr(self, old_name))

        def fail(self, message):
            """Called by logassert.SetupLogChecker on failure."""
            raise AssertionError(message)

    return FixtureLogChecker("fades")
