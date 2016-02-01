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
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from fades import file_options


#    def test_simple(self):
#        parsed = parsing._parse_content(io.StringIO("""
#            import time
#            import foo    # fades.pypi
#        """))
#        self.assertDictEqual(parsed, {REPO_PYPI: [get_req('foo')]})
#

class GetParsersTestCase(unittest.TestCase):
    """Check file_options.get_parsers()."""

    def test_no_config_file_present(self):
        parsers = file_options.get_parsers(config_files={'none': "/foo/bar"})

        self.assertIsNone(parsers)

    def test_empty_config_files(self):
        config_file_1 = NamedTemporaryFile()
        config_file_2 = NamedTemporaryFile()

        parsers = file_options.get_parsers([config_file_1.name, config_file_2.name])

        config_file_1.close()
        config_file_2.close()

        self.assertIsNone(parsers)

    def test_read_corrupted_config_file(self):
        with NamedTemporaryFile() as corrupted:
            corrupted.write(b"""
                            [fades]
                            foofoo;1
                            """)
            corrupted.seek(0)
            with self.assertRaises(Exception):
                file_options.get_parsers([corrupted.name])


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

    @patch("fades.file_options.get_parsers")
    def test_no_parsers(self, mock_get_parsers):
        mock_get_parsers.return_value = None
        args = self.argparser.parse_args(['positional'])
        result = file_options.options_from_file(args)

        self.assertEqual(args, result)
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.get_parsers")
    def test_single_config_file_no_cli(self, mock_get_parsers):
        parsed_args = {'foo': 'true', 'bar': 'hux'}
        mock_get_parsers.return_value = [self.build_parser(parsed_args)]
        args = self.argparser.parse_args(['positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'hux')
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.get_parsers")
    def test_single_config_file(self, mock_get_parsers):
        parsed_args = {'foo': 'false', 'bar': 'hux', 'no_in_cli': 'testing'}
        mock_get_parsers.return_value = [self.build_parser(parsed_args)]
        args = self.argparser.parse_args(['--foo', '--bar', 'other', 'positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'other')
        self.assertEqual(result.no_in_cli, 'testing')
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.get_parsers")
    def test_single_config_file_with_mergeable(self, mock_get_parsers):
        parsed_args = {'dependency': 'two'}
        mock_get_parsers.return_value = [self.build_parser(parsed_args)]
        args = self.argparser.parse_args(
            ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'other')
        self.assertEqual(result.dependency, ['one', 'two'])
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.get_parsers")
    def test_two_config_file_with_mergeable(self, mock_get_parsers):
        parsed_args_a = {'dependency': 'two'}
        parsed_args_b = {'dependency': 'three'}
        mock_get_parsers.return_value = [self.build_parser(parsed_args_a),
                                         self.build_parser(parsed_args_b)]
        args = self.argparser.parse_args(
            ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
        result = file_options.options_from_file(args)

        self.assertTrue(result.foo)
        self.assertEqual(result.bar, 'other')
        self.assertEqual(result.dependency, ['one', 'two', 'three'])
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.get_parsers")
    def test_two_config_file_override_by_cli(self, mock_get_parsers):
        parsed_args_a = {'bar': 'no_this'}
        parsed_args_b = {'bar': 'no_this_b'}
        mock_get_parsers.return_value = [self.build_parser(parsed_args_a),
                                         self.build_parser(parsed_args_b)]
        args = self.argparser.parse_args(['--bar', 'this'])
        result = file_options.options_from_file(args)

        self.assertEqual(result.bar, 'this')
        self.assertIsInstance(args, argparse.Namespace)

    @patch("fades.file_options.get_parsers")
    def test_two_config_file_override(self, mock_get_parsers):
        parsed_args_a = {'bar': 'this'}
        parsed_args_b = {'bar': 'no_this'}
        parsed_args_c = {'bar': 'neither_this'}
        mock_get_parsers.return_value = [self.build_parser(parsed_args_a),
                                         self.build_parser(parsed_args_b),
                                         self.build_parser(parsed_args_c)]
        args = self.argparser.parse_args([])
        result = file_options.options_from_file(args)

        self.assertEqual(result.bar, 'this')
        self.assertIsInstance(args, argparse.Namespace)
