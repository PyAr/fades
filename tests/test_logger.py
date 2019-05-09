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

    assert "INFO" == caplog.records[0].levelname
    assert "Hi! This is fades" in caplog.records[0].msg

    assert "WARNING" == caplog.records[1].levelname
    assert 'test foobar' in caplog.records[1].msg


def test_salutes_once(caplog):
    logger = log_set_up(verbose=False, quiet=False)
    logger.info("test foobar")

    assert "INFO" == caplog.records[0].levelname
    assert "Hi! This is fades" in caplog.records[0].msg
    assert "INFO" == caplog.records[1].levelname
    assert 'test foobar' in caplog.records[1].msg

    # again, check this time it didn't salute, but original log message is ok
    caplog.set_level(logging.INFO, logger='fades')
    logger.info("test barbarroja")

    assert "Hi! This is fades" not in caplog.records[2].msg
    assert "test barbarroja" in caplog.records[2].msg
    assert "INFO" == caplog.records[2].levelname
