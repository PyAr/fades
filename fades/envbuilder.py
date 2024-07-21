# Copyright 2014-2024 Facundo Batista, Nicolás Demarchi
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

"""Tools to create, destroy and handle usage of virtual environments."""

import logging
import os
import pathlib
import shutil

from datetime import datetime, timezone
from venv import EnvBuilder
from uuid import uuid4

from fades import FadesError, REPO_PYPI, REPO_VCS
from fades import helpers
from fades.pipmanager import PipManager
from fades.multiplatform import filelock

logger = logging.getLogger(__name__)

# UTC can be imported directly from datetime from Python 3.11
UTC = timezone.utc


class _FadesEnvBuilder(EnvBuilder):
    """Create always a virtual environment.

    This is structured as a class mostly to take advantage of EnvBuilder, not because
    it's provides the best interface: external callers should just use module's ``create_env``
    and ``destroy_env``.
    """

    def __init__(self):
        basedir = helpers.get_basedir()
        self.env_path = os.path.join(basedir, str(uuid4()))
        self.env_bin_path = ''
        logger.debug("Env will be created at: %s", self.env_path)

        if os.environ.get("SNAP"):
            # running inside a snap: we need to avoid EnvBuilder ending up running ensurepip
            # because it doesn't work properly (it does a special magic to run the script
            # and ends up mixing external and internal pips)
            self.pip_installed = False

        else:
            # try to install pip using default machinery (which will work in a lot
            # of systems, noticeably it won't in some debians or ubuntus, like
            # Trusty; in that cases mark it to install manually later)
            try:
                import ensurepip  # NOQA
                self.pip_installed = True
            except ImportError:
                self.pip_installed = False

        super().__init__(with_pip=self.pip_installed, symlinks=True)

    def create_with_external_venv(self, interpreter, options):
        """Create a virtual environment using the venv module externally."""
        args = [interpreter, "-m", "venv", self.env_path]
        args.extend(options)
        if not self.pip_installed:
            args.insert(3, '--without-pip')

        try:
            helpers.logged_exec(args)
        except helpers.ExecutionError as error:
            error.dump_to_log(logger)
            raise FadesError("Failed to run venv module externally")
        except Exception as error:
            logger.exception("Error creating virtual environment:  %s", error)
            raise FadesError("General error while running external venv")

        # XXX Facundo 2024-06-29: the helper uses pathlib; eventually everything will be
        # pathlib (see #435), so these translations will be cleaned up
        self.env_bin_path = str(helpers.get_env_bin_path(pathlib.Path(self.env_path)))

    def create_env(self, interpreter, is_current, options):
        """Create the virtual environment and return its info."""
        venv_options = options['venv_options']
        if is_current:
            # apply venv options
            logger.debug("Creating virtual environment internally; options=%s", venv_options)
            for option in venv_options:
                attrname = option[2:].replace("-", "_")  # '--system-packgs' ->  'system_packgs'
                setattr(self, attrname, True)
            self.create(self.env_path)
        else:
            logger.debug(
                "Creating virtual environment with external venv; options=%s", venv_options)
            self.create_with_external_venv(interpreter, venv_options)
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


def create_venv(requested_deps, interpreter, is_current, options, pip_options, avoid_pip_upgrade):
    """Create a new virtualvenv with the requirements of this script."""
    # create virtual environment
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
            mgr = PipManager(
                env_bin_path, pip_installed=pip_installed, options=pip_options,
                avoid_pip_upgrade=avoid_pip_upgrade)
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
                logger.debug("Installation Step failed, removing virtual environment")
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
                project = dependency.name
                version = mgr.get_version(project)
            installed[repo][project] = version

        logger.debug("Installed dependencies: %s", installed)
    return venv_data, installed


def destroy_venv(env_path, venvscache=None):
    """Destroy a venv."""
    # remove the venv itself in disk
    logger.debug("Destroying virtual environment at: %s", env_path)
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
        file_.write('{} {}\n'.format(uuid, self._datetime_to_str(datetime.now(UTC))))

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
            now = datetime.now(UTC)
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
                    logger.info("Destroying virtual environment at: %s", env_path)
                    destroy_venv(env_path, self.venvscache)

            self._write_compacted_dict_usage_to_file(venvs_dict)

    def _get_compacted_dict_usage_from_file(self):
        all_lines = open(self.stat_file_path).readlines()
        return dict(x.split() for x in all_lines)

    def _write_compacted_dict_usage_to_file(self, dict_usage):
        with open(self.stat_file_path, 'wt') as file_:
            for uuid, date in dict_usage.items():
                file_.write('{} {}\n'.format(uuid, date))
