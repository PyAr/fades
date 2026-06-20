# Copyright 2024-2026 Facundo Batista, Nicolás Demarchi
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

"""Interface to handle uv as an alternative backend to pip.

uv has no supported Python API, so (just like pip) we invoke its binary through subprocess.
It operates on the already-created virtualenv by pointing ``--python`` at the venv's interpreter.
"""

import logging
from pathlib import Path

from fades import helpers

logger = logging.getLogger(__name__)


class UvManager():
    """A manager for all uv related actions.

    Exposes the same public interface as ``PipManager`` (install/get_version/freeze) so it can be
    used interchangeably as a fades install backend.
    """

    def __init__(self, env_bin_path: Path, options: list = None, uv_exe: str = None):
        self.env_bin_path = env_bin_path
        self.options = options
        self.python_exe = self.env_bin_path / "python"
        self.uv_exe = uv_exe or helpers.get_uv_exe()

    def install(self, dependency):
        """Install a new dependency into the venv using uv."""
        # split to pass several tokens on multiword dependency (this is very specific for '-e' on
        # external requirements, but implemented generically; mirror PipManager.install)
        str_dep = str(dependency)
        args = [self.uv_exe, "pip", "install", "--python", str(self.python_exe)] + str_dep.split()

        if self.options:
            for option in self.options:
                args.extend(option.split())
        logger.info("Installing dependency (with uv): %r", str_dep)
        try:
            helpers.logged_exec(args)
        except helpers.ExecutionError as error:
            error.dump_to_log(logger)
            raise error
        except Exception as error:
            logger.exception("Error installing %s: %s", str_dep, error)
            raise error

    def get_version(self, dependency):
        """Return the installed version parsing the output of 'uv pip show'."""
        logger.debug("getting installed version for %s", dependency)
        # note: no '--quiet' here, as uv silences the whole 'pip show' output with it (the
        # informational "Using Python ... environment" line it emits is harmless, as below we
        # only keep lines starting with 'Version:')
        stdout = helpers.logged_exec(
            [self.uv_exe, "pip", "show", "--python", str(self.python_exe), str(dependency)])
        version = [line for line in stdout if line.startswith('Version:')]
        if len(version) == 1:
            version = version[0].strip().split()[1]
            logger.debug("Installed version of %s is: %s", dependency, version)
            return version
        else:
            logger.error('Fades is having problems getting the installed version. '
                         'Run with -v or check the logs for details')
            return ''

    def freeze(self, filepath: Path):
        """Dump venv contents to the indicated filepath."""
        logger.debug("running freeze to store in %r", filepath)
        stdout = helpers.logged_exec(
            [self.uv_exe, "pip", "freeze", "--quiet", "--python", str(self.python_exe)])
        with open(filepath, "wt", encoding='utf8') as fh:
            fh.writelines(line + '\n' for line in sorted(stdout))
