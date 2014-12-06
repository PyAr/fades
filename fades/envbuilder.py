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

""" class extended from EnvBuilder to create a venv and install
    deps from diferents sources in it"""

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


class FadesEnvBuilder(EnvBuilder):
    """Create always a virtualenv and install the dependencies."""
    def __init__(self, deps):
        basedir = os.path.join(BaseDirectory.xdg_data_home, 'fades')
        self.env_path = "{}/{}".format(basedir, uuid4())
        self.pip_installer_fname = os.path.join(basedir, "get-pip.py")
        self.env_bin_path = ""
        self.deps = deps
        super().__init__(with_pip=False)
        logger.info("libs to install: %s", self.deps)
        logger.info("env will be created at: %s", self.env_path)

        # try to install pip using default machinery (which will work in a lot
        # of systems, noticeably it won't in some debians or ubuntus, like
        # Trusty; in that cases mark it to install manually later)
        self._builtin_pip = True
        try:
            import ensurepip
        except ImportError:
            self._builtin_pip = False

    def create_and_install(self):
        self.create(self.env_path)

    def post_setup(self, context):
        """Install deps into the enviroment being created."""
        self.env_bin_path = context.bin_path
        for dependency in self.deps:
            if dependency.repo == Repo.pypi:
                self._pip_install(dependency)
            else:
                logger.warning(
                    "install from %s not implemented", dependency.repo)
        self._save_fades_info()

    def _brute_force_install_pip(self):
        """A brute force install of pip itself."""
        if os.path.exists(self.pip_installer_fname):
            logger.info("Using pip installer from %r",
                        self.pip_installer_fname)
        else:
            logger.info("Installer for pip not found in %r, downloading it",
                        self.pip_installer_fname)
            u = request.urlopen(PIP_INSTALLER)
            with open(self.pip_installer_fname, 'wb') as fh:
                fh.write(u.read())

        logger.info("Installing PIP manually in the virtualenv")
        python_exe = os.path.join(self.env_bin_path, "python")
        subprocess.check_call([python_exe, self.pip_installer_fname])

    def _pip_install(self, dependency):
        "install a dependency with pip"
        if not self._builtin_pip:
            logger.info("Need to install a dependency with pip, "
                        "but no builtin, install it manually")
            self._brute_force_install_pip()

        pip_exe = "{}/pip".format(self.env_bin_path)
        if dependency.version is None:
            module = dependency.module
        else:
            module = dependency.module+dependency.version
        args = [pip_exe, "install", module]
        logger.info("running: %s", args)
        try:
            #FIXME : send stdout and stderror to logfile? print human info
            subprocess.check_call(args)
        except Exception as error:
            logger.error("Error installing %s : %s", module, error)

    def _save_fades_info(self):
        """Save env and deps info in file's xattr."""
        pass
