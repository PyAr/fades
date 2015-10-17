# Copyright 2014, 2015 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

"""Tests for the parsing of module imports."""

import io
import unittest

import logassert

from pkg_resources import parse_requirements

from fades import parsing, REPO_PYPI


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))[0]


class PyPIFileParsingTestCase(unittest.TestCase):
    """Check the imports parsing for PyPI."""

    def setUp(self):
        logassert.setup(self, 'fades.parsing')

    def test_nocomment(self):
        # note that we're testing the import at the beginning of the line, and
        # in also indented
        parsed = parsing._parse_content(io.StringIO("""import time
            import time
            from time import foo
        """))
        self.assertDictEqual(parsed, {})

    def test_simple(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time
            import foo    # fades.pypi
        """))
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_simple_default(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time
            import foo    # fades
        """))
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_double(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time  # fades.pypi
            import foo    # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('time'), get_req('foo')]
        })

    def test_version_same(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_default(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_different(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi !=3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo !=3.5')]
        })

    def test_version_same_no_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi==3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==3.5')]
        })

    def test_version_same_two_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  ==  3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==  3.5')]
        })

    def test_version_same_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi== 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi==  3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==  3.5')]
        })

    def test_version_greater(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi > 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_no_space(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >2')]
        })

    def test_version_greater_no_space_default(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades>2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >2')]
        })

    def test_version_greater_two_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  >  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >  2')]
        })

    def test_version_greater_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi> 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi> 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_same_or_greater(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi >= 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_no_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi >=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >=2')]
        })

    def test_version_same_or_greater_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi  >=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >=2')]
        })

    def test_version_same_or_greater_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>= 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi>=  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_continuation_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar
            # fades.pypi > 2
            import foo
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_from_import_simple(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import bar   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_import(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo.bar   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_from_import_complex(self):
        parsed = parsing._parse_content(io.StringIO("""
            from baz.foo import bar   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('baz')]
        })

    def test_allow_other_comments(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import *   # NOQA   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_allow_other_comments_reverse(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import * # fades.pypi # NOQA
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_allow_other_comments_reverse_default(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import * # fades # NOQA
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_strange_import(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo bar import :(   # fades.pypi
        """))
        self.assertLoggedWarning("Not understood import info",
                                 "['from', 'foo', 'bar', 'import', ':(']")
        self.assertDictEqual(parsed, {})

    def test_strange_fadesinfo(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo   # fades.broken
        """))
        self.assertLoggedWarning("Not understood fades info", "fades.broken")
        self.assertDictEqual(parsed, {})

    def test_strange_fadesinfo2(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo   # fadesbroken
        """))
        self.assertLoggedWarning("Not understood fades info", "fadesbroken")
        self.assertDictEqual(parsed, {})

    def test_projectname_noversion(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi othername
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername')]
        })

    def test_projectname_version_nospace(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi othername==5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername==5')]
        })

    def test_projectname_version_space(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades.pypi othername <5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername <5')]
        })

    def test_projectname_pkgnamedb(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bs4   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('beautifulsoup4')]
        })

    def test_projectname_pkgnamedb_version(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bs4   # fades.pypi >=5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('beautifulsoup4 >=5')]
        })

    def test_projectname_pkgnamedb_othername(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bs4   # fades.pypi othername
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername')]
        })

    def test_projectname_pkgnamedb_othername_default(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bs4   # fades othername
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername')]
        })

    def test_projectname_pkgnamedb_version_othername(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bs4   # fades.pypi othername >=5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername >=5')]
        })

    def test_comma_separated_import(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import bar, baz, qux   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_other_lines_with_fades_string(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar # fades.pypi
            print("screen fades to black")
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('bar')]
        })

    def test_commented_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            #import foo   # fades.pypi
        """))
        self.assertDictEqual(parsed, {})
        self.assertNotLoggedWarning("Not understood fades")

    def test_with_fades_commented_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            #import foo   # fades.pypi
            import bar   # fades.pypi
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('bar')]
        })
        self.assertNotLoggedWarning("Not understood fades")

    def test_with_commented_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar   # fades.pypi
            # a commented line
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('bar')]
        })
        self.assertNotLoggedWarning("Not understood fades")


class PyPIManualParsingTestCase(unittest.TestCase):
    """Check the manual parsing for PyPI."""

    def test_none(self):
        parsed = parsing.parse_manual(None)
        self.assertDictEqual(parsed, {})

    def test_nothing(self):
        parsed = parsing.parse_manual([])
        self.assertDictEqual(parsed, {})

    def test_simple(self):
        parsed = parsing.parse_manual(["pypi::foo"])
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_simple_default(self):
        parsed = parsing.parse_manual(["foo"])
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_double(self):
        parsed = parsing.parse_manual(["pypi::foo", "pypi::bar"])
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo'), get_req('bar')]
        })

    def test_version(self):
        parsed = parsing.parse_manual(["pypi::foo == 3.5"])
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]

        })

    def test_version_default(self):
        parsed = parsing.parse_manual(["foo == 3.5"])
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]

        })


class PyPIReqsParsingTestCase(unittest.TestCase):
    """Check the requirements parsing for PyPI."""

    def setUp(self):
        logassert.setup(self, 'fades.parsing')

    def test_empty(self):
        parsed = parsing._parse_requirement(io.StringIO("""

        """))
        self.assertDictEqual(parsed, {})

    def test_simple(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            pypi::foo
        """))
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_simple_default(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            foo
        """))
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_double(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            pypi::time
            foo
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('time'), get_req('foo')]
        })

    def test_version_same(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            pypi::foo == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_default(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            foo == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_different(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            foo  !=3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo !=3.5')]
        })

    def test_version_same_no_spaces(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            foo==3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==3.5')]
        })

    def test_version_greater_two_spaces(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            foo   >  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >  2')]
        })

    def test_version_same_or_greater(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            foo   >=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_comments(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            pypi::foo   # some text
            # other text
            bar
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo'), get_req('bar')]
        })

    def test_strange_repo(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            unknown::foo
        """))
        self.assertLoggedWarning("Not understood dependency", "unknown::foo")
        self.assertDictEqual(parsed, {})


