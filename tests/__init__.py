# Copyright 2017-2024 Facundo Batista, Nicolás Demarchi
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

"""Common code for the tests."""

import os
from tempfile import mkstemp

from packaging.requirements import Requirement


def get_tempfile(testcase):
    """Return the name of a temp file that will be removed when the test finishes."""
    # create the file and close its descriptor
    descriptor, tempfile = mkstemp(prefix="test-temp-file")
    os.close(descriptor)

    def clean():
        """Clean the file from disk, if still there."""
        if os.path.exists(tempfile):
            os.remove(tempfile)
    testcase.addCleanup(clean)

    return tempfile


def create_tempfile(testcase, lines):
    tempfile = get_tempfile(testcase)

    with open(tempfile, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write(line + '\n')

    return tempfile


def get_python_filepaths(roots):
    """Helper to retrieve paths of Python files."""
    python_paths = []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".py"):
                    python_paths.append(os.path.join(dirpath, filename))
    return python_paths


def get_reqs(*items):
    """Transform text requirements into Requirement objects."""
    return [Requirement(item) for item in items]
