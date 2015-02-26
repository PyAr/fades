# Copyright 2014-2015 Facundo Batista, Nicolás Demarchi
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

"""Main 'fades' modules."""

import os
import sys
import logging
import subprocess

from fades import parsing, logger, cache, helpers, envbuilder


USAGE = """
Usage:  fades [<fades_options>] child_program [<child_program_options>]

    All fades options are optional:
        -h|--help:    show this help and quit
        -V|--version: show version and info about the system
        -v|--verbose: send all internal debugging lines to stderr, which
                      may be very useful if any problem arises.
        -q|--quiet:   don't show anything (unless it has a real problem),
                      so the original script stderr is not polluted at all.

    The "child program" is the script that fades will execute. It's a
    mandatory parameter, the first thing received by fades that is not
    a parameter.

    The child program options (everything after the child program) are
    parameters passed as is to the child program.
"""


def _parse_argv(argv):
    """Ad-hoc argv parsing for the complicated rules.

    As fades is a program that executes programs, at first there is the complexity of
    deciding which of the parameters are for fades and which ones are for the executed
    child program. For this, we decided that after fades itself, everything starting with
    a "-" is a parameter for fade, then the rest is for child program.

    Also, it happens that if you pass several parameters to fades when calling it using
    the "!#/usr/bin/fades" magic at the beginning of a file, all the parameters you put
    there come as a single string."""

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

    # validate input, parameters, and support some special options
    if "-V" in fades_options or "--version" in fades_options:
        print("Running 'fades' version", version)
        print("    Python:", sys.version_info)
        print("    System:", sys.platform)
        sys.exit()
    if "-h" in fades_options or "--help" in fades_options:
        print(USAGE)
        sys.exit()
    if not child_program:
        print("ERROR: the 'child program' is mandatory.")
        print(USAGE)
        sys.exit()

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

    # parse file and get deps
    requested_deps = parsing.parse_file(child_program)

    # start the virtualenvs manager
    venvscache = cache.VEnvsCache(os.path.join(helpers.get_basedir(), 'venvs.idx'))
    venv_data = venvscache.get_venv(requested_deps)
    if venv_data is None:
        venv_data, installed = envbuilder.create_venv(requested_deps)
        # store this new venv in the cache
        venvscache.store(installed, venv_data)

    # run forest run!!
    l.debug("Calling the child Python program %r with options %s", child_program, child_options)
    python_exe = os.path.join(venv_data['env_bin_path'], "python3")
    rc = subprocess.call([python_exe, child_program] + child_options)
    if rc:
        l.debug("Child process not finished correctly: returncode=%d", rc)