class PyPIDocstringParsingTestCase(unittest.TestCase):
    """Check the requirements parsing for PyPI."""

    def setUp(self):
        logassert.setup(self, 'fades.parsing')

    def test_empty(self):
        parsed = parsing._parse_docstring(io.StringIO("""

        """))
        self.assertDictEqual(parsed, {})

    def test_only_comment(self):
        with open("tests/test_files/no_req.py") as f:
            parsed = parsing._parse_docstring(f)
        self.assertDictEqual(parsed, {})

    def test_req_in_module_docstring_triple_doublequoute(self):
        with open("tests/test_files/req_module.py") as f:
            parsed = parsing._parse_docstring(f)
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo'), get_req('bar')]
        })

    def test_req_in_module_docstring_triple_singlequote(self):
        with open("tests/test_files/req_module_2.py") as f:
            parsed = parsing._parse_docstring(f)
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo'), get_req('bar')]
        })

    def test_req_in_module_docstring_one_doublequote(self):
        with open("tests/test_files/req_module_3.py") as f:
            parsed = parsing._parse_docstring(f)
        self.assertDictEqual(parsed, {})

    def test_req_in_class_docstring(self):
        with open("tests/test_files/req_class.py") as f:
            parsed = parsing._parse_docstring(f)
        # no requirements found
        self.assertDictEqual(parsed, {})

    def test_req_in_def_docstring(self):
        with open("tests/test_files/req_def.py") as f:
            parsed = parsing._parse_docstring(f)
        # no requirements found
        self.assertDictEqual(parsed, {})

    def test_req_in_multi_docstring(self):
        with open("tests/test_files/req_all.py") as f:
            parsed = parsing._parse_docstring(f)
        # Only module requirements was found
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo==1.4')]
        })

    def test_fades_word_as_part_of_text(self):
        with open("tests/test_files/fades_as_part_of_other_word.py") as f:
            parsed = parsing._parse_docstring(f)
        self.assertDictEqual(parsed, {})
