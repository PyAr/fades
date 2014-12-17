# Copyright 2014 Facundo Batista, Nicolás Demarchi
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License version 3, as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranties of MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
# For further info, check  https://github.com/PyAr/fades

"""Main 'fades' modules."""

import os
import sys
import logging
import subprocess

from fades import parsing, logger
from fades.pipmanager import PipManager
from fades.envbuilder import FadesEnvBuilder
from fades.helpers import save_xattr, get_xattr, update_xattr


def _parse_argv(argv):
    """Ad-hoc argv parsing for the complicated rules.

    As fades is a program that executes programs, at first there is the complexity of deciding which of the
    parameters are for fades and which ones are for the executed child program. For this, we decided that after
    fades itself, everything starting with a "-" is a parameter for fade, then the rest is for child program.

    Also, it happens that if you pass several parameters to fades when calling it using the "!#/usr/bin/fades"
    magic at the beginning of a file, all the parameters you put there come as a single string."""
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

    # parse file and get deps
    parsed_deps = parsing.parse_file(child_program)

    # get xattr
    installed_deps, env_path, env_bin_path = get_xattr(child_program)

    if env_path is None:
        #create virtualenv
        env = FadesEnvBuilder()
        env_path, env_bin_path = env.create_env()

    #compare deps
    if installed_deps is not None:
        pass
        deps = []
        #fixme: Compare parsed_deps with installed_deps and build de deps list regard the result of comparing.
    else:
        deps = parsed_deps

    if len(deps) > 0:
        pip_mng = PipManager(env_bin_path, pip_installed=env.pip_installed)
        for dependency in deps:
            if dependency['repo'] == parsing.Repo.pypi:
                pip_mng.handle_deps(dependency)
                if dependency['version'] is None:
                    # if version is not specified. store the installed version.
                    dependency['version'] = pip_mng.get_version(dependency)
            else:
                logger.warning("Install from %s not implemented", dependency['repo'])

        save_xattr(child_program, deps, env_path, env_bin_path)

    l.debug("Calling the child Python program %r with options %s", child_program, child_options)
    python_exe = os.path.join(env_bin_path, "python3")
    # run forest run!!
    subprocess.check_call([python_exe, child_program] + child_options)
