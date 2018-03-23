# Copyright 2016 Facundo Batista, Nicolás Demarchi
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

import os
import threading
import time
import unittest

from fades.multiplatform import filelock


class LockChecker(threading.Thread):
    """Helper to check the lock in other thread.

    The time.sleep() in the middle of the process is for time.time()
    granularity in different platforms to not mess our tests.
    """

    def __init__(self, filepath):
        self.filepath = filepath
        self.pre_lock = self.in_lock = self.post_work = None
        self.middle_work = threading.Event()
        super().__init__()

    def run(self):
        self.pre_lock = time.time()
        time.sleep(.01)
        with filelock(self.filepath):
            self.in_lock = time.time()
            self.middle_work.wait()
            time.sleep(.01)
            self.post_work = time.time()


class LockCacheTestCase(unittest.TestCase):
    """Tests for the locking utility."""

    def setUp(self):
        self.test_path = "test_filelock"

    def tearDown(self):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)

    def wait(self, lock_checker, attr_name):
        """Wait at most a second for the LockChecker to end."""
        for i in range(10):
            attr = getattr(lock_checker, attr_name)
            if attr is not None:
                # ended!
                return
            time.sleep(.3)
        self.fail("LC didnt end: %s" % (lock_checker,))

    def test_lock_alone(self):
        lc = LockChecker(self.test_path)
        lc.start()
        lc.middle_work.set()
        self.wait(lc, 'post_work')

    def test_lock_intermixed(self):
        lc1 = LockChecker(self.test_path)
        lc1.start()
        self.wait(lc1, 'in_lock')

        lc2 = LockChecker(self.test_path)
        lc2.start()

        lc1.middle_work.set()
        self.wait(lc1, 'post_work')

        lc2.middle_work.set()
        self.wait(lc2, 'post_work')

        # check LC 2 waited to enter
        self.assertGreater(lc2.in_lock, lc1.post_work)

    def test_lock_exploding(self):
        # get the lock and explode in the middle (then ignore the blast)
        try:
            with filelock(self.test_path):
                raise ValueError("pumba")
        except ValueError:
            pass

        # get the lock again
        with filelock(self.test_path):
            pass
