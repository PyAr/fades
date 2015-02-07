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

"""Extended class from EnvBuilder to create a venv using a uuid4 id."""
# NOTE: this class only work in the same python version that Fades is running. So you don't need
# to have installed a virtualenv tool. For other python versions Fades needs a
# virtualenv tool installed.

import logging
import os

from venv import EnvBuilder
from uuid import uuid4
from xdg import BaseDirectory


logger = logging.getLogger(__name__)


class FadesEnvBuilder(EnvBuilder):
    """Create always a virtualenv"""
    def __init__(self):
        basedir = os.path.join(BaseDirectory.xdg_data_home, 'fades')
        self.env_path = os.path.join(basedir, str(uuid4()))
        self.env_bin_path = ''
        logger.debug("Env will be created at: %s", self.env_path)

        # try to install pip using default machinery (which will work in a lot
        # of systems, noticeably it won't in some debians or ubuntus, like
        # Trusty; in that cases mark it to install manually later)
        try:
            import ensurepip  # NOQA
            self.pip_installed = True
        except ImportError:
            self.pip_installed = False

        if self.pip_installed:
            super().__init__(with_pip=True)
        else:
            super().__init__(with_pip=False)

    def create_env(self):
        """Create the virtualenv and return its info."""
        self.create(self.env_path)
        logger.debug("env_bin_path: %s", self.env_bin_path)
        return self.env_path, self.env_bin_path, self.pip_installed

    def post_setup(self, context):
        """Gets the bin path from context."""
        self.env_bin_path = context.bin_path
