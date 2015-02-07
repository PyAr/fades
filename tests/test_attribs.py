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

"""Tests for the attribs."""

import logging.handlers
import os
import pickle
import tempfile
import unittest

from fades.attribs import XAttrsManager


class SetupLogChecker(logging.handlers.MemoryHandler):
    """A fake handler to store the records."""

    def __init__(self, test_instance, log_path):
        # init memory handler to never flush
        super(SetupLogChecker, self).__init__(capacity=100000, flushLevel=1000)
        self.test_instance = test_instance
        test_instance.assertLogged = self._check

        # hook in the logger
        logger = logging.getLogger(log_path)
        logger.addHandler(self)
        logger.setLevel(logging.DEBUG)
        self.setLevel(logging.DEBUG)

    def _check(self, level, *tokens):
        """Check if the the different tokens were logged in one record."""
        for record in self.buffer:
            if record.levelno == level:
                msg = record.getMessage()
                if all(token in msg for token in tokens):
                    return

        # didn't exit, all tokens are not present in the same record
        self.test_instance.fail("Tokens %s were not logged: %s" % (
            tokens, [(r.levelname, r.getMessage()) for r in self.buffer]))


class AttribsManagingTestCase(unittest.TestCase):
    """Basic functionality tests."""

    def setUp(self):
        _, self.tempfile = tempfile.mkstemp(prefix="test-temp-file", dir='.')
        self.addCleanup(os.remove, self.tempfile)
        SetupLogChecker(self, 'fades.attribs')

    def test_load_empty(self):
        xam = XAttrsManager(self.tempfile)
        self.assertEqual(len(xam), 0)
        self.assertLogged(logging.DEBUG, 'Getting fades info', self.tempfile)

    def test_load_data(self):
        # save it "by hand"
        d = dict(foo='bar', baz=123)
        os.setxattr(self.tempfile, XAttrsManager._namespace, pickle.dumps(d), flags=os.XATTR_CREATE)

        # read it
        xam = XAttrsManager(self.tempfile)
        self.assertEqual(xam['foo'], 'bar')
        self.assertEqual(xam['baz'], 123)

    def test_load_failure(self):
        # read a file that doesn't exist, should be empty (don't crash) but log the problem
        xam = XAttrsManager('bad')
        self.assertEqual(len(xam), 0)
        self.assertLogged(logging.ERROR, 'Error getting xattr', 'bad')

    def test_save(self):
        # save it
        xam = XAttrsManager(self.tempfile)
        xam['foo'] = 'bar'
        xam['baz'] = 123
        xam.save()

        # check
        d = pickle.loads(os.getxattr(self.tempfile, XAttrsManager._namespace))
        self.assertEqual(d, dict(foo='bar', baz=123))
        self.assertLogged(logging.DEBUG, 'Saving xattr info')

    def test_save_failure(self):
        # save after changing the filepath, so it will fail
        xam = XAttrsManager(self.tempfile)
        xam._filepath = 'bad'
        xam.save()

        # shouldn't crash, but log
        self.assertLogged(logging.ERROR, 'Error saving xattr', 'bad')

    def test_update(self):
        # save it "by hand"
        d = dict(foo='bar', baz=123)
        os.setxattr(self.tempfile, XAttrsManager._namespace, pickle.dumps(d), flags=os.XATTR_CREATE)

        # load, change, save it
        xam = XAttrsManager(self.tempfile)
        xam['foo'] = 'bar'
        xam['baz'] = 987
        xam['new'] = ':)'
        xam.save()

        # check
        d = pickle.loads(os.getxattr(self.tempfile, XAttrsManager._namespace))
        self.assertEqual(d, dict(foo='bar', baz=987, new=':)'))
