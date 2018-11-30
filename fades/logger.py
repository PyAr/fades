# Copyright 2014-2018 Facundo Batista, Nicolás Demarchi
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
import os.path

from fades._version import __version__


FMT_SIMPLE = "*** fades ***  %(asctime)s  %(levelname)-8s %(message)s"
FMT_DETAILED = "*** fades ***  %(asctime)s  %(name)-18s %(levelname)-8s %(message)s"
FMT_SYSLOG = "[%(process)d] %(name)-18s %(levelname)-8s %(message)s"

SALUTATION = "Hi! This is fades {}, automatically managing your dependencies".format(__version__)


class SalutingStreamHandler(logging.StreamHandler):
    """A handler that salutes once before polluting user screen.

    Note that the salutation is done in INFO level, to respect "verbose" modifiers.
    """

    def __init__(self, logger):
        """Init."""
        super().__init__()
        self._already_saluted = False
        self._logger = logger

    def emit(self, record):
        """Call father's emit, but salute first (just once)."""
        if not self._already_saluted:
            self._already_saluted = True
            self._logger.info(SALUTATION)
        super().emit(record)


def set_up(verbose, quiet):
    """Set up the logging."""
    logger = logging.getLogger('fades')
    logger.setLevel(logging.DEBUG)

    # select logging level according to user desire; also use a simpler
    # formatting for non-verbose logging
    if verbose:
        log_level = logging.DEBUG
        log_format = FMT_DETAILED
    elif quiet:
        log_level = logging.WARNING
        log_format = FMT_SIMPLE
    else:
        log_level = logging.INFO
        log_format = FMT_SIMPLE

    # all to the stdout
    handler = SalutingStreamHandler(logger)
    handler.setLevel(log_level)
    logger.addHandler(handler)
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)

    # and to the syslog
    for syslog_path in ('/dev/log', '/var/run/syslog'):
        if not os.path.exists(syslog_path):
            continue
        try:
            handler = logging.handlers.SysLogHandler(address=syslog_path)
        except Exception:
            # silently ignore that the user doesn't have a syslog active; can
            # see all the info with "-v" anyway
            pass
        else:
            logger.addHandler(handler)
            formatter = logging.Formatter(FMT_SYSLOG)
            handler.setFormatter(formatter)
            break

    return logger
