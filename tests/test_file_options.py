# Copyright 2016 Facundo Batista, Nicolás Demarchi
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

"""Tests for file_options."""

import argparse
import unittest
from configparser import ConfigParser
from unittest.mock import patch

from fades import file_options


class OptionsFileTestCase(unittest.TestCase):
    """Check file_options.options_from_file()."""

    def setUp(self):
        self.argparser = argparse.ArgumentParser()
        self.argparser.add_argument
        self.argparser.add_argument('-f', '--foo', action='store_true')
        self.argparser.add_argument('-b', '--bar', action='store')
        self.argparser.add_argument('-d', '--dependency', action='append')
        self.argparser.add_argument('positional', nargs='?', default=None)

    def build_parser(self, args):
        config_parser = ConfigParser()
        config_parser['fades'] = args
        return config_parser

    @patch("fades.file_options.CONFIG_FILES", ('/foo/none', '/dev/null'))
    def test_no_config_files(self):
        args = self.argparser.parse_args([])
        result = file_options.options_from_file(args)

        self.assertEqual(args, result)
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
    @patch("configparser.ConfigParser.items")
    def test_single_config_file_no_cli(self, mocked_parser):
        mocked_parser.return_value = [('foo', 'true'), ('bar', 'hux')]
        args = self.argparser.parse_args(['positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'hux')
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
    @patch("configparser.ConfigParser.items")
    def test_single_config_file_with_cli(self, mocked_parser):
        mocked_parser.return_value = [('foo', 'false'), ('bar', 'hux'), ('no_in_cli', 'testing')]
        args = self.argparser.parse_args(['--foo', '--bar', 'other', 'positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'other')
        self.assertEqual(result.no_in_cli, 'testing')
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
    @patch("configparser.ConfigParser.items")
    def test_single_config_file_with_mergeable(self, mocked_parser):
        mocked_parser.return_value = [('dependency', 'two')]
        args = self.argparser.parse_args(
            ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'other')
        self.assertEqual(result.dependency, ['one', 'two'])
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
    @patch("configparser.ConfigParser.items")
    def test_single_config_file_complex_mergeable(self, mocked_parser):
        mocked_parser.return_value = [('dependency', 'requests>=2.1,<2.8,!=2.6.5')]
        args = self.argparser.parse_args(
            ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'other')
        self.assertEqual(result.dependency, ['one', 'requests>=2.1,<2.8,!=2.6.5'])
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini'))
    @patch("configparser.ConfigParser.items")
    def test_two_config_file_with_mergeable(self, mocked_parser):
        mocked_parser.side_effect = [
            [('dependency', 'two')],
            [('dependency', 'three')],
        ]
        args = self.argparser.parse_args(
            ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'other')
        self.assertEqual(result.dependency, ['one', 'two', 'three'])
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini'))
    @patch("configparser.ConfigParser.items")
    def test_two_config_file_with_booleans(self, mocked_parser):
        mocked_parser.side_effect = [
            [('foo', 'true')],
            [('foo', 'false')],
        ]
        args = self.argparser.parse_args([])
        result = file_options.options_from_file(args)

        self.assertFalse(result.foo)
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini'))
    @patch("configparser.ConfigParser.items")
    def test_two_config_file_override_by_cli(self, mocked_parser):
        mocked_parser.side_effect = [
            [('bar', 'no_this')],
            [('bar', 'no_this_b')],
        ]
        args = self.argparser.parse_args(['--bar', 'this'])
        result = file_options.options_from_file(args)

        self.assertEqual(result.bar, 'this')
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini', 'mock3.ini'))
    @patch("configparser.ConfigParser.items")
    def test_three_config_file_override(self, mocked_parser):
        mocked_parser.side_effect = [
            [('bar', 'no_this')],
            [('bar', 'neither_this')],
            [('bar', 'this')],
        ]
        args = self.argparser.parse_args([])
        result = file_options.options_from_file(args)

        self.assertEqual(result.bar, 'this')
        self.assertIsInstance(args, argparse.Namespace)
