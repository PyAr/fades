# Copyright 2015 Facundo Batista, Nicolás Demarchi
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

"""The cache manager for virtualenvs."""

import json
import logging
import time

logger = logging.getLogger(__name__)


class VEnvsCache:
    """A cache for virtualenvs."""

    def __init__(self, filepath):
        self.filepath = filepath

    def _venv_match(self, installed, requirements):
        """Return True if what is installed satisfies the requirements."""
        print("======= match?", installed)
        for repo, req_deps in requirements.items():
            if repo not in installed:
                return

            inst_deps = installed[repo]
            print("======== deps?", req_deps, inst_deps)
            for dep, req_version in req_deps.items():
                if dep not in inst_deps:
                    return

                inst_version = inst_deps[dep].strip()
                req_version = req_version.strip()

                if req_version.startswith('=='):
                    req_version = req_version[2:].strip()

                elif req_version.startswith('>='):
                    req = req_version[2:].strip()
                    return inst_version >= req

                elif req_version.startswith('>'):
                    req = req_version[1:].strip()
                    return inst_version > req

                # no special case or eq from above
                return req_version == inst_version

    def _select(self, current_venvs, requirements):
        """Select which venv satisfy the received requirements."""
        logger.debug("Searching a match for reqs: %s", requirements)
        print("========== req", requirements)
        for venv in current_venvs:
            if self._venv_match(venv['installed'], requirements):
                return venv['metadata']

    def get_venv(self, requirements):
        """Find a venv that serves these requirements, if any."""
        with open(self.filepath, 'rt', encoding='utf8') as fh:
            lines = [x.strip() for x in fh]
        return self._select(lines, requirements)

    def store(self, installed_stuff, metadata):
        """Store the virtualenv metadata for the indicated installed_stuff."""
        new_content = {
            'timestamp': int(time.mktime(time.localtime())),
            'installed': installed_stuff,
            'metadata': metadata,
        }
        with open(self.filepath, 'at', encoding='utf8') as fh:
            fh.write(json.dumps(new_content) + '\n')

#    # compare and install deps
#    previous_deps = xattrs.get('requested_deps', {})
#    for repo in requested_deps.keys():
#        if repo == parsing.Repo.pypi:
#            mgr = PipManager(xattrs['env_bin_path'], pip_installed=xattrs['pip_installed'])
#        else:
#            l.warning("Install from %s not implemented", repo)
#            continue
#
#        repo_requested = requested_deps[repo]
#        repo_previous = previous_deps.get(repo, {})
#        l.debug("Managing dependencies for repo %r: requested=%s previous=%s",
#                repo, repo_requested, repo_previous)
#        _manage_dependencies(mgr, repo_requested, repo_previous)
#        l.debug("Resulted dependencies: %s", repo_requested)
#
#def _manage_dependencies(manager, requested_deps, previous_deps):
#    """Decide the action to take for the dependencies of a repo.
#
#    Note that it will change the requested_deps version accordingly to
#    what was really installed.
#    """
#    for dependency, requested_data in requested_deps.items():
#        requested_version = requested_data['version']
#        try:
#            previous_data = previous_deps[dependency]
#        except KeyError:
#            # this dependency wasn't isntalled before!
#            manager.install(dependency, requested_version)
#        else:
#            # dependency installed before... do action only on version not satisfied by current
#            if not is_version_satisfied(previous_data['version'], requested_version):
#                manager.update(dependency, requested_version)
#
#        # always store the installed dependency, as in the future we'll want to react
#        # based on what is installed, not what used requested (remember that user may
#        # request >, >=, etc!)
#        requested_data['version'] = manager.get_version(dependency)
#
#    for dependency in set(previous_deps) - set(requested_deps):
#        manager.remove(dependency)
#
#
#
#
#
#class XAttrsManager(dict):
#    """Manager for the extended attributes in a file.
#
#    It presents the interface of a dictionary, with an extra method: save.
#    """
#
#    _namespace = 'user.fades'
#
#    def __init__(self, filepath):
#        self._filepath = filepath
#        self._virgin = False
#
#        logger.debug('Getting fades info from xattr for %r', filepath)
#        try:
#            data = pickle.loads(os.getxattr(filepath, self._namespace))
#        except OSError as error:
#            self._virgin = True
#            if error.errno != errno.ENODATA:
#                # something bad happened (other than the simple 'no data' case)
#                logger.error('Error getting xattr from %r: %s(%s)',
#                             filepath, error.__class__.__name__, error)
#        else:
#            self.update(data)
#        logger.debug('Xattr obtained: %s', self)
#
#    def save(self):
#        """Save current data to disk."""
#        logger.debug('Saving xattr info: %s', self)
#        data = pickle.dumps(self)
#
#        flag = os.XATTR_CREATE if self._virgin else os.XATTR_REPLACE
#        try:
#            os.setxattr(self._filepath, self._namespace, data, flags=flag)
#        except OSError as error:
#            logger.error('Error saving xattr: %s', error)
#
