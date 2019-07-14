"""Check the imports parsing."""
import io

from fades import parsing, REPO_PYPI, REPO_VCS

from tests import get_reqs


def test_nocomment():
    # note that we're testing the import at the beginning of the line, and
    # in also indented
    parsed = parsing._parse_content(io.StringIO("""import time
        import time
        from time import foo
    """))
    assert parsed == {}


def test_simple_default():
    parsed = parsing._parse_content(io.StringIO("""
        import time
        import foo    # fades
    """))
    assert parsed == {REPO_PYPI: get_reqs('foo')}


def test_double():
    parsed = parsing._parse_content(io.StringIO("""
        import time  # fades
        import foo   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('time') + get_reqs('foo')
    }


def test_version_same_default():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades == 3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo == 3.5')
    }


def test_version_different():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades !=3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo !=3.5')
    }


def test_version_same_no_spaces():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades==3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo ==3.5')
    }


def test_version_same_two_spaces():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades  ==  3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo ==  3.5')
    }


def test_version_same_one_space_before():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades == 3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo == 3.5')
    }


def test_version_same_two_space_before():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades  == 3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo == 3.5')
    }


def test_version_same_one_space_after():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades== 3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo == 3.5')
    }


def test_version_same_two_space_after():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades==  3.5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo ==  3.5')
    }


def test_version_greater():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades > 2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo > 2')
    }


def test_version_greater_no_space():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades>2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >2')
    }


def test_version_greater_no_space_default():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades>2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >2')
    }


def test_version_greater_two_spaces():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades  >  2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >  2')
    }


def test_version_greater_one_space_after():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades> 2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo > 2')
    }


def test_version_greater_two_space_after():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades>  2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo > 2')
    }


def test_version_greater_one_space_before():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades> 2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo > 2')
    }


def test_version_greater_two_space_before():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades>  2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo > 2')
    }


def test_version_same_or_greater():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades >= 2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >= 2')
    }


def test_version_same_or_greater_no_spaces():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades>=2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >= 2')
    }


def test_version_same_or_greater_one_space_before():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades >=2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >=2')
    }


def test_version_same_or_greater_two_space_before():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades  >=2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >=2')
    }


def test_version_same_or_greater_one_space_after():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades>= 2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >= 2')
    }


def test_version_same_or_greater_two_space_after():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades>=  2
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo >= 2')
    }


def test_continuation_line():
    parsed = parsing._parse_content(io.StringIO("""
        import bar
        # fades > 2
        import foo
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo > 2')
    }


def test_from_import_simple():
    parsed = parsing._parse_content(io.StringIO("""
        from foo import bar   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo')
    }


def test_import():
    parsed = parsing._parse_content(io.StringIO("""
        import foo.bar   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo')
    }


def test_from_import_complex():
    parsed = parsing._parse_content(io.StringIO("""
        from baz.foo import bar   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('baz')
    }


def test_allow_other_comments():
    parsed = parsing._parse_content(io.StringIO("""
        from foo import *   # NOQA   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo')
    }


def test_allow_other_comments_reverse_default():
    parsed = parsing._parse_content(io.StringIO("""
        from foo import * # fades # NOQA
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo')
    }


def test_strange_import(logged):
    parsed = parsing._parse_content(io.StringIO("""
        from foo bar import :(   # fades
    """))
    logged.assert_debug(
        "Not understood import info",
        "['from', 'foo', 'bar', 'import', ':(']"
    )
    assert parsed == {}


def test_strange_fadesinfo(logged):
    parsed = parsing._parse_content(io.StringIO("""
        import foo   # fades  broken::whatever
    """))
    logged.assert_warning("Not understood fades repository", "broken")
    assert parsed == {}


def test_strange_fadesinfo2(logged):
    parsed = parsing._parse_content(io.StringIO("""
        import foo   # fadesbroken
    """))
    logged.assert_warning("Not understood fades info", "fadesbroken")
    assert parsed == {}


def test_projectname_noversion_implicit():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades othername
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('othername')
    }


def test_projectname_noversion_explicit():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades pypi::othername
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('othername')
    }


def test_projectname_version_explicit():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades pypi::othername >= 3
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('othername >= 3')
    }


def test_projectname_version_nospace():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades othername==5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('othername==5')
    }


def test_projectname_version_space():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades othername <5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('othername <5')
    }


def test_projectname_pkgnamedb():
    parsed = parsing._parse_content(io.StringIO("""
        import bs4   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('beautifulsoup4')
    }


def test_projectname_pkgnamedb_version():
    parsed = parsing._parse_content(io.StringIO("""
        import bs4   # fades >=5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('beautifulsoup4 >=5')
    }


def test_projectname_pkgnamedb_othername_default():
    parsed = parsing._parse_content(io.StringIO("""
        import bs4   # fades othername
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('othername')
    }


def test_projectname_pkgnamedb_version_othername():
    parsed = parsing._parse_content(io.StringIO("""
        import bs4   # fades othername >=5
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('othername >=5')
    }


def test_comma_separated_import():
    parsed = parsing._parse_content(io.StringIO("""
        from foo import bar, baz, qux   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('foo')
    }


def test_other_lines_with_fades_string():
    parsed = parsing._parse_content(io.StringIO("""
        import bar # fades
        print("screen fades to black")
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('bar')
    }


def test_commented_line(logged):
    parsed = parsing._parse_content(io.StringIO("""
        #import foo   # fades
    """))
    assert parsed == {}
    logged.assert_not_warning("Not understood fades")


def test_with_fades_commented_line(logged):
    parsed = parsing._parse_content(io.StringIO("""
        #import foo   # fades
        import bar   # fades
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('bar')
    }
    logged.assert_not_warning("Not understood fades")


def test_with_commented_line(logged):
    parsed = parsing._parse_content(io.StringIO("""
        import bar   # fades
        # a commented line
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('bar')
    }
    logged.assert_not_warning("Not understood fades")


def test_vcs_explicit():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades vcs::superurl
    """))
    assert parsed == {
        REPO_VCS: [parsing.VCSDependency('superurl')]
    }


def test_vcs_implicit():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades   http://www.whatever/project
    """))
    assert parsed == {
        REPO_VCS: [parsing.VCSDependency('http://www.whatever/project')]
    }


def test_mixed():
    parsed = parsing._parse_content(io.StringIO("""
        import foo    # fades vcs::superurl
        import bar    # fades
    """))
    assert parsed == {
        REPO_VCS: [parsing.VCSDependency('superurl')],
        REPO_PYPI: get_reqs('bar'),
    }


def test_fades_and_hashtag_mentioned_in_code():
    """Test the case where a string contains both: fades and hashtag (#)
    but is not an import.
    """
    parsed = parsing._parse_content(io.StringIO("""
      'http://fades.readthedocs.io/en/release-7-0/readme.html#how-to-use-it'
    """))
    assert parsed == {}


def test_fades_and_hashtag_mentioned_in_code_mixed_with_imports():
    parsed = parsing._parse_content(io.StringIO("""import requests  # fades

      'http://fades.readthedocs.io/en/release-7-0/readme.html#how-to-use-it'
    """))
    assert parsed == {
        REPO_PYPI: get_reqs('requests')
    }


def test_fades_user_strange_comment_with_hashtag_ignored():
    parsed = parsing._parse_content(io.StringIO("""
      import foo # fades==2 # Some comment with #hashtash
    """))
    assert parsed == {}
