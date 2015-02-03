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
import errno
import pickle
import logging
import subprocess

logger = logging.getLogger(__name__)

FADES_XATTR = 'user.fades'


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


def save_xattr(child_program, deps, env_path, env_bin_path, pip_installed):
    """Saves fades info into xattr"""
    logger.info('Saving fades info in xattr of %s', child_program)

    xattr = {}
    xattr['deps'] = deps
    xattr['env_path'] = env_path
    xattr['env_bin_path'] = env_bin_path
    xattr['pip_installed'] = pip_installed

    logger.debug('xattr dict == %s', xattr)

    serialized_xattr = pickle.dumps(xattr)

    try:
        os.setxattr(child_program, FADES_XATTR, serialized_xattr, flags=os.XATTR_CREATE)
    except OSError as error:
        logger.error('Error saving xattr: %s', error)


def get_xattr(child_program, return_dict=False):
    """Gets fades info from xattr"""
    logger.debug('Getting fades info from xattr for %s', child_program)
    try:
        xattr = pickle.loads(os.getxattr(child_program, FADES_XATTR))
        logger.debug('Xattr obtained from %s: %s', child_program, xattr)
        if return_dict:
            return xattr
        else:
            deps = xattr['deps']
            env_path = xattr['env_path']
            env_bin_path = xattr['env_bin_path']
            pip_installed = xattr['pip_installed']
            return deps, env_path, env_bin_path, pip_installed

    except OSError as error:
        if error.errno == errno.ENODATA:  # No data available
            logger.debug('%s has no fades xattr', child_program)
            return {}, None, None, None
        else:
            logger.error('Error getting xattr: %s', error)
            raise


def update_xattr(child_program, deps):
    """Overrite fades info into xattr"""
    logger.info('Updating xattr fades info for %s', child_program)
    logger.debug('Updating xattr with: %s', deps)
    xattr = get_xattr(child_program, return_dict=True)
    xattr['deps'] = deps

    serialized_xattr = pickle.dumps(xattr)
    try:
        os.setxattr(child_program, FADES_XATTR, serialized_xattr, flags=os.XATTR_REPLACE)
    except OSError as error:
        logger.error('Error updating xattr: %s', error)


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
