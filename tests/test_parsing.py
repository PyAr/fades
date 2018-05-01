# Copyright 2014-2016 Facundo Batista, Nicolás Demarchi
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

from fades import parsing, REPO_PYPI, REPO_VCS


def get_req(text):
    """Transform a text requirement into the pkg_resources object."""
    return list(parse_requirements(text))[0]


class FileParsingTestCase(unittest.TestCase):
    """Check the imports parsing."""

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

    def test_simple_default(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time
            import foo    # fades
        """))
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_double(self):
        parsed = parsing._parse_content(io.StringIO("""
            import time  # fades
            import foo    # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('time'), get_req('foo')]
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
            import foo    # fades !=3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo !=3.5')]
        })

    def test_version_same_no_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades==3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==3.5')]
        })

    def test_version_same_two_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades  ==  3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==  3.5')]
        })

    def test_version_same_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades  == 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades== 3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo == 3.5')]
        })

    def test_version_same_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades==  3.5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo ==  3.5')]
        })

    def test_version_greater(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades > 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_no_space(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades>2
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
            import foo    # fades  >  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >  2')]
        })

    def test_version_greater_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades> 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades>  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades> 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_greater_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades>  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_version_same_or_greater(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades >= 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_no_spaces(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades>=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_one_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades >=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >=2')]
        })

    def test_version_same_or_greater_two_space_before(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades  >=2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >=2')]
        })

    def test_version_same_or_greater_one_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades>= 2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_version_same_or_greater_two_space_after(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades>=  2
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo >= 2')]
        })

    def test_continuation_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar
            # fades > 2
            import foo
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo > 2')]
        })

    def test_from_import_simple(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import bar   # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_import(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo.bar   # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_from_import_complex(self):
        parsed = parsing._parse_content(io.StringIO("""
            from baz.foo import bar   # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('baz')]
        })

    def test_allow_other_comments(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import *   # NOQA   # fades
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
            from foo bar import :(   # fades
        """))
        self.assertLoggedDebug("Not understood import info",
                               "['from', 'foo', 'bar', 'import', ':(']")
        self.assertDictEqual(parsed, {})

    def test_strange_fadesinfo(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo   # fades  broken::whatever
        """))
        self.assertLoggedWarning("Not understood fades repository", "broken")
        self.assertDictEqual(parsed, {})

    def test_strange_fadesinfo2(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo   # fadesbroken
        """))
        self.assertLoggedWarning("Not understood fades info", "fadesbroken")
        self.assertDictEqual(parsed, {})

    def test_projectname_noversion_implicit(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades othername
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername')]
        })

    def test_projectname_noversion_explicit(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades pypi::othername
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername')]
        })

    def test_projectname_version_explicit(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades pypi::othername >= 3
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername >= 3')]
        })

    def test_projectname_version_nospace(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades othername==5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername==5')]
        })

    def test_projectname_version_space(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades othername <5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername <5')]
        })

    def test_projectname_pkgnamedb(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bs4   # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('beautifulsoup4')]
        })

    def test_projectname_pkgnamedb_version(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bs4   # fades >=5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('beautifulsoup4 >=5')]
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
            import bs4   # fades othername >=5
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('othername >=5')]
        })

    def test_comma_separated_import(self):
        parsed = parsing._parse_content(io.StringIO("""
            from foo import bar, baz, qux   # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')]
        })

    def test_other_lines_with_fades_string(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar # fades
            print("screen fades to black")
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('bar')]
        })

    def test_commented_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            #import foo   # fades
        """))
        self.assertDictEqual(parsed, {})
        self.assertNotLoggedWarning("Not understood fades")

    def test_with_fades_commented_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            #import foo   # fades
            import bar   # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('bar')]
        })
        self.assertNotLoggedWarning("Not understood fades")

    def test_with_commented_line(self):
        parsed = parsing._parse_content(io.StringIO("""
            import bar   # fades
            # a commented line
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('bar')]
        })
        self.assertNotLoggedWarning("Not understood fades")

    def test_vcs_explicit(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades vcs::superurl
        """))
        self.assertDictEqual(parsed, {
            REPO_VCS: [parsing.VCSDependency('superurl')]
        })

    def test_vcs_implicit(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades   http://www.whatever/project
        """))
        self.assertDictEqual(parsed, {
            REPO_VCS: [parsing.VCSDependency('http://www.whatever/project')]
        })

    def test_mixed(self):
        parsed = parsing._parse_content(io.StringIO("""
            import foo    # fades vcs::superurl
            import bar    # fades
        """))
        self.assertDictEqual(parsed, {
            REPO_VCS: [parsing.VCSDependency('superurl')],
            REPO_PYPI: [get_req('bar')],
        })

    def test_fades_and_hashtag_mentioned_in_code(self):
        """Test the case where a string contains both: fades and hashtag (#)
        but is not an import.
        """
        parsed = parsing._parse_content(io.StringIO("""
          'http://fades.readthedocs.io/en/release-7-0/readme.html#how-to-use-it'
        """))
        self.assertDictEqual(parsed, {})

    def test_fades_and_hashtag_mentioned_in_code_mixed_with_imports(self):
        parsed = parsing._parse_content(io.StringIO("""import requests  # fades

          'http://fades.readthedocs.io/en/release-7-0/readme.html#how-to-use-it'
        """))
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('requests')]
        })

    def test_fades_user_strange_comment_with_hashtag_ignored(self):
        parsed = parsing._parse_content(io.StringIO("""
          import foo # fades==2 # Some comment with #hashtash
        """))  # noqa
        self.assertDictEqual(parsed, {})


class ManualParsingTestCase(unittest.TestCase):
    """Check the manual parsing."""

    def test_none(self):
        parsed = parsing.parse_manual(None)
        self.assertDictEqual(parsed, {})

    def test_nothing(self):
        parsed = parsing.parse_manual([])
        self.assertDictEqual(parsed, {})

    def test_simple(self):
        parsed = parsing.parse_manual(["pypi::foo"])
        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})

    def test_simple_default_pypi(self):
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

    def test_vcs_simple(self):
        url = "git+git://server.com/etc"
        parsed = parsing.parse_manual(["vcs::" + url])
        self.assertDictEqual(parsed, {REPO_VCS: [parsing.VCSDependency(url)]})

    def test_vcs_simple_default(self):
        url = "git+git://server.com/etc"
        parsed = parsing.parse_manual([url])
        self.assertDictEqual(parsed, {REPO_VCS: [parsing.VCSDependency(url)]})

    def test_mixed(self):
        parsed = parsing.parse_manual(["pypi::foo", "vcs::git+git://server.com/etc"])
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo')],
            REPO_VCS: [parsing.VCSDependency("git+git://server.com/etc")],
        })


class ReqsParsingTestCase(unittest.TestCase):
    """Check the requirements parsing."""

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
        self.assertLoggedWarning("Not understood fades repository", "unknown")
        self.assertDictEqual(parsed, {})

    def test_vcs_simple(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            vcs::strangeurl
        """))
        self.assertDictEqual(parsed, {REPO_VCS: [parsing.VCSDependency("strangeurl")]})

    def test_vcs_simple_default(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            bzr+http://server/bleh
        """))
        self.assertDictEqual(parsed, {REPO_VCS: [parsing.VCSDependency("bzr+http://server/bleh")]})

    def test_mixed(self):
        parsed = parsing._parse_requirement(io.StringIO("""
            vcs::strangeurl
            pypi::foo
        """))
        self.assertDictEqual(parsed, {
            REPO_VCS: [parsing.VCSDependency("strangeurl")],
            REPO_PYPI: [get_req('foo')],
        })


class DocstringParsingTestCase(unittest.TestCase):
    """Check the docstring parsing."""

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

    def test_mixed_backends(self):
        with open("tests/test_files/req_mixed_backends.py") as f:
            parsed = parsing._parse_docstring(f)
        # Only module requirements was found
        self.assertDictEqual(parsed, {
            REPO_PYPI: [get_req('foo'), get_req('bar')],
            REPO_VCS: [parsing.VCSDependency('git+http://whatever'),
                       parsing.VCSDependency('anotherurl')],
        })


class VCSDependencyTestCase(unittest.TestCase):
    """Check the VCSDependency."""

    def test_string_representation(self):
        """This is particularly tested because it's the interface to be installed."""
        dep = parsing.VCSDependency("testurl")
        self.assertEqual(str(dep), "testurl")

    def test_contains(self):
        """This is particularly tested because it's how fulfilling is tested."""
        dep1 = parsing.VCSDependency("testurl")
        dep2 = parsing.VCSDependency("testurl")
        dep3 = parsing.VCSDependency("otherurl")
        self.assertTrue(dep1 in dep2)
        self.assertFalse(dep1 in dep3)

    def test_equality(self):
        dep1 = parsing.VCSDependency("testurl")
        dep2 = parsing.VCSDependency("testurl")
        dep3 = parsing.VCSDependency("otherurl")
        self.assertTrue(dep1 == dep2)
        self.assertFalse(dep1 == dep3)
        self.assertFalse(dep1 != dep2)
        self.assertTrue(dep1 != dep3)
        self.assertFalse(dep1 == 123)
        self.assertFalse(dep1 == "testurl")
