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
#
# NOTE: We are not using pip as a API because fades is not running in the same
# env that the child program. So we have to call the pip binary that is inside
# the created virtualenv.


import os
import logging
import subprocess

from urllib import request
from xdg import BaseDirectory

from fades.helpers import logged_exec

logger = logging.getLogger(__name__)

PIP_INSTALLER = "https://bootstrap.pypa.io/get-pip.py"


class PipManager():
    """A manager for all PIP related actions."""
    def __init__(self, env_bin_path, pip_installed=False):
        self.env_bin_path = env_bin_path
        self.pip_installed = pip_installed
        self.pip_exe = os.path.join(self.env_bin_path, "pip")
        basedir = os.path.join(BaseDirectory.xdg_data_home, 'fades')
        self.pip_installer_fname = os.path.join(basedir, "get-pip.py")

    def _handle_dep(self, module, version):
        """Install/upgrade a dependency wit pip."""
        if not self.pip_installed:
            logger.info("Need to install a dependency with pip, but no builtin"
                        ", install it manually")
            self._brute_force_install_pip()

        if version is not None:
            module = module + version
        args = [self.pip_exe, "install", module]
        logger.info("Installing dependency: %s", module)
        try:
            logged_exec(args)
        except Exception as error:
            logger.exception("Error installing %s: %s", module, error)
            exit()

    def install(self, module, version):
        """Install a new dependency."""
        self._handle_dep(module, version)

    def update(self, module, version):
        """Update a dependency revision."""
        self._handle_dep(module, version)

    def remove(self, module):
        """Remove a dependency."""
        args = [self.pip_exe, "uninstall", module, '--yes']
        logger.info("Uninstalling dependency: %s", module)
        try:
            logged_exec(args)
        except Exception as error:
            logger.exception("Error uninstalling %s: %s", module, error)
            exit()

    def get_version(self, dependency):
        """Returns the installed version parsing the output of 'pip show'."""
        logger.debug("getting installed versión for %s", dependency)
        cmd = [self.pip_exe, "show", dependency]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        version = p.stdout.readlines()[2].decode('utf-8').strip().split()[1]
        logger.debug("Installed versión of %s is: %s", dependency, version)
        return version

    def _brute_force_install_pip(self):
        """A brute force install of pip itself."""
        if os.path.exists(self.pip_installer_fname):
            logger.debug("Using pip installer from %r", self.pip_installer_fname)
        else:
            logger.debug("Installer for pip not found in %r, downloading it", self.pip_installer_fname)
            u = request.urlopen(PIP_INSTALLER)
            with open(self.pip_installer_fname, 'wb') as fh:
                fh.write(u.read())

        logger.debug("Installing PIP manually in the virtualenv")
        python_exe = os.path.join(self.env_bin_path, "python")
        logged_exec([python_exe, self.pip_installer_fname])
