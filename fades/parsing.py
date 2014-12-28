# Copyright 2014 Facundo Batista, Nicolás Demarchi
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

import enum
import logging


logger = logging.getLogger(__name__)

Repo = enum.Enum('Repo', 'pypi')


def _parse_content(fh):
    """Parse the content of a script to find marked dependencies."""
    content = iter(fh)
    deps = {}
    for repo in Repo:
        deps[repo] = {}

    for line in content:
        # quickly discard most of the lines
        if 'fades' not in line:
            continue

        # assure that it's a well commented line and no other stuff
        line = line.strip()
        import_part, fades_part = line.rsplit("#", 1)
        fades_part = fades_part.strip()
        if not fades_part.startswith("fades."):
            continue

        if not import_part:
            # the fades comment was done at the beginning of the line,
            # which means that the import info is in the next one
            import_part = next(content).strip()

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

        # get the fades info
        if fades_part.startswith("fades.pypi"):
            repo = Repo.pypi
            parts = fades_part.split(maxsplit=1)
            version_info = None if len(parts) == 1 else parts[1]
        else:
            logger.warning("Not understood fades info: %r", fades_part)
            continue

        # record the dependency

        deps[repo][module] = {'version': version_info}

    return deps


def parse_file(filepath):
    """Parse a file and return its marked dependencies."""
    with open(filepath, 'rt', encoding='utf8') as fh:
        return _parse_content(fh)
