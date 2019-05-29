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

from fades import cache


def test_missing_file_pytest(tmp_file, mocker):
    venvscache = cache.VEnvsCache(str(tmp_file))
    mock = mocker.patch.object(venvscache, '_select')
    mock.return_value = None
    resp = venvscache.get_venv('requirements', 'interpreter', uuid='', options='options')
    mock.assert_called_with([], 'requirements', 'interpreter', uuid='', options='options')
    assert not resp


def test_empty_file_pytest(tmp_file, mocker):
    open(tmp_file, 'wt', encoding='utf8').close()
    venvscache = cache.VEnvsCache(tmp_file)
    mock = mocker.patch.object(venvscache, '_select', return_value=None)
    resp = venvscache.get_venv('requirements', 'interpreter')
    mock.assert_called_with([], 'requirements', 'interpreter', uuid='', options=None)
    assert not resp


def test_some_file_content_pytest(tmp_file, mocker):
    with open(tmp_file, 'wt', encoding='utf8') as fh:
        fh.write('foo\nbar\n')
    venvscache = cache.VEnvsCache(tmp_file)
    mock = mocker.patch.object(venvscache, '_select', return_value="resp")
    resp = venvscache.get_venv('requirements', 'interpreter', uuid='', options='options')
    mock.assert_called_with(['foo', 'bar'], 'requirements', 'interpreter', uuid='',
                            options='options')
    assert resp == 'resp'


def test_get_by_uuid_pytest(tmp_file, mocker):
    with open(tmp_file, 'wt', encoding='utf8') as fh:
        fh.write('foo\nbar\n')
    venvscache = cache.VEnvsCache(tmp_file)
    mock = mocker.patch.object(venvscache, '_select', return_value='resp')
    resp = venvscache.get_venv(uuid='uuid')
    mock.assert_called_with(['foo', 'bar'], None, '', uuid='uuid', options=None)
    assert resp == 'resp'
