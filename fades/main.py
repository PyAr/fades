# Copyright 2014-2015 Facundo Batista, Nicolás Demarchi
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

from fades import parsing, logger, attribs
from fades.pipmanager import PipManager
from fades.envbuilder import FadesEnvBuilder
from fades.helpers import is_version_satisfied


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


def _manage_dependencies(manager, requested_deps, previous_deps):
    """Decide the action to take for the dependencies of a repo.

    Note that it will change the requested_deps version accordingly to
    what was really installed.
    """
    for dependency, requested_data in requested_deps.items():
        requested_version = requested_data['version']
        try:
            previous_data = previous_deps[dependency]
        except KeyError:
            # this dependency wasn't isntalled before!
            manager.install(dependency, requested_version)
        else:
            # dependency installed before... do action only on version not satisfied by current
            if not is_version_satisfied(previous_data['version'], requested_version):
                manager.update(dependency, requested_version)

        # always store the installed dependency, as in the future we'll want to react
        # based on what is installed, not what used requested (remember that user may
        # request >, >=, etc!)
        requested_data['version'] = manager.get_version(dependency)

    for dependency in set(previous_deps) - set(requested_deps):
        manager.remove(dependency)


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
    requested_deps = parsing.parse_file(child_program)

    # start the attributes manager
    xattrs = attribs.XAttrsManager(child_program)

    if 'env_path' not in xattrs:
        l.info('%s has not a virtualenv yet. Creating one', child_program)
        # create virtualenv
        env = FadesEnvBuilder()
        env_path, env_bin_path, pip_installed = env.create_env()
        xattrs['env_path'] = env_path
        xattrs['env_bin_path'] = env_bin_path
        xattrs['pip_installed'] = pip_installed

    # compare and install deps
    previous_deps = xattrs.get('requested_deps', {})
    for repo in requested_deps.keys():
        if repo == parsing.Repo.pypi:
            mgr = PipManager(xattrs['env_bin_path'], pip_installed=xattrs['pip_installed'])
        else:
            l.warning("Install from %s not implemented", repo)
            continue

        repo_requested = requested_deps[repo]
        repo_previous = previous_deps.get(repo, {})
        l.debug("Managing dependencies for repo %r: requested=%s previous=%s",
                repo, repo_requested, repo_previous)
        _manage_dependencies(mgr, repo_requested, repo_previous)
        l.debug("Resulted dependencies: %s", repo_requested)

    # save/update xattr at this point, as the repo requested information may have changed
    # in the installation process
    xattrs['requested_deps'] = requested_deps
    xattrs.save()

    # run forest run!!
    l.debug("Calling the child Python program %r with options %s", child_program, child_options)
    python_exe = os.path.join(xattrs['env_bin_path'], "python3")
    rc = subprocess.call([python_exe, child_program] + child_options)
    if rc:
        l.debug("Child process not finished correctly: returncode=%d", rc)
