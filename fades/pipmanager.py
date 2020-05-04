# Copyright 2014-2020 Facundo Batista, Nicolás Demarchi
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

"""Interface to handle pip.

We are not using pip as a API because fades is not running in the same
env that the child program. So we have to call the pip binary that is inside
the created virtualenv.
"""

import os
import logging
import shutil
import contextlib

from urllib import request

from fades import helpers

logger = logging.getLogger(__name__)

PIP_INSTALLER = "https://bootstrap.pypa.io/get-pip.py"


class PipManager():
    """A manager for all PIP related actions."""

    def __init__(self, env_bin_path, pip_installed=False, options=None):
        """Init."""
        self.env_bin_path = env_bin_path
        self.pip_installed = pip_installed
        self.options = options
        self.pip_exe = os.path.join(self.env_bin_path, "pip")
        basedir = helpers.get_basedir()
        self.pip_installer_fname = os.path.join(basedir, "get-pip.py")

    def install(self, dependency):
        """Install a new dependency."""
        if not self.pip_installed:
            logger.info("Need to install a dependency with pip, but no builtin, "
                        "doing it manually (just wait a little, all should go well)")
            self._brute_force_install_pip()

        # split to pass several tokens on multiword dependency (this is very specific for '-e' on
        # external requirements, but implemented generically; note that this does not apply for
        # normal reqs, because even if it originally is 'foo > 1.2', after parsing it loses the
        # internal spaces)
        str_dep = str(dependency)
        args = [self.pip_exe, "install"] + str_dep.split()

        if self.options:
            for option in self.options:
                args.extend(option.split())
        logger.info("Installing dependency: %r", str_dep)
        try:
            helpers.logged_exec(args)
        except helpers.ExecutionError as error:
            error.dump_to_log(logger)
            raise error
        except Exception as error:
            logger.exception("Error installing %s: %s", str_dep, error)
            raise error

    def get_version(self, dependency):
        """Return the installed version parsing the output of 'pip show'."""
        logger.debug("getting installed version for %s", dependency)
        stdout = helpers.logged_exec([self.pip_exe, "show", str(dependency)])
        version = [line for line in stdout if line.startswith('Version:')]
        if len(version) == 1:
            version = version[0].strip().split()[1]
            logger.debug("Installed version of %s is: %s", dependency, version)
            return version
        else:
            logger.error('Fades is having problems getting the installed version. '
                         'Run with -v or check the logs for details')
            return ''

    def _download_pip_installer(self):
        u = request.urlopen(PIP_INSTALLER)
        temp_location = self.pip_installer_fname + '.temp'
        with contextlib.closing(u), open(temp_location, 'wb') as f:
            shutil.copyfileobj(u, f)
        os.rename(temp_location, self.pip_installer_fname)

    def _brute_force_install_pip(self):
        """A brute force install of pip itself."""
        if os.path.exists(self.pip_installer_fname):
            logger.debug("Using pip installer from %r", self.pip_installer_fname)
        else:
            logger.debug(
                "Installer for pip not found in %r, downloading it", self.pip_installer_fname)
            self._download_pip_installer()

        logger.debug("Installing PIP manually in the virtualenv")
        python_exe = os.path.join(self.env_bin_path, "python")
        helpers.logged_exec([python_exe, self.pip_installer_fname, '-I'])
        self.pip_installed = True

    def freeze(self, filepath):
        """Dump venv contents to the indicated filepath."""
        logger.debug("running freeze to store in %r", filepath)
        stdout = helpers.logged_exec([self.pip_exe, "freeze", "--all", "--local"])
        with open(filepath, "wt", encoding='utf8') as fh:
            fh.writelines(line + '\n' for line in sorted(stdout))
