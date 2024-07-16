# Copyright 2024 Facundo Batista, Nicolás Demarchi
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

"""Helper to run integration tests.

This is not part of the regular test suite, but a test that is used in a very specific
way from the integration tests defined in the Github CI infrastructure.
"""

import sys


def test_assert_python_version(pytestconfig):
    expected = pytestconfig.getoption("integtest_pyversion")
    vi = sys.version_info
    current = f"{vi.major}.{vi.minor}"
    assert current == expected
