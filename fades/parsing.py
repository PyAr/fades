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

import functools
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

# Canonical regular expression to find a '# /// script' metadata block, as defined by
# PEP 723 (see https://peps.python.org/pep-0723/#reference-implementation).
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


def _parse_dependency_list(dependencies, context):
    """Convert a list of dependency strings (PEP 508) to the usual repo->deps structure.

    The dependencies are standard requirement strings; the ones pointing to a URL
    (e.g. 'foo @ git+https://...' or 'foo @ file:///some/path') are not from PyPI, and are
    handled like any other VCS dependency (pip understands them as they are).

    ``context`` describes where the dependencies come from; it's used in error messages.
    """
    if not isinstance(dependencies, list):
        logger.error(
            "The 'dependencies' field in %s must be a list, got %s",
            context, type(dependencies).__name__)
        raise FadesError("The 'dependencies' field must be a list")

    deps = {}
    for text in dependencies:
        try:
            requirement = Requirement(text)
        except (InvalidRequirement, TypeError) as error:
            logger.error("Invalid dependency %r in %s: %s", text, context, error)
            raise FadesError("Invalid dependency found")
        if requirement.url:
            deps.setdefault(REPO_VCS, []).append(VCSDependency(text.strip()))
        else:
            deps.setdefault(REPO_PYPI, []).append(requirement)

    return deps


def _parse_pep723(content):
    """Parse the '# /// script' metadata block of a script, if any.

    This block (defined in PEP 723, and also understood by tools like pipx, pip-run and uv)
    is a group of comment lines holding TOML content, e.g.:

        # /// script
        # requires-python = ">=3.11"
        # dependencies = ["requests<3", "rich"]
        # ///

    Return a tuple ``(deps, python_toml)`` where ``deps`` is the usual repo->deps mapping and
    ``python_toml`` is the raw Python version specifier the script declares it needs (its
    'requires-python' field), or None.
    """
    matches = [m for m in PEP723_REGEX.finditer(content) if m.group('type') == 'script']
    if not matches:
        return {}, None
    if len(matches) > 1:
        # the PEP mandates that tools error when several blocks of the same type exist
        logger.error(
            "Found %d '# /// script' metadata blocks in the script, but only one is allowed",
            len(matches))
        raise FadesError("Multiple '# /// script' metadata blocks found")
    logger.debug("Found a '# /// script' metadata block in the script")

    if tomllib is None:
        logger.warning(
            "Found a '# /// script' metadata block in the script, but it can't be read "
            "because no TOML parser is available; install the 'tomli' package to support "
            "it in Python <3.11")
        return {}, None

    # rebuild the TOML content stripping the comment prefix of each line, as per the PEP
    toml_content = ''.join(
        line[2:] if line.startswith('# ') else line[1:]
        for line in matches[0].group('content').splitlines(keepends=True))
    try:
        metadata = tomllib.loads(toml_content)
    except tomllib.TOMLDecodeError as error:
        logger.error("Invalid TOML in the script's '# /// script' metadata block: %s", error)
        raise FadesError("Invalid TOML in the '# /// script' metadata block")
    logger.debug("Parsed '# /// script' metadata: %s", metadata)

    dependencies = metadata.get('dependencies', [])
    deps = _parse_dependency_list(dependencies, "the script's '# /// script' metadata block")

    return deps, metadata.get('requires-python')


@functools.lru_cache(maxsize=None)
def parse_pep723(filepath):
    """Parse the '# /// script' metadata block of a source file.

    Return a tuple ``(deps, python_toml)``; see ``_parse_pep723``.

    The result is cached because the file is analyzed twice (to get the dependencies, and
    to get the Python version it needs); callers must not modify the returned values.
    """
    if filepath is None:
        return {}, None
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_pep723(fh.read())


def parse_pyproject(filepath):
    """Parse a pyproject.toml and return the dependencies declared by its [project] table.

    Only the standard PEP 621 'dependencies' list is considered: neither
    'optional-dependencies' nor '[build-system].requires' are taken, as they are not the
    runtime dependencies of what fades will run; a [project] table that declares no
    dependencies simply produces none.

    Raise FadesError if the content is not valid TOML, there is no [project] table, or
    any dependency is invalid.
    """
    if tomllib is None:
        logger.warning(
            "The dependencies of %r can't be read because no TOML parser is available; "
            "install the 'tomli' package to support it in Python <3.11", filepath)
        return {}

    with open(filepath, 'rb') as fh:
        try:
            metadata = tomllib.load(fh)
        except tomllib.TOMLDecodeError as error:
            logger.error("Invalid TOML in %r: %s", filepath, error)
            raise FadesError("Invalid TOML in pyproject.toml")

    project = metadata.get('project')
    if not isinstance(project, dict):
        logger.error("No [project] table found in %r", filepath)
        raise FadesError("No [project] table in pyproject.toml")

    dependencies = project.get('dependencies', [])
    return _parse_dependency_list(dependencies, "the [project] table of {!r}".format(filepath))


def parse_deps_from(filepath):
    """Parse a file indicated with --deps-from, guessing its format from the file name.

    The supported formats are:

    - ``.txt``: a requirements file, parsed exactly like the ones from -r/--requirement
    - ``.py``: a Python script, from which dependencies are taken the same way as when
      it's the program being run: its '# fades' comments, its docstring, and its
      '# /// script' metadata block (PEP 723)
    - ``pyproject.toml``: a PEP 621 project file, from which [project] dependencies
      are taken

    Return a tuple ``(deps, python_toml)`` where ``deps`` is the usual repo->deps mapping
    and ``python_toml`` is the Python version the file declares it needs (only a .py
    file, through its PEP 723 metadata block, may declare it), or None.

    Raise FadesError if the file format is not a supported one.
    """
    filepath = Path(filepath)

    if filepath.name == 'pyproject.toml':
        return parse_pyproject(filepath), None

    suffix = filepath.suffix.lower()
    if suffix == '.txt':
        return parse_reqfile(filepath), None

    if suffix == '.py':
        srcfile_deps = parse_srcfile(filepath)
        docstring_deps = parse_docstring(filepath)
        pep723_deps, python_toml = parse_pep723(filepath)
        deps = {}
        for dep in (srcfile_deps, docstring_deps, pep723_deps):
            for repo, info in dep.items():
                deps.setdefault(repo, set()).update(info)
        return deps, python_toml

    logger.error(
        "Unsupported file to read dependencies from %r: it must be a .txt requirements "
        "file, a .py script, or a pyproject.toml", filepath)
    raise FadesError("Unsupported file to read dependencies from: {!r}".format(filepath))


def merge_requires_python(specifiers):
    """Combine several 'requires-python' specifiers into a single one: their intersection.

    None or empty items are ignored; return None if nothing remains, meaning no Python
    version restriction at all.
    """
    cleaned = [spec.strip() for spec in specifiers if spec]
    if not cleaned:
        return None
    return ', '.join(cleaned)
