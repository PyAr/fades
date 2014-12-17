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

"""Logging set up."""

import logging
import logging.handlers


def set_up(level):
    """Set up the logging."""
    # all to the syslog
    logger = logging.getLogger('fades')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.SysLogHandler(address='/dev/log')
    logger.addHandler(handler)
    formatter = logging.Formatter("%(name)s[%(process)d]: %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)

    # and to the stdout
    handler = logging.StreamHandler()
    handler.setLevel(level)
    logger.addHandler(handler)
    formatter = logging.Formatter("*** fades ***  %(asctime)s  %(name)-18s %(levelname)-8s %(message)s")
    handler.setFormatter(formatter)

    return logger
