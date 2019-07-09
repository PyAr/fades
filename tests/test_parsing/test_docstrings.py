"""Check the docstring parsing."""
import io

from fades import parsing, REPO_PYPI, REPO_VCS

from tests import get_reqs


def test_empty():
    parsed = parsing._parse_docstring(
        io.StringIO("""

        """)
    )
    assert parsed == {}


def test_only_comment():
    with open("tests/test_files/no_req.py") as f:
        parsed = parsing._parse_docstring(f)
    assert parsed == {}


def test_req_in_module_docstring_triple_doublequoute():
    with open("tests/test_files/req_module.py") as f:
        parsed = parsing._parse_docstring(f)
    assert parsed == {REPO_PYPI: get_reqs("foo", "bar")}


def test_req_in_module_docstring_triple_singlequote():
    with open("tests/test_files/req_module_2.py") as f:
        parsed = parsing._parse_docstring(f)
    assert parsed == {REPO_PYPI: get_reqs("foo", "bar")}


def test_req_in_module_docstring_one_doublequote():
    with open("tests/test_files/req_module_3.py") as f:
        parsed = parsing._parse_docstring(f)
    assert parsed == {}


def test_req_in_class_docstring():
    with open("tests/test_files/req_class.py") as f:
        parsed = parsing._parse_docstring(f)
    # no requirements found
    assert parsed == {}


def test_req_in_def_docstring():
    with open("tests/test_files/req_def.py") as f:
        parsed = parsing._parse_docstring(f)
    # no requirements found
    assert parsed == {}


def test_req_in_multi_docstring():
    with open("tests/test_files/req_all.py") as f:
        parsed = parsing._parse_docstring(f)
    # Only module requirements was found
    assert parsed == {REPO_PYPI: get_reqs("foo==1.4")}


def test_fades_word_as_part_of_text():
    with open("tests/test_files/fades_as_part_of_other_word.py") as f:
        parsed = parsing._parse_docstring(f)
    assert parsed == {}


def test_mixed_backends():
    with open("tests/test_files/req_mixed_backends.py") as f:
        parsed = parsing._parse_docstring(f)
    # Only module requirements was found
    assert parsed == {
        REPO_PYPI: get_reqs("foo", "bar"),
        REPO_VCS: [
            parsing.VCSDependency("git+http://whatever"),
            parsing.VCSDependency("anotherurl"),
        ],
    }
