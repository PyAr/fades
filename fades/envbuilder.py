# Copyright 2014-2016 Facundo Batista, Nicolás Demarchi
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
import shutil
import sys

from datetime import datetime
from venv import EnvBuilder
from uuid import uuid4

from fades import FadesError, REPO_PYPI, REPO_VCS
from fades import helpers
from fades.pipmanager import PipManager
from fades.multiplatform import filelock

logger = logging.getLogger(__name__)


class _FadesEnvBuilder(EnvBuilder):
    """Create always a virtualenv.

    This is structured as a class mostly to take advantage of EnvBuilder, not because
    it's provides the best interface: external callers should just use module's ``create_env``
    and ``destroy_env``.
    """

    def __init__(self, env_path=None):
        """Init."""
        basedir = helpers.get_basedir()
        if env_path is None:
            env_path = os.path.join(basedir, str(uuid4()))
        self.env_path = env_path
        self.env_bin_path = ''
        logger.debug("Env will be created at: %s", self.env_path)

        if sys.version_info >= (3, 4):
            # try to install pip using default machinery (which will work in a lot
            # of systems, noticeably it won't in some debians or ubuntus, like
            # Trusty; in that cases mark it to install manually later)
            try:
                import ensurepip  # NOQA
                self.pip_installed = True
            except ImportError:
                self.pip_installed = False

            super().__init__(with_pip=self.pip_installed, symlinks=True)

        else:
            # old Python doesn't have integrated pip
            self.pip_installed = False
            super().__init__(symlinks=True)

    def create_with_virtualenv(self, interpreter, virtualenv_options):
        """Create a virtualenv using the virtualenv lib."""
        args = ['virtualenv', '--python', interpreter, self.env_path]
        args.extend(virtualenv_options)
        if not self.pip_installed:
            args.insert(3, '--no-pip')
        try:
            helpers.logged_exec(args)
            self.env_bin_path = os.path.join(self.env_path, 'bin')
        except FileNotFoundError as error:
            logger.error('Virtualenv is not installed. It is needed to create a virtualenv with '
                         'a different python version than fades (got {})'.format(error))
            raise FadesError('virtualenv not found')
        except helpers.ExecutionError as error:
            error.dump_to_log(logger)
            raise FadesError('virtualenv could not be run')
        except Exception as error:
            logger.exception("Error creating virtualenv:  %s", error)
            raise FadesError('General error while running virtualenv')

    def create_env(self, interpreter, is_current, options):
        """Create the virtualenv and return its info."""
        if is_current:
            # apply pyvenv options
            pyvenv_options = options['pyvenv_options']
            if "--system-site-packages" in pyvenv_options:
                self.system_site_packages = True
            logger.debug("Creating virtualenv with pyvenv. options=%s", pyvenv_options)
            self.create(self.env_path)
        else:
            virtualenv_options = options['virtualenv_options']
            logger.debug("Creating virtualenv with virtualenv")
            self.create_with_virtualenv(interpreter, virtualenv_options)
        logger.debug("env_bin_path: %s", self.env_bin_path)

        # Re check if pip was installed (supporting both binary and .exe for Windows)
        pip_bin = os.path.join(self.env_bin_path, "pip")
        pip_exe = os.path.join(self.env_bin_path, "pip.exe")
        if not (os.path.exists(pip_bin) or os.path.exists(pip_exe)):
            logger.debug("pip isn't installed in the venv, setting pip_installed=False")
            self.pip_installed = False

        return self.env_path, self.env_bin_path, self.pip_installed

    def post_setup(self, context):
        """Get the bin path from context."""
        self.env_bin_path = context.bin_path


