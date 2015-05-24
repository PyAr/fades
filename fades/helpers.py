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
import logging
import subprocess

logger = logging.getLogger(__name__)


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


def which(file):
    for path in os.environ["PATH"].split(":"):
        if os.path.exists("{}/{}".format(path, file)):
                return "{}/{}".format(path, file)

    return None


def get_interpreter_version(requested_version):
    """ Return a sanitized interpreter and compare if
    this is equal that the current one. """
    logger.debug('Getting interpreter version for: %s', requested_version)

    if requested_version is None:
        interpreter = sys.executable.split('/')[-1]
        logger.debug('interpreter version is: %s and it is the same as fades.', interpreter)
        return (interpreter, True)

    if not any([char.isdigit() for char in requested_version]):
        if not '/' in requested_version:
            requested_version = which(requested_version)
        requested_version = os.readlink(requested_version)

    major, minor, micro = sys.version_info[:3]
    current_version = 'python{}.{}.{}'.format(major, minor, micro)
    requested_version = requested_version.split('/')[-1]
    is_current = requested_version == current_version[:len(requested_version)]
    logger.debug('Interpreter=%s. It is the same as fades?=%s', requested_version, is_current)
    return (requested_version, is_current)
