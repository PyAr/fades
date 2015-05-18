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

"""Script parsing to get needed dependencies."""

import logging

from pkg_resources import parse_requirements

from fades import REPO_PYPI
from fades.pkgnamesdb import PKG_NAMES_DB

logger = logging.getLogger(__name__)


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

        # get module
        import_tokens = import_part.split()
        if import_tokens[0] == 'import':
            module_path = import_tokens[1]
        elif import_tokens[0] == 'from' and import_tokens[2] == 'import':
            module_path = import_tokens[1]
        else:
            logger.warning("Not understood import info: %s", import_tokens)
            continue
        module = module_path.split(".")[0]
        # If fades know the real name of the pkg. Replace it!
        if module in PKG_NAMES_DB:
            module = PKG_NAMES_DB[module]
        # To match the "safe" name that pkg_resources creates:
        module = module.replace('_', '-')

        # get the fades info
        if fades_part.startswith("fades.pypi"):
            repo = REPO_PYPI
            marked = fades_part[10:].strip()
        elif fades_part.startswith("fades") and (len(fades_part) == 5 or fades_part[5] in "<>=! "):
            # starts with 'fades' only, and continues with a space or a
            # comparison, not a dot, neither other word stuck together
            repo = REPO_PYPI
            marked = fades_part[5:].strip()
        else:
            logger.warning("Not understood fades info: %r", fades_part)
            continue

        if not marked:
            # nothing after the pypi token
            requirement = module
        elif marked[0] in "<>=!":
            # the rest is just the version
            requirement = module + ' ' + marked
        else:
            # the rest involves not only a version, but also the project name
            requirement = marked

        # record the dependency
        dependency = list(parse_requirements(requirement))[0]
        deps.setdefault(repo, []).append(dependency)

    return deps


def _parse_requirement(iterable):
    """Actually parse the requirements, from file or manually specified."""
    deps = {}
    for line in iterable:
        line = line.strip()
        if not line or line[0] == '#':
            continue

        if "::" in line:
            try:
                repo_raw, requirement = line.split("::")
                repo = {'pypi': REPO_PYPI}[repo_raw]
            except:
                logger.warning("Not understood dependency: %r", line)
                continue
        else:
            repo = REPO_PYPI
            requirement = line

        dependency = list(parse_requirements(requirement))[0]
        deps.setdefault(repo, []).append(dependency)

    return deps


def parse_manual(dependencies):
    """Parse a string and return specified dependencies."""
    if dependencies is None:
        return {}
    return _parse_requirement(dependencies)


def parse_reqfile(filepath):
    """Parse a requirement file and return the indicated dependencies."""
    if filepath is None:
        return {}
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_requirement(fh)


def parse_srcfile(filepath):
    """Parse a source file and return its marked dependencies."""
    if filepath is None:
        return {}
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_content(fh)
