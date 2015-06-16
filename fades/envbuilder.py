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

"""Extended class from EnvBuilder to create a venv using a uuid4 id.

NOTE: this class only work in the same python version that Fades is
running. So, you don't need to have installed a virtualenv tool. For
other python versions Fades needs a virtualenv tool installed.
"""

import logging
import os

from venv import EnvBuilder
from uuid import uuid4

from fades import REPO_PYPI
from fades import helpers
from fades.pipmanager import PipManager

try:
    # test if virtualenv is installed
    import virtualenv  # NOQA
except ImportError:
    virtualenv = None

logger = logging.getLogger(__name__)


class FadesEnvBuilder(EnvBuilder):
    """Create always a virtualenv"""
    def __init__(self):
        basedir = helpers.get_basedir()
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

        super().__init__(with_pip=self.pip_installed, symlinks=True)

    def create_with_virtualenv(self, interpreter):
        """Create a virtualenv using the virtualenv lib."""
        if virtualenv is None:
            logger.error('Virtualenv is not installed. It is needed to create a virtualenv with '
                         'a different python version than fades')
            exit()
        args = ['virtualenv', '--python', interpreter, self.env_path]
        if not self.with_pip:
            args.insert(3, '--no-pip')
        try:
            helpers.logged_exec(args)
            self.env_bin_path = os.path.join(self.env_path, 'bin')
        except Exception as error:
            logger.exception("Error creating virtualenv:  %s", error)
            exit()

    def create_env(self, interpreter, is_current):
        """Create the virtualenv and return its info."""
        if is_current:
            logger.debug("Creating virtualenv with pyvenv")
            self.create(self.env_path)
        else:
            logger.debug("Creating virtualenv with virtualenv")
            self.create_with_virtualenv(interpreter)
        logger.debug("env_bin_path: %s", self.env_bin_path)
        return self.env_path, self.env_bin_path, self.pip_installed

    def post_setup(self, context):
        """Gets the bin path from context."""
        self.env_bin_path = context.bin_path


def create_venv(requested_deps, interpreter, is_current):
    """Create a new virtualvenv with the requirements of this script."""
    # create virtualenv
    env = FadesEnvBuilder()
    env_path, env_bin_path, pip_installed = env.create_env(interpreter, is_current)
    venv_data = {}
    venv_data['env_path'] = env_path
    venv_data['env_bin_path'] = env_bin_path
    venv_data['pip_installed'] = pip_installed

    # install deps
    installed = {}
    for repo in requested_deps.keys():
        if repo == REPO_PYPI:
            mgr = PipManager(env_bin_path, pip_installed=pip_installed)
        else:
            logger.warning("Install from %r not implemented", repo)
            continue
        installed[repo] = {}

        repo_requested = requested_deps[repo]
        logger.debug("Installing dependencies for repo %r: requested=%s", repo, repo_requested)
        for dependency in repo_requested:
            mgr.install(dependency)

            # always store the installed dependency, as in the future we'll select the venv
            # based on what is installed, not what used requested (remember that user may
            # request >, >=, etc!)
            project = dependency.project_name
            installed[repo][project] = mgr.get_version(project)

        logger.debug("Installed dependencies: %s", installed)
    return venv_data, installed
