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

"""Create a venv and install deps from diferents sources in it."""

import logging
import os
import subprocess

from venv import EnvBuilder
from urllib import request
from uuid import uuid4
from xdg import BaseDirectory

from fades.parsing import Repo

logger = logging.getLogger(__name__)

PIP_INSTALLER = "https://bootstrap.pypa.io/get-pip.py"


def _logged_exec(cmd):
    """Execute a command, redirecting the output to the log."""
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout:
        logger.debug(line[:-1].decode("utf8"))


class FadesEnvBuilder(EnvBuilder):
    """Create always a virtualenv and install the dependencies."""
    def __init__(self, deps):
        basedir = os.path.join(BaseDirectory.xdg_data_home, 'fades')
        self.env_path = os.path.join(basedir, str(uuid4()))
        self.pip_installer_fname = os.path.join(basedir, "get-pip.py")
        self.env_bin_path = ""
        self.deps = deps
        logger.debug("Libs to install: %s", self.deps)
        logger.debug("Env will be created at: %s", self.env_path)

        # try to install pip using default machinery (which will work in a lot
        # of systems, noticeably it won't in some debians or ubuntus, like
        # Trusty; in that cases mark it to install manually later)
        try:
            import ensurepip  # NOQA
            self._pip_installed = True
        except ImportError:
            self._pip_installed = False

        if self._pip_installed:
            super().__init__(with_pip=True)
        else:
            super().__init__(with_pip=False)

    def create_and_install(self):
        """Create and install the venv."""
        self.create(self.env_path)

    def post_setup(self, context):
        """Install deps into the enviroment being created."""
        self.env_bin_path = context.bin_path
        for dependency in self.deps:
            if dependency.repo == Repo.pypi:
                self._pip_install(dependency)
            else:
                logger.warning("Install from %s not implemented",
                               dependency.repo)
        self._save_fades_info()

    def _brute_force_install_pip(self):
        """A brute force install of pip itself."""
        if os.path.exists(self.pip_installer_fname):
            logger.debug("Using pip installer from %r",
                         self.pip_installer_fname)
        else:
            logger.debug("Installer for pip not found in %r, downloading it",
                         self.pip_installer_fname)
            u = request.urlopen(PIP_INSTALLER)
            with open(self.pip_installer_fname, 'wb') as fh:
                fh.write(u.read())

        logger.debug("Installing PIP manually in the virtualenv")
        python_exe = os.path.join(self.env_bin_path, "python")
        _logged_exec([python_exe, self.pip_installer_fname])

    def _pip_install(self, dependency):
        """Install a dependency with pip."""
        if not self._pip_installed:
            logger.info("Need to install a dependency with pip, "
                        "but no builtin, install it manually")
            self._brute_force_install_pip()
            self._pip_installed = True

        pip_exe = os.path.join(self.env_bin_path, "pip")
        if dependency.version is None:
            module = dependency.module
        else:
            module = dependency.module + dependency.version
        args = [pip_exe, "install", module]
        logger.info("Installing dependency: %s", module)
        try:
            _logged_exec(args)
        except Exception as error:
            logger.error("Error installing %s: %s", module, error)

    def _save_fades_info(self):
        """Save env and deps info in file's xattr."""
        pass
