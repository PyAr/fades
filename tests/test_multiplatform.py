# Copyright 2016-2026 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General
# Public License version 3, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

"""Tests for the helpers in multiplatform."""

import threading
import time

import pytest

from fades.multiplatform import filelock


class LockChecker(threading.Thread):
    """Helper to check the lock in other thread.

    The time.sleep() in the middle of the process is for time.time()
    granularity in different platforms to not mess our tests.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.in_lock = self.post_work = None
        self.middle_work = threading.Event()
        super().__init__()

    def run(self):
        with filelock(self.filepath):
            time.sleep(.01)
            self.in_lock = time.time()
            self.middle_work.wait()
            self.post_work = time.time()


@pytest.fixture
def lock_path(tmp_path):
    """Provide a path for the lock file."""
    return tmp_path / "test_filelock"


def wait(lock_checker, attr_name):
    """Wait at most a second for the LockChecker to end."""
    for i in range(10):
        attr = getattr(lock_checker, attr_name)
        if attr is not None:
            # ended!
            return
        time.sleep(.3)
    pytest.fail("LC didnt end: %s" % (lock_checker,))


def test_lock_alone(lock_path):
    lc = LockChecker(lock_path)
    lc.start()
    lc.middle_work.set()
    wait(lc, 'post_work')


def test_lock_intermixed(lock_path):
    lc1 = LockChecker(lock_path)
    lc1.start()
    wait(lc1, 'in_lock')

    lc2 = LockChecker(lock_path)
    lc2.start()

    lc1.middle_work.set()
    wait(lc1, 'post_work')

    lc2.middle_work.set()
    wait(lc2, 'post_work')

    # check LC 2 waited to enter
    assert lc2.in_lock > lc1.post_work


def test_lock_exploding(lock_path):
    # get the lock and explode in the middle (then ignore the blast)
    try:
        with filelock(lock_path):
            raise ValueError("pumba")
    except ValueError:
        pass

    # get the lock again
    with filelock(lock_path):
        pass
