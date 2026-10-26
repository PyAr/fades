# Copyright 2016-2026 Facundo Batista, Nicolás Demarchi
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
from unittest.mock import patch

import pytest

from fades import file_options


@pytest.fixture
def argparser():
    """Build the argument parser used in the tests."""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--foo', action='store_true')
    parser.add_argument('-b', '--bar', action='store')
    parser.add_argument('-d', '--dependency', action='append')
    parser.add_argument('positional', nargs='?', default=None)
    return parser


@patch("fades.file_options.CONFIG_FILES", ('/foo/none', '/dev/null'))
def test_no_config_files(argparser):
    args = argparser.parse_args([])
    result = file_options.options_from_file(args)

    assert args == result
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
@patch("configparser.ConfigParser.items")
def test_single_config_file_no_cli(mocked_parser, argparser):
    mocked_parser.return_value = [('foo', 'true'), ('bar', 'hux')]
    args = argparser.parse_args(['positional'])
    result = file_options.options_from_file(args)

    assert result.foo
    assert result.bar == 'hux'
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
@patch("configparser.ConfigParser.items")
def test_single_config_file_with_cli(mocked_parser, argparser):
    mocked_parser.return_value = [('foo', 'false'), ('bar', 'hux'), ('no_in_cli', 'testing')]
    args = argparser.parse_args(['--foo', '--bar', 'other', 'positional'])
    result = file_options.options_from_file(args)

    assert result.foo
    assert result.bar == 'other'
    assert result.no_in_cli == 'testing'
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
@patch("configparser.ConfigParser.items")
def test_single_config_file_with_mergeable(mocked_parser, argparser):
    mocked_parser.return_value = [('dependency', 'two')]
    args = argparser.parse_args(
        ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
    result = file_options.options_from_file(args)

    assert result.foo
    assert result.bar == 'other'
    assert result.dependency == ['one', 'two']
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini',))
@patch("configparser.ConfigParser.items")
def test_single_config_file_complex_mergeable(mocked_parser, argparser):
    mocked_parser.return_value = [('dependency', 'requests>=2.1,<2.8,!=2.6.5')]
    args = argparser.parse_args(
        ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
    result = file_options.options_from_file(args)

    assert result.foo
    assert result.bar == 'other'
    assert result.dependency == ['one', 'requests>=2.1,<2.8,!=2.6.5']
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini'))
@patch("configparser.ConfigParser.items")
def test_two_config_file_with_mergeable(mocked_parser, argparser):
    mocked_parser.side_effect = [
        [('dependency', 'two')],
        [('dependency', 'three')],
    ]
    args = argparser.parse_args(
        ['--foo', '--bar', 'other', '--dependency', 'one', 'positional'])
    result = file_options.options_from_file(args)

    assert result.foo
    assert result.bar == 'other'
    assert result.dependency == ['one', 'two', 'three']
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini'))
@patch("configparser.ConfigParser.items")
def test_two_config_file_with_booleans(mocked_parser, argparser):
    mocked_parser.side_effect = [
        [('foo', 'true')],
        [('foo', 'false')],
    ]
    args = argparser.parse_args([])
    result = file_options.options_from_file(args)

    assert not result.foo
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini'))
@patch("configparser.ConfigParser.items")
def test_two_config_file_override_by_cli(mocked_parser, argparser):
    mocked_parser.side_effect = [
        [('bar', 'no_this')],
        [('bar', 'no_this_b')],
    ]
    args = argparser.parse_args(['--bar', 'this'])
    result = file_options.options_from_file(args)

    assert result.bar == 'this'
    assert isinstance(args, argparse.Namespace)


@patch("fades.file_options.CONFIG_FILES", ('mock.ini', 'mock2.ini', 'mock3.ini'))
@patch("configparser.ConfigParser.items")
def test_three_config_file_override(mocked_parser, argparser):
    mocked_parser.side_effect = [
        [('bar', 'no_this')],
        [('bar', 'neither_this')],
        [('bar', 'this')],
    ]
    args = argparser.parse_args([])
    result = file_options.options_from_file(args)

    assert result.bar == 'this'
    assert isinstance(args, argparse.Namespace)
