# Copyright 2018 Facundo Batista, Nicolás Demarchi
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

"""Tests for logger related code."""
import logging
from fades.logger import set_up as log_set_up


def test_salutes_info(caplog):
    """Check saluting handler."""
    logger = log_set_up(verbose=False, quiet=True)
    logger.warning("test foobar")

    assert caplog.record_tuples == [
        ('fades', logging.INFO, "Hi! This is fades 8.1, automatically managing your dependencies"),
        ('fades', logging.WARN, 'test foobar')
    ]


def test_salutes_once(caplog):
    logger = log_set_up(verbose=False, quiet=False)
    logger.info("test foobar")

    # again, check this time it didn't salute, but original log message is ok
    caplog.set_level(logging.INFO, logger='fades')
    logger.info("test barbarroja")

    assert caplog.record_tuples == [
        ('fades', logging.INFO, "Hi! This is fades 8.1, automatically managing your dependencies"),
        ('fades', logging.INFO, 'test foobar'),
        ('fades', logging.INFO, 'test barbarroja'),
    ]
