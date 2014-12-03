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
from uuid import uuid4
from xdg import BaseDirectory
from fades.parsing import Repo


logger = logging.getLogger(__name__)


class FadesEnvBuilder(EnvBuilder):
    """create always a virtualenv and install the dependencies"""
    def __init__(self, deps):
        basedir = os.path.join(BaseDirectory.xdg_data_home, 'fades')
        self.env_path = "{}/{}".format(basedir, uuid4())
        self.env_bin_path = ""
        self.deps = deps
        super().__init__(with_pip=True)
        logger.info("libs to install: %s", self.deps)
        logger.info("env will be created at: %s", self.env_path)

    def create_and_install(self):
        self.create(self.env_path)

    def post_setup(self, context):
        "Install deps into the enviroment being created"
        self.env_bin_path = context.bin_path
        for dependency in self.deps:
            if dependency.repo == Repo.pypi:
                self._pip_install(dependency)
            else:
                logger.warning(
                    "install from %s not implemented", dependency.repo)
        self._save_fades_info()

    def _pip_install(self, dependency):
        "install a dependency with pip"
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
        "Save env and deps info in file's xattr"
        pass
