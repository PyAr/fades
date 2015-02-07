# Copyright 2015 Facundo Batista, Nicolás Demarchi
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

"""The manager for the attributes to be stored."""

import errno
import logging
import os
import pickle

logger = logging.getLogger(__name__)


class XAttrsManager(dict):
    """Manager for the extended attributes in a file.

    It presents the interface of a dictionary, with an extra method: save.
    """

    _namespace = 'user.fades'

    def __init__(self, filepath):
        self._filepath = filepath
        self._virgin = False

        logger.debug('Getting fades info from xattr for %r', filepath)
        try:
            data = pickle.loads(os.getxattr(filepath, self._namespace))
        except OSError as error:
            self._virgin = True
            if error.errno != errno.ENODATA:
                # something bad happened (other than the simple 'no data' case)
                logger.error('Error getting xattr from %r: %s(%s)',
                             filepath, error.__class__.__name__, error)
        else:
            self.update(data)
        logger.debug('Xattr obtained: %s', self)

    def save(self):
        """Save current data to disk."""
        logger.debug('Saving xattr info: %s', self)
        data = pickle.dumps(self)

        flag = os.XATTR_CREATE if self._virgin else os.XATTR_REPLACE
        try:
            os.setxattr(self._filepath, self._namespace, data, flags=flag)
        except OSError as error:
            logger.error('Error saving xattr: %s', error)
