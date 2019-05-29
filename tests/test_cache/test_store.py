# Copyright 2015-2019 Facundo Batista, Nicolás Demarchi
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

import json

from fades import cache


def test_missing_file(tmp_file):
    venvscache = cache.VEnvsCache(tmp_file)
    venvscache.store('installed', 'metadata', 'interpreter', 'options')

    with open(tmp_file, 'rt', encoding='utf8') as fh:
        data = json.loads(fh.readline())
        assert 'timestamp' in data
        assert data['installed'], 'installed'
        assert data['metadata'], 'metadata'
        assert data['interpreter'], 'interpreter'
        assert data['options'], 'options'


def test_with_previous_content(tmp_file):
    with open(tmp_file, 'wt', encoding='utf8') as fh:
        fh.write(json.dumps({'foo': 'bar'}) + '\n')

    venvscache = cache.VEnvsCache(tmp_file)
    venvscache.store('installed', 'metadata', 'interpreter', 'options')

    with open(tmp_file, 'rt', encoding='utf8') as fh:
        data = json.loads(fh.readline())
        assert data, {'foo': 'bar'}

        data = json.loads(fh.readline())
        assert 'timestamp' in data
        assert data['installed'], 'installed'
        assert data['metadata'], 'metadata'
        assert data['interpreter'], 'interpreter'
        assert data['options'], 'options'
