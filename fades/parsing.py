# Copyright 2014-2019 Facundo Batista, Nicolás Demarchi
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

"""Script parsing to get needed dependencies."""

import logging
import os
import re

from pkg_resources import parse_requirements

from fades import REPO_PYPI, REPO_VCS
from fades.pkgnamesdb import MODULE_TO_PACKAGE

logger = logging.getLogger(__name__)


class VCSDependency:
    """A dependency object for VCS urls (git, bzr, etc.).

    It stores as unique identifier the whole URL; there may be a little
    inefficiency because we may consider as different two urls for same
    project but using different transports, but it's a small price for
    not needing to parse and analyze url parts.
    """

    def __init__(self, url):
        """Init."""
        self.url = url

    def __str__(self):
        """Return the URL as this is the interface to get what pip will use."""
        return self.url

    def __repr__(self):
        """Repr."""
        return "<VCSDependency: {!r}>".format(self.url)

    def __contains__(self, other):
        """Tell if requirement is satisfied."""
        return other.url == self.url

    def __eq__(self, other):
        """Tell if one VCSDependency is equal to other."""
        if not isinstance(other, VCSDependency):
            return False
        return self.url == other.url

    def __hash__(self):
        """Pair to __eq__ to make this hashable."""
        return hash(self.url)


def parse_fade_requirement(text):
    """Return a requirement and repo from the given text, already parsed and converted."""
    text = text.strip()

    if "::" in text:
        repo_raw, requirement = text.split("::", 1)
        try:
            repo = {'pypi': REPO_PYPI, 'vcs': REPO_VCS}[repo_raw]
        except KeyError:
            logger.warning("Not understood fades repository: %r", repo_raw)
            return
    else:
        if ":" in text and "/" in text:
            repo = REPO_VCS
        else:
            repo = REPO_PYPI
        requirement = text

    if repo == REPO_VCS:
        dependency = VCSDependency(requirement)
    else:
        dependency = list(parse_requirements(requirement))[0]
    return repo, dependency


def _parse_content(fh):
    """Parse the content of a script to find marked dependencies."""
    content = iter(fh)
    deps = {}

    for line in content:
        # quickly discard most of the lines
        if 'fades' not in line:
            continue

        # discard other string with 'fades' that isn't a comment
        if '#' not in line:
            continue

        # assure that it's a well commented line and no other stuff
        line = line.strip()
        index_of_last_fades = line.rfind('fades')
        index_of_first_hash = line.index('#')

        # discard when fades does not appear after #
        if index_of_first_hash > index_of_last_fades:
            continue

        import_part, fades_part = line.rsplit("#", 1)

        # discard other comments in the same line that aren't for fades
        if "fades" not in fades_part:
            import_part, fades_part = import_part.rsplit("#", 1)

        fades_part = fades_part.strip()
        if not fades_part.startswith("fades"):
            continue

        if not import_part:
            # the fades comment was done at the beginning of the line,
            # which means that the import info is in the next one
            import_part = next(content).strip()

        if import_part.startswith('#'):
            continue

        # Get the module.
        import_tokens = import_part.split()
        if import_tokens[0] == 'import':
            module_path = import_tokens[1]
        elif import_tokens[0] == 'from' and import_tokens[2] == 'import':
            module_path = import_tokens[1]
        else:
            logger.debug("Not understood import info: %s", import_tokens)
            continue
        module = module_path.split(".")[0]

        # The package has the same name (most of the times! if fades knows the conversion, use it).
        if module in MODULE_TO_PACKAGE:
            package = MODULE_TO_PACKAGE[module]
        else:
            package = module

        # To match the "safe" name that pkg_resources creates:
        package = package.replace('_', '-')

        # get the fades info after 'fades' mark, if any
        if len(fades_part) == 5 or fades_part[5:].strip()[0] in "<>=!":
            # just the 'fades' mark, and maybe a version specification, the requirement is what
            # was imported (maybe with that version comparison)
            requirement = package + fades_part[5:]
        elif fades_part[5] != " ":
            # starts with fades but it's part of a longer weird word
            logger.warning("Not understood fades info: %r", fades_part)
            continue
        else:
            # more complex stuff, to be parsed as a normal requirement
            requirement = fades_part[5:]

        # parse and convert the requirement
        parsed_req = parse_fade_requirement(requirement)
        if parsed_req is None:
            continue
        repo, dependency = parsed_req
        deps.setdefault(repo, []).append(dependency)

    return deps


def _parse_docstring(fh):
    """Parse the docstrings of a script to find marked dependencies."""
    find_fades = re.compile(r'\b(fades)\b:').search

    for line in fh:
        if line.startswith("'"):
            quote = "'"
            break
        if line.startswith('"'):
            quote = '"'
            break
    else:
        return {}

    if line[1] == quote:
        # comment start with triple quotes
        endquote = quote * 3
    else:
        endquote = quote

    if endquote in line[len(endquote):]:
        docstring_lines = [line[:line.index(endquote)]]
    else:
        docstring_lines = [line]
        for line in fh:
            if endquote in line:
                docstring_lines.append(line[:line.index(endquote)])
                break
            docstring_lines.append(line)

    docstring_lines = iter(docstring_lines)
    for doc_line in docstring_lines:
        if find_fades(doc_line):
            break
    else:
        return {}

    return _parse_requirement(list(docstring_lines))


def _parse_requirement(iterable):
    """Actually parse the requirements, from file or manually specified."""
    deps = {}
    for line in iterable:
        line = line.strip()
        if not line or line[0] == '#':
            continue

        parsed_req = parse_fade_requirement(line)
        if parsed_req is None:
            continue
        repo, dependency = parsed_req
        deps.setdefault(repo, []).append(dependency)

    return deps


def parse_manual(dependencies):
    """Parse an iterable and return specified dependencies."""
    if dependencies is None:
        return {}
    return _parse_requirement(dependencies)


def _read_lines(filepath):
    """Read a req file to a list to support nested requirement files."""
    with open(filepath, 'rt', encoding='utf8') as fh:
        for line in fh:
            line = line.strip()
            if line.startswith("-r"):
                logger.debug("Reading deps from nested requirement file: %s", line)
                try:
                    nested_filename = line.split()[1]
                except IndexError:
                    logger.warning(
                        "Invalid format to indicate a nested requirements file: '%r'", line)
                else:
                    nested_filepath = os.path.join(
                        os.path.dirname(filepath), nested_filename)
                    yield from _read_lines(nested_filepath)
            else:
                yield line


def parse_reqfile(filepath):
    """Parse a requirement file and return the indicated dependencies."""
    if filepath is None:
        return {}
    return _parse_requirement(_read_lines(filepath))


def parse_srcfile(filepath):
    """Parse a source file and return its marked dependencies."""
    if filepath is None:
        return {}
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_content(fh)


def parse_docstring(filepath):
    """Parse a source file and return its dependencies specified into docstrings."""
    if filepath is None:
        return {}
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_docstring(fh)
