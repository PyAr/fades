# Copyright 2014 Facundo Batista, Nicolás Demarchi
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

"""Main 'fades' modules."""

import logging
import os
import subprocess
import sys

from fades.envbuilder import FadesEnvBuilder
from fades import parsing, logger


def _parse_argv(argv):
    """Ad-hoc argv parsing for the complicated rules.

    As fades is a program that executes programs, at first there is the
    complexity of deciding which of the parameters are for fades and which
    ones are for the executed child program. For this, we decided that after
    fades itself, everything starting with a "-" is a parameter for fade,
    then the rest is for child program.

    Also, it happens that if you pass several parameters to fades when
    calling it using the "!#/usr/bin/fades" magic at the beginning of a file,
    all the parameters you put there come as a single string.
    """
    # get a copy, as we'll destroy this; in the same move ignore first
    # parameter that is the name of fades executable itself
    argv = argv[1:]

    fades_options = []
    while argv and argv[0][0] == '-':
        fades_options.extend(argv.pop(0).split())
    if not argv:
        return fades_options, "", []

    child_program = argv[0]
    return fades_options, child_program, argv[1:]


def go(version, argv):
    """Make the magic happen."""
    fades_options, child_program, child_options = _parse_argv(sys.argv)
    verbose = "-v" in fades_options or "--verbose" in fades_options
    quiet = "-q" in fades_options or "--quiet" in fades_options
    if verbose:
        log_level = logging.DEBUG
    elif quiet:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO

    # set up logger and dump basic version info
    l = logger.set_up(log_level)
    l.debug("Running Python %s on %r", sys.version_info, sys.platform)
    l.debug("Starting fades v. %s", version)

    if verbose and quiet:
        l.warning("Overriding 'quiet' option ('verbose' also requested)")

    deps = parsing.parse_file(child_program)
    env = FadesEnvBuilder(deps)
    env.create_and_install()

    l.debug("Calling the child Python program %r with options %s",
             child_program, child_options)
    python_exe = os.path.join(env.env_bin_path, "python3")
    subprocess.check_call([python_exe, child_program] + child_options)
