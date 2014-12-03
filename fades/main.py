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

"""Main 'fades' modules."""

import logging
import subprocess

from fades.envbuilder import FadesEnvBuilder
from fades import parsing

logger = logging.getLogger(__name__)


def go(argv):
    """Make the magic happen."""
    deps = parsing.parse_file(argv[1])
    env = FadesEnvBuilder(deps)
    env.create_and_install()
    python_exe = "{}/python3".format(env.env_bin_path)
    subprocess.check_call([python_exe] + argv[1:])
