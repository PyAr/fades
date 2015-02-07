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

import logging
import subprocess

logger = logging.getLogger(__name__)


def logged_exec(cmd):
    """Execute a command, redirecting the output to the log."""
    logger = logging.getLogger('fades.exec')
    logger.debug("Executing external command: %r", cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout:
        logger.debug(":: " + line[:-1].decode("utf8"))
    retcode = p.wait()
    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd)


def is_version_satisfied(previous, requested):
    """Decide if the previous version satisfies what is requested."""
    if requested is None:
        # don't care what we had before if nothing specific is requested
        return True

    if previous is None:
        # something requested, and no info from the past, sure it's different
        return False

    previous = previous.strip()
    requested = requested.strip()

    if requested.startswith('=='):
        req = requested[2:].strip()
        return req == previous

    if requested.startswith('>='):
        req = requested[2:].strip()
        return previous >= req

    if requested.startswith('>'):
        req = requested[1:].strip()
        return previous > req

    # no special case
    return requested == previous
