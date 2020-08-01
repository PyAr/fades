"""Check the requirements parsing from a reqs.txt file."""
import os

from fades import parsing, REPO_PYPI

from tests import get_reqs


def test_requirement_files(create_tmpfile):
    parsed = parsing.parse_reqfile(create_tmpfile(['foo']))
    assert parsed == {REPO_PYPI: get_reqs('foo')}


def test_nested_requirement_files(create_tmpfile):
    requirement_file = create_tmpfile(['foo'])
    requirement_file_nested = create_tmpfile(
        ['bar\n-r {}'.format(requirement_file)]
    )
    parsed = parsing.parse_reqfile(requirement_file_nested)

    assert parsed == {REPO_PYPI: get_reqs('bar', 'foo')}


def test_nested_requirement_files_invalid_format(logs, create_tmpfile):
    requirement_file_nested = create_tmpfile(['foo\n-r'])
    parsed = parsing.parse_reqfile(requirement_file_nested)

    assert parsed == {REPO_PYPI: get_reqs('foo')}
    assert "Invalid format to indicate a nested requirements file:" in logs.warning


def test_nested_requirement_files_not_pwd(create_tmpfile):
    requirement_file = create_tmpfile(['foo'])
    fname = os.path.basename(requirement_file)
    requirement_file_nested = create_tmpfile(
        ['bar\n-r {}'.format(fname)])
    parsed = parsing.parse_reqfile(requirement_file_nested)

    assert parsed, {REPO_PYPI: get_reqs('bar', 'foo')}


def test_nested_requirement_files_first_line(create_tmpfile):
    requirement_file = create_tmpfile(['foo'])
    requirement_file_nested = create_tmpfile(
        ['\n-r {}\nbar'.format(requirement_file)])
    parsed = parsing.parse_reqfile(requirement_file_nested)

    assert parsed == {REPO_PYPI: get_reqs('foo', 'bar')}


def test_two_nested_requirement_files(create_tmpfile):
    requirement_file = create_tmpfile(['foo'])
    requirement_file_nested1 = create_tmpfile(
        ['bar\n-r {}'.format(requirement_file)])
    requirement_file_nested2 = create_tmpfile(
        ['baz\n-r {}'.format(requirement_file_nested1)])
    parsed = parsing.parse_reqfile(requirement_file_nested2)

    assert parsed == {REPO_PYPI: get_reqs('baz', 'bar', 'foo')}