def create_venv(requested_deps, interpreter, is_current, options, pip_options):
    """Create a new virtualvenv with the requirements of this script."""
    # create virtualenv
    env = _FadesEnvBuilder()
    env_path, env_bin_path, pip_installed = env.create_env(interpreter, is_current, options)
    venv_data = {}
    venv_data['env_path'] = env_path
    venv_data['env_bin_path'] = env_bin_path
    venv_data['pip_installed'] = pip_installed

    # install deps
    installed = {}
    for repo in requested_deps.keys():
        if repo in (REPO_PYPI, REPO_VCS):
            mgr = PipManager(env_bin_path, pip_installed=pip_installed, options=pip_options)
        else:
            logger.warning("Install from %r not implemented", repo)
            continue
        installed[repo] = {}

        repo_requested = requested_deps[repo]
        logger.debug("Installing dependencies for repo %r: requested=%s", repo, repo_requested)
        for dependency in repo_requested:
            try:
                mgr.install(dependency)
            except Exception:
                logger.debug("Installation Step failed, removing virtualenv")
                destroy_venv(env_path)
                raise FadesError('Dependency installation failed')

            if repo == REPO_VCS:
                # no need to request the installed version, as we'll always compare
                # to the url itself
                project = dependency.url
                version = None
            else:
                # always store the installed dependency, as in the future we'll select the venv
                # based on what is installed, not what used requested (remember that user may
                # request >, >=, etc!)
                project = dependency.project_name
                version = mgr.get_version(project)
            installed[repo][project] = version

        logger.debug("Installed dependencies: %s", installed)
    return venv_data, installed


def destroy_venv(env_path, venvscache=None):
    """Destroy a venv."""
    # remove the venv itself in disk
    logger.debug("Destroying virtualenv at: %s", env_path)
    shutil.rmtree(env_path, ignore_errors=True)

    # remove venv from cache
    if venvscache is not None:
        venvscache.remove(env_path)


class UsageManager:
    """Class to handle usage file and venv cleanning."""

    def __init__(self, stat_file_path, venvscache):
        """Init."""
        self.stat_file_path = stat_file_path
        self.stat_file_lock = stat_file_path + '.lock'
        self.venvscache = venvscache
        self._create_initial_usage_file_if_not_exists()

    def store_usage_stat(self, venv_data, cache):
        """Log an usage record for venv_data."""
        with open(self.stat_file_path, 'at') as f:
            self._write_venv_usage(f, venv_data)

    def _create_initial_usage_file_if_not_exists(self):
        if not os.path.exists(self.stat_file_path):
            existing_venvs = self.venvscache.get_venvs_metadata()
            with open(self.stat_file_path, 'wt') as f:
                for venv_data in existing_venvs:
                    self._write_venv_usage(f, venv_data)

    def _write_venv_usage(self, file_, venv_data):
        _, uuid = os.path.split(venv_data['env_path'])
        file_.write('{} {}\n'.format(uuid, self._datetime_to_str(datetime.utcnow())))

    def _datetime_to_str(self, datetime_):
        return datetime.strftime(datetime_, "%Y-%m-%dT%H:%M:%S.%f")

    def _str_to_datetime(self, str_):
        return datetime.strptime(str_, "%Y-%m-%dT%H:%M:%S.%f")

    def clean_unused_venvs(self, max_days_to_keep):
        """Compact usage stats and remove venvs.

        This method loads the complete file usage in memory, for every venv compact all records in
        one (the lastest), updates this info for every env deleted and, finally, write the entire
        file to disk.

        If something failed during this steps, usage file remains unchanged and can contain some
        data about some deleted env. This is not a problem, the next time this function it's
        called, this records will be deleted.
        """
        with filelock(self.stat_file_lock):
            now = datetime.utcnow()
            venvs_dict = self._get_compacted_dict_usage_from_file()
            for venv_uuid, usage_date in venvs_dict.copy().items():
                usage_date = self._str_to_datetime(usage_date)
                if (now - usage_date).days > max_days_to_keep:
                    # remove venv from usage dict
                    del venvs_dict[venv_uuid]
                    venv_meta = self.venvscache.get_venv(uuid=venv_uuid)
                    if venv_meta is None:
                        # if meta isn't found means that something had failed previously and
                        # usage_file wasn't updated.
                        continue
                    env_path = venv_meta['env_path']
                    logger.info("Destroying virtualenv at: %s", env_path)  # #256
                    destroy_venv(env_path, self.venvscache)

            self._write_compacted_dict_usage_to_file(venvs_dict)

    def _get_compacted_dict_usage_from_file(self):
        all_lines = open(self.stat_file_path).readlines()
        return dict(x.split() for x in all_lines)

    def _write_compacted_dict_usage_to_file(self, dict_usage):
        with open(self.stat_file_path, 'wt') as file_:
            for uuid, date in dict_usage.items():
                file_.write('{} {}\n'.format(uuid, date))
