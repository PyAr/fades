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

"""Parse fades options from config files."""

import logging
from configparser import ConfigParser

from fades.helpers import get_confdir

logger = logging.getLogger(__name__)

CONFIG_FILES = ("/etc/fades/fades.ini", get_confdir(), ".fades.ini")


MERGEABLE_CONFIGS = ("dependency", "pip_options", "virtualenv-options")


def get_parsers(config_files=CONFIG_FILES):
    """Search for config files return a ConfigParser for each one.

    Return a Configparser with all files merged in the first position and one
    Configparser for each file ordered by priority.
    """
    parser = ConfigParser()
    existing_files = parser.read(config_files)
    logger.debug("Found these config files: %s", existing_files)
    if existing_files and parser.sections():
        parsers = []
        parsers.append(parser)  # first parser is the one with all the settings.
        for config_file in existing_files:
            single_parser = ConfigParser()
            single_parser.read(config_file)
            if parser.sections():  # avoid empty files.
                parsers.append(single_parser)
            return parsers


def merge_parsers(parsers):
    """Merge options in MERGEABLE_CONFIGS in a uniq ConfigParser."""
    merged_parser = parsers[0]
    for parser in parsers[1:]:
        # list of parsers is ordered by priority, last one is highest.
        items = parser.items('fades')
        for key, value in items:
            if key in MERGEABLE_CONFIGS:
                new_value = "{};{}".format(merged_parser.get('fades', key), value)
                merged_parser.set('fades', key, new_value)
    return merged_parser


def options_from_file(args):
    """Get a argparse.Namespace and return it updated with options from config files.

    Config files will be parsed with priority equal to his order in CONFIG_FILES.
    """
    logger.debug("updating options from config files")
    parsers = get_parsers()
    if parsers is None:
        return args
    parser = merge_parsers(parsers)
    config_items = parser['fades']
    for config_key, config_value in config_items.items():
        if config_value in ['true', 'false']:
            config_value = config_items.getboolean(config_key)
        if config_key in MERGEABLE_CONFIGS:
            current_value = getattr(args, config_key, [])
            if current_value is None:
                current_value = []
            config_value = config_value.split(';')
            new_value = current_value + config_value
            logger.debug("Updating %s, from %s to %s", config_key, current_value, new_value)
            setattr(args, config_key, new_value)
        if not getattr(args, config_key, False):
            # By default all 'store-true' arguments are False. So we only
            # override them if they are False. If they are True means that the
            # user is setting those on the CLI.
            setattr(args, config_key, config_value)
            logger.debug("updating %s to %s from file settings", config_key, config_value)
    return args
