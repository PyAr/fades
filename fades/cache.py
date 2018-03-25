# Copyright 2015-2016 Facundo Batista, Nicolás Demarchi
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

from fades import REPO_VCS

from pkg_resources import Distribution

from fades.multiplatform import filelock
from fades.parsing import VCSDependency

logger = logging.getLogger(__name__)


class VEnvsCache:
    """A cache for virtualenvs."""

    def __init__(self, filepath):
        """Init."""
        logger.debug("Using cache index: %r", filepath)
        self.filepath = filepath
        self.lockpath = filepath + ".lock"

    def _venv_match(self, installed, requirements):
        """Return True if what is installed satisfies the requirements.

        This method has multiple exit-points, but only for False (because
        if *anything* is not satisified, the venv is no good). Only after
        all was checked, and it didn't exit, the venv is ok so return True.
        """
        if not requirements:
            # special case for no requirements, where we can't actually
            # check anything: the venv is useful if nothing installed too
            return None if installed else []

        satisfying_deps = []
        for repo, req_deps in requirements.items():
            useful_inst = set()
            if repo not in installed:
                # the venv doesn't even have the repo
                return None

            if repo == REPO_VCS:
                inst_deps = {VCSDependency(url) for url in installed[repo].keys()}
            else:
                inst_deps = {Distribution(project_name=dep, version=ver)
                             for (dep, ver) in installed[repo].items()}
            for req in req_deps:
                for inst in inst_deps:
                    if inst in req:
                        useful_inst.add(inst)
                        break
                else:
                    # nothing installed satisfied that requirement
                    return None

            # assure *all* that is installed is useful for the requirements
            if useful_inst == inst_deps:
                satisfying_deps.extend(inst_deps)
            else:
                return None

        # it did it through!
        return satisfying_deps

    def _match_by_uuid(self, current_venvs, uuid):
        """Select a venv matching exactly by uuid."""
        for venv_str in current_venvs:
            venv = json.loads(venv_str)
            env_path = venv.get('metadata', {}).get('env_path')
            _, env_uuid = os.path.split(env_path)
            if env_uuid == uuid:
                return venv

    def _select_better_fit(self, matching_venvs):
        """Receive a list of matching venvs, and decide which one is the best fit."""
        # keep the venvs in a separate array, to pick up the winner, and the (sorted, to compare
        # each dependency with its equivalent) in other structure to later compare
        venvs = []
        to_compare = []
        for matching, venv in matching_venvs:
            to_compare.append(sorted(matching, key=lambda req: getattr(req, 'key', '')))
            venvs.append(venv)

        # compare each n-tuple of dependencies to see which one is bigger, and add score to the
        # position of the winner
        scores = [0] * len(venvs)
        for dependencies in zip(*to_compare):
            if not isinstance(dependencies[0], Distribution):
                # only distribution URLs can be compared
                continue

            winner = dependencies.index(max(dependencies))
            scores[winner] = scores[winner] + 1

        # get the rightmost winner (in case of ties, to select the latest venv)
        winner_pos = None
        winner_score = -1
        for i, score in enumerate(scores):
            if score >= winner_score:
                winner_score = score
                winner_pos = i
        return venvs[winner_pos]

    def _match_by_requirements(self, current_venvs, requirements, interpreter, options):
        """Select a venv matching interpreter and options, complying with requirements.

        Several venvs can be found in this case, will return the better fit.
        """
        matching_venvs = []
        for venv_str in current_venvs:
            venv = json.loads(venv_str)

            # simple filter, need to have exactly same options and interpreter
            if venv.get('options') != options or venv.get('interpreter') != interpreter:
                continue

            # requirements complying: result can be None (no comply) or a score to later sort
            matching = self._venv_match(venv['installed'], requirements)
            if matching is not None:
                matching_venvs.append((matching, venv))

        if not matching_venvs:
            return

        return self._select_better_fit(matching_venvs)

    def _select(self, current_venvs, requirements=None, interpreter='', uuid='', options=None):
        """Select which venv satisfy the received requirements."""
        if uuid:
            logger.debug("Searching a venv by uuid: %s", uuid)
            venv = self._match_by_uuid(current_venvs, uuid)
        else:
            logger.debug("Searching a venv for: reqs=%s interpreter=%s options=%s",
                         requirements, interpreter, options)
            venv = self._match_by_requirements(current_venvs, requirements, interpreter, options)

        if venv is None:
            logger.debug("No matching venv found :(")
            return

        logger.debug("Found a matching venv! %s", venv)
        return venv['metadata']

    def get_venv(self, requirements=None, interpreter='', uuid='', options=None):
        """Find a venv that serves these requirements, if any."""
        lines = self._read_cache()
        return self._select(lines, requirements, interpreter, uuid=uuid, options=options)

    def get_venvs_metadata(self):
        """Yield metadata of each existing venv."""
        for line in self._read_cache():
            yield json.loads(line)['metadata']

    def store(self, installed_stuff, metadata, interpreter, options):
        """Store the virtualenv metadata for the indicated installed_stuff."""
        new_content = {
            'timestamp': int(time.mktime(time.localtime())),
            'installed': installed_stuff,
            'metadata': metadata,
            'interpreter': interpreter,
            'options': options
        }
        logger.debug("Storing installed=%s metadata=%s interpreter=%s options=%s",
                     installed_stuff, metadata, interpreter, options)
        with filelock(self.lockpath):
            self._write_cache([json.dumps(new_content)], append=True)

    def remove(self, env_path):
        """Remove metadata for a given virtualenv from cache."""
        with filelock(self.lockpath):
            cache = self._read_cache()
            logger.debug("Removing virtualenv from cache: %s" % env_path)
            lines = [
                line for line in cache
                if json.loads(line).get('metadata', {}).get('env_path') != env_path
            ]
            self._write_cache(lines)

    def _read_cache(self):
        """Read virtualenv metadata from cache."""
        if os.path.exists(self.filepath):
            with open(self.filepath, 'rt', encoding='utf8') as fh:
                lines = [x.strip() for x in fh]
        else:
            logger.debug("Index not found, starting empty")
            lines = []
        return lines

    def _write_cache(self, lines, append=False):
        """Write virtualenv metadata to cache."""
        mode = 'at' if append else 'wt'
        with open(self.filepath, mode, encoding='utf8') as fh:
            fh.writelines(line + '\n' for line in lines)
