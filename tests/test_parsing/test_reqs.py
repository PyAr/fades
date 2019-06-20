"""Check the requirements parsing."""
import io

from pkg_resources import parse_requirements
from fades import parsing, REPO_PYPI, REPO_VCS


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))[0]


def test_empty():
    parsed = parsing._parse_requirement(io.StringIO("""

    """))
    assert parsed == {}


def test_simple():
    parsed = parsing._parse_requirement(io.StringIO("""
        pypi::foo
    """))
    assert parsed == {REPO_PYPI: [get_req('foo')]}


def test_simple_default():
    parsed = parsing._parse_requirement(io.StringIO("""
        foo
    """))
    assert parsed == {REPO_PYPI: [get_req('foo')]}


def test_double():
    parsed = parsing._parse_requirement(io.StringIO("""
        pypi::time
        foo
    """))
    assert parsed == {
        REPO_PYPI: [get_req('time'), get_req('foo')]
    }


def test_version_same():
    parsed = parsing._parse_requirement(io.StringIO("""
        pypi::foo == 3.5
    """))
    assert parsed == {
        REPO_PYPI: [get_req('foo == 3.5')]
    }


def test_version_same_default():
    parsed = parsing._parse_requirement(io.StringIO("""
        foo == 3.5
    """))
    assert parsed == {
        REPO_PYPI: [get_req('foo == 3.5')]
    }


def test_version_different():
    parsed = parsing._parse_requirement(io.StringIO("""
        foo  !=3.5
    """))
    assert parsed == {
        REPO_PYPI: [get_req('foo !=3.5')]
    }


def test_version_same_no_spaces():
    parsed = parsing._parse_requirement(io.StringIO("""
        foo==3.5
    """))
    assert parsed == {
        REPO_PYPI: [get_req('foo ==3.5')]
    }


def test_version_greater_two_spaces():
    parsed = parsing._parse_requirement(io.StringIO("""
        foo   >  2
    """))
    assert parsed == {
        REPO_PYPI: [get_req('foo >  2')]
    }


def test_version_same_or_greater():
    parsed = parsing._parse_requirement(io.StringIO("""
        foo   >=2
    """))
    assert parsed == {
        REPO_PYPI: [get_req('foo >= 2')]
    }


def test_comments():
    parsed = parsing._parse_requirement(io.StringIO("""
        pypi::foo   # some text
        # other text
        bar
    """))
    assert parsed == {
        REPO_PYPI: [get_req('foo'), get_req('bar')]
    }


def test_strange_repo(logged):
    parsed = parsing._parse_requirement(io.StringIO("""
        unknown::foo
    """))
    logged.assert_warning("Not understood fades repository", "unknown")
    assert parsed == {}


def test_vcs_simple():
    parsed = parsing._parse_requirement(io.StringIO("""
        vcs::strangeurl
    """))
    assert parsed == {REPO_VCS: [parsing.VCSDependency("strangeurl")]}


def test_vcs_simple_default():
    parsed = parsing._parse_requirement(io.StringIO("""
        bzrhttp://server/bleh
    """))
    assert parsed == {REPO_VCS: [parsing.VCSDependency("bzrhttp://server/bleh")]}


def test_mixed():
    parsed = parsing._parse_requirement(io.StringIO("""
        vcs::strangeurl
        pypi::foo
    """))
    assert parsed == {
        REPO_VCS: [parsing.VCSDependency("strangeurl")],
        REPO_PYPI: [get_req('foo')],
    }
