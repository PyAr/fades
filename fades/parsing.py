# Copyright 2014-2026 Facundo Batista, Nicolás Demarchi
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
import re
from pathlib import Path
from typing import Generator

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    try:
        import tomli as tomllib
    except ModuleNotFoundError:
        tomllib = None  # PEP 723 support degrades gracefully; warned at use site

from packaging.requirements import InvalidRequirement, Requirement
from packaging.version import Version

from fades import FadesError, REPO_PYPI, REPO_VCS
from fades.pkgnamesdb import MODULE_TO_PACKAGE

logger = logging.getLogger(__name__)

# Canonical regular expression to find a PEP 723 metadata block (see
# https://peps.python.org/pep-0723/#reference-implementation).
PEP723_REGEX = re.compile(
    r'(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)+)^# ///$')


class _VCSSpecifier:
    """A simple specifier that works with VCSDependency."""

    def contains(self, other):
        """VCS dependency does not handle versions."""
        return other is None


class VCSDependency:
    """A dependency object for VCS urls (git, bzr, etc.).

    It stores as unique identifier the whole URL; there may be a little
    inefficiency because we may consider as different two urls for same
    project but using different transports, but it's a small price for
    not needing to parse and analyze url parts.
    """

    def __init__(self, url):
        """Init."""
        self.url = self.name = self.project_name = self.version = url
        self.specifier = _VCSSpecifier()

    def __str__(self):
        """Return the URL as this is the interface to get what pip will use."""
        return self.url

    def __repr__(self):
        """Repr."""
        return "<VCSDependency: {!r}>".format(self.url)

    def __eq__(self, other):
        """Tell if one VCSDependency is equal to other."""
        if not isinstance(other, VCSDependency):
            return False
        return self.url == other.url

    def __hash__(self):
        """Pair to __eq__ to make this hashable."""
        return hash(self.url)


class NameVerDependency:
    """A dependency indicated by name and version."""

    def __init__(self, name, version):
        self.name = name
        self.version = Version(version)

    def __eq__(self, other):
        return self.name == other.name and self.version == other.version

    def __hash__(self):
        return hash((self.name, self.version))

    def __lt__(self, other):
        assert not isinstance(self.version, str)
        return (self.name, self.version) < (other.name, other.version)


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
        dependency = Requirement(requirement)
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

        # To match the "safe" name
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
        if "#" in line:
            line = line[:line.index("#")]
        if not line:
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


def _read_lines(filepath: Path) -> Generator[str, None, None]:
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
                    nested_filepath = filepath.parent / nested_filename
                    yield from _read_lines(nested_filepath)
            else:
                yield line


def parse_reqfile(filepath: Path):
    """Parse a requirement file and return the indicated dependencies."""
    if filepath is None:
        return {}
    return _parse_requirement(_read_lines(filepath))


def parse_srcfile(filepath: Path):
    """Parse a source file and return its marked dependencies."""
    if filepath is None:
        return {}
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_content(fh)


def parse_docstring(filepath: Path):
    """Parse a source file and return its dependencies specified into docstrings."""
    if filepath is None:
        return {}
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_docstring(fh)


def _parse_pep723(content):
    """Parse a PEP 723 inline metadata block.

    Return a tuple ``(deps, requires_python)`` where ``deps`` is the usual repo->deps
    mapping and ``requires_python`` is the raw 'requires-python' specifier (or None).
    """
    matches = [m for m in PEP723_REGEX.finditer(content) if m.group('type') == 'script']
    if not matches:
        return {}, None
    if len(matches) > 1:
        # The PEP mandates that tools error when several blocks of the same type exist.
        logger.error("Found %d PEP 723 'script' blocks, but only one is allowed", len(matches))
        raise FadesError("Multiple PEP 723 'script' blocks found")
    logger.debug("Found a PEP 723 'script' metadata block")

    if tomllib is None:
        logger.warning(
            "Found a PEP 723 metadata block but no TOML parser is available; "
            "install the 'tomli' package to enable PEP 723 support in Python <3.11")
        return {}, None

    # Rebuild the TOML content stripping the comment prefix of each line, as per the PEP.
    toml_content = ''.join(
        line[2:] if line.startswith('# ') else line[1:]
        for line in matches[0].group('content').splitlines(keepends=True))
    try:
        metadata = tomllib.loads(toml_content)
    except tomllib.TOMLDecodeError as error:
        logger.error("Invalid TOML in the PEP 723 metadata block: %s", error)
        raise FadesError("Invalid TOML in the PEP 723 metadata block")
    logger.debug("Parsed PEP 723 metadata: %s", metadata)

    deps = {}
    dependencies = metadata.get('dependencies', [])
    if not isinstance(dependencies, list):
        logger.error(
            "PEP 723 'dependencies' must be a list, got %s", type(dependencies).__name__)
        raise FadesError("PEP 723 'dependencies' must be a list")
    if dependencies:
        # PEP 723 dependencies are standard PEP 508 strings (including 'name @ url' direct
        # references that pip understands), so they all go to the PyPI repo.
        try:
            deps[REPO_PYPI] = [Requirement(dep) for dep in dependencies]
        except InvalidRequirement as error:
            logger.error("Invalid dependency in the PEP 723 metadata block: %s", error)
            raise FadesError("Invalid dependency in the PEP 723 metadata block")

    return deps, metadata.get('requires-python')


def parse_pep723(filepath):
    """Parse a source file's PEP 723 metadata block.

    Return a tuple ``(deps, requires_python)``; see ``_parse_pep723``.
    """
    if filepath is None:
        return {}, None
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_pep723(fh.read())
