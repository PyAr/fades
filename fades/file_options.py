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
import os

from configparser import ConfigParser, NoSectionError

from fades.helpers import get_confdir

logger = logging.getLogger(__name__)

CONFIG_FILES = ("/etc/fades/fades.ini", os.path.join(get_confdir(), 'fades.ini'), ".fades.ini")

MERGEABLE_CONFIGS = ("dependency", "pip_options", "virtualenv-options")


def options_from_file(args):
    """Get a argparse.Namespace and return it updated with options from config files.

    Config files will be parsed with priority equal to his order in CONFIG_FILES.
    """
    logger.debug("updating options from config files")
    updated_from_file = []
    for config_file in CONFIG_FILES:
        logger.debug("updating from: %s", config_file)
        parser = ConfigParser()
        parser.read(config_file)
        try:
            items = parser.items('fades')
        except NoSectionError:
            continue

        for config_key, config_value in items:
            if config_value in ['true', 'false']:
                config_value = config_value == 'true'
            if config_key in MERGEABLE_CONFIGS:
                current_value = getattr(args, config_key, [])
                if current_value is None:
                    current_value = []
                current_value.append(config_value)
                setattr(args, config_key, current_value)
            if not getattr(args, config_key, False) or config_key in updated_from_file:
                # By default all 'store-true' arguments are False. So we only
                # override them if they are False. If they are True means that the
                # user is setting those on the CLI.
                setattr(args, config_key, config_value)
                updated_from_file.append(config_key)
                logger.debug("updating %s to %s from file settings", config_key, config_value)

    return args
