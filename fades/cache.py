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
import os
import time

logger = logging.getLogger(__name__)


class VEnvsCache:
    """A cache for virtualenvs."""

    def __init__(self, filepath):
        logger.debug("Using cache index: %r", filepath)
        self.filepath = filepath

    def _venv_match(self, installed, requirements):
        """Return True if what is installed satisfies the requirements.

        This method has multiple exit-points, but only for False (because
        if *anything* is not satisified, the venv is no good). Only after
        all was checked, and it didn't exit, the venv is ok so return True.
        """
        for repo, req_deps in requirements.items():
            if repo not in installed:
                # the venv doesn't even have the repo
                return False

            inst_deps = installed[repo]
            for dep, req_version in req_deps.items():
                if dep not in inst_deps:
                    # the venv doesn't even have the dependency for that repo
                    return False

                if req_version is None:
                    # no particular version requested, with the dependency present it's ok
                    continue

                inst_version = inst_deps[dep].strip()
                req_comp, req_value = req_version

                if req_comp == '==':
                    if inst_version != req_value:
                        return

                elif req_comp == '>=':
                    if inst_version < req_value:
                        return

                elif req_comp == '>':
                    if inst_version <= req_value:
                        return

                elif req_comp == '<=':
                    if inst_version > req_value:
                        return

                elif req_comp == '<':
                    if inst_version >= req_value:
                        return

                else:
                    raise ValueError("Bad requirement received: " + repr(req_version))

        # it did it through!
        return True

    def _select(self, current_venvs, requirements):
        """Select which venv satisfy the received requirements."""
        logger.debug("Searching a venv for reqs: %s", requirements)
        for venv_str in current_venvs:
            venv = json.loads(venv_str)
            if self._venv_match(venv['installed'], requirements):
                logger.debug("Found a matching venv! %s", venv)
                return venv['metadata']
        logger.debug("No matching venv found :(")

    def get_venv(self, requirements):
        """Find a venv that serves these requirements, if any."""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'rt', encoding='utf8') as fh:
                lines = [x.strip() for x in fh]
        else:
            logger.debug("Index not found, starting empty")
            lines = []
        return self._select(lines, requirements)

    def store(self, installed_stuff, metadata):
        """Store the virtualenv metadata for the indicated installed_stuff."""
        new_content = {
            'timestamp': int(time.mktime(time.localtime())),
            'installed': installed_stuff,
            'metadata': metadata,
        }
        logger.debug("Storing installed=%s metadata=%s", installed_stuff, metadata)
        with open(self.filepath, 'at', encoding='utf8') as fh:
            fh.write(json.dumps(new_content) + '\n')
