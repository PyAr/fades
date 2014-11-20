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


logger = logging.getLogger(__name__)
basedir = os.path.join(BaseDirectory.xdg_data_home, 'fades')


class FadesEnvBuilder(EnvBuilder):
    """create always a virtualenv and install the dependencies"""

    def __init__(self, system_site_packages=False, clear=False,
                 symlinks=False, upgrade=False, with_pip=True,
                 libs_to_install=None):

        self.venv_path = "{}/{}".format(basedir, uuid4())
        self.libs_to_install = libs_to_install
        super().__init__(system_site_packages, clear, symlinks, upgrade,
                         with_pip)

    def post_setup(self, context):
        print("acá se ejecutan muchas cosas")
        print("path: {}".format(self.venv_path))
        print("libs: {}".format(self.libs_to_install))

    def pip_install(self, libs_to_install):
        pass


def main():
    libs_to_install = ["requests", "touchandgo"]
    builder = FadesEnvBuilder(libs_to_install=libs_to_install)
    builder.create(builder.venv_path)

if __name__ == '__main__':
    main()
