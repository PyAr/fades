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
from venv import EnvBuilder
from uuid import uuid4
from xdg import BaseDirectory
from subprocess import Popen


logger = logging.getLogger(__name__)


class FadesEnvBuilder(EnvBuilder):
    """create always a virtualenv and install the dependencies"""

    def __init__(self, libs_to_install):
        basedir = os.path.join(BaseDirectory.xdg_data_home, 'fades')
        self.venv_path = "{}/{}".format(basedir, uuid4())
        self.libs_to_install = libs_to_install
        self.install_from = "pip"
        self.bin_path = None
        super().__init__(with_pip=True)
        logger.info(("libs to install: {}".format(self.libs_to_install)))
        logger.info("venv will be created on: {}".format(self.venv_path))

    def post_setup(self, context):
        self.bin_path = context.bin_path
        if self.install_from == "pip":
            self.pip_install()



    def pip_install(self):
        "install libs with pip"
        pip_exe = "{}/pip".format(self.bin_path)
        args = [pip_exe, "install"]
        args.extend(self.libs_to_install)
        logger.debug("running: %s", args)
        process = Popen(args)
        return process


def main():
    libs_to_install = ["requests", "flask"]
    builder = FadesEnvBuilder(libs_to_install)
    builder.create(builder.venv_path)

if __name__ == '__main__':
    main()
