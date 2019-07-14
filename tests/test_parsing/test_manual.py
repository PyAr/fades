"""Tests for the check of the manual parsing."""
from fades import parsing, REPO_PYPI, REPO_VCS
from tests import get_reqs


def test_none():
    parsed = parsing.parse_manual(None)
    assert parsed == {}


def test_nothing():
    parsed = parsing.parse_manual([])
    assert parsed == {}


def test_simple():
    parsed = parsing.parse_manual(["pypi::foo"])
    assert parsed == {REPO_PYPI: get_reqs("foo")}


def test_simple_default_pypi():
    parsed = parsing.parse_manual(["foo"])
    assert parsed == {REPO_PYPI: get_reqs("foo")}


def test_double():
    parsed = parsing.parse_manual(["pypi::foo", "pypi::bar"])
    assert parsed == {REPO_PYPI: get_reqs("foo", "bar")}


def test_version():
    parsed = parsing.parse_manual(["pypi::foo == 3.5"])
    assert parsed == {REPO_PYPI: get_reqs("foo == 3.5")}


def test_version_default():
    parsed = parsing.parse_manual(["foo == 3.5"])
    assert parsed == {REPO_PYPI: get_reqs("foo == 3.5")}


def test_vcs_simple():
    url = "git+git://server.com/etc"
    parsed = parsing.parse_manual(["vcs::" + url])
    assert parsed == {REPO_VCS: [parsing.VCSDependency(url)]}


def test_vcs_simple_default():
    url = "git+git://server.com/etc"
    parsed = parsing.parse_manual([url])
    assert parsed == {REPO_VCS: [parsing.VCSDependency(url)]}


def test_mixed():
    parsed = parsing.parse_manual(["pypi::foo", "vcs::git+git://server.com/etc"])
    assert parsed == {
        REPO_PYPI: get_reqs("foo"),
        REPO_VCS: [parsing.VCSDependency("git+git://server.com/etc")],
    }
