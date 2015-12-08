# Copyright 2014-2015 Facundo Batista, Nicolás Demarchi
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

"""A collection of utilities for fades."""

import os
import sys
import json
import logging
import subprocess

from urllib import request
from urllib.error import HTTPError

from fades import parsing

logger = logging.getLogger(__name__)

SHOW_VERSION_CMD = """
import sys, json
d = dict(path=sys.executable)
d.update(zip('major minor micro releaselevel serial'.split(), sys.version_info))
print(json.dumps(d))
"""

BASE = 'http://pypi.python.org/pypi/{name}/json'


def logged_exec(cmd):
    """Execute a command, redirecting the output to the log."""
    logger = logging.getLogger('fades.exec')
    logger.debug("Executing external command: %r", cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout = []
    for line in p.stdout:
        line = line[:-1].decode("utf8")
        stdout.append(line)
        logger.debug(":: " + line)
    retcode = p.wait()
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd)
    return stdout


def get_basedir():
    """Get the base fades directory, from xdg or kinda hardcoded."""
    try:
        from xdg import BaseDirectory  # NOQA
        return os.path.join(BaseDirectory.xdg_data_home, 'fades')
    except ImportError:
        logger.debug("Package xdg not installed; using ~/.fades folder")
        from os.path import expanduser
        return expanduser("~/.fades")


def _get_interpreter_info(interpreter=None):
    """Return the interpreter's full path using pythonX.Y format."""
    if interpreter is None:
        # If interpreter is None by default returns the current interpreter data.
        major, minor = sys.version_info[:2]
        executable = sys.executable
    else:
        args = [interpreter, '-c', SHOW_VERSION_CMD]
        try:
            requested_interpreter_info = logged_exec(args)
        except Exception as error:
            logger.error("Error getting requested interpreter version: %s", error)
            exit()
        requested_interpreter_info = json.loads(requested_interpreter_info[0])
        executable = requested_interpreter_info['path']
        major = requested_interpreter_info['major']
        minor = requested_interpreter_info['minor']
    if executable[-1].isdigit():
        executable = executable.split(".")[0][:-1]
    interpreter = "{}{}.{}".format(executable, major, minor)
    return interpreter


def get_interpreter_version(requested_interpreter):
    """Return a 'sanitized' interpreter and indicates if it is the current one."""
    logger.debug('Getting interpreter version for: %s', requested_interpreter)
    current_interpreter = _get_interpreter_info()
    logger.debug('Current interpreter is %s', current_interpreter)
    if requested_interpreter is None:
        return(current_interpreter, True)
    else:
        requested_interpreter = _get_interpreter_info(requested_interpreter)
        is_current = requested_interpreter == current_interpreter
        logger.debug('Interpreter=%s. It is the same as fades?=%s',
                     requested_interpreter, is_current)
        return (requested_interpreter, is_current)


def get_latest_version_number(project_name):
    """Return last version of a package."""
    try:
        raw = request.urlopen(BASE.format(name=project_name)).read()
    except HTTPError:
        logger.warning("Requested project named %s is not found in pypi",
                       project_name)
        return None
    else:
        try:
            data = json.loads(raw.decode("utf8"))
            last_version = data["info"]["version"]
        except (KeyError, ValueError):  # malformed json or empty string
            logger.error("Could not get the version of the package")
            return None
        return last_version


def check_updates(dependencies):
    """Return a list of dependencies to upgrade."""
    dependencies_up_to_date = []
    dependencies_names_to_update = []
    for dependency in dependencies.get('pypi'):
        # get last version from pypi api
        last_version = get_latest_version_number(dependency.project_name)

        # get required version
        required_version = None
        if dependency.specs:
            lookup, required_version = dependency.specs[0]

        # log in INFO if there is a new version
        if last_version is not None and required_version is not None:
            if last_version > required_version:
                logger.info("There is a new version %s of %s",
                            last_version, dependency.project_name)

        if not required_version:
            project_name = "%s==%s" % (dependency.project_name, last_version)
            dependencies_names_to_update.append(project_name)
        else:
            dependencies_up_to_date.append(dependency)

    new_deps = parsing.parse_manual(dependencies_names_to_update) or {"pypi": []}
    # merge new and old dependencies
    new_deps['pypi'] += dependencies_up_to_date
    return new_deps
