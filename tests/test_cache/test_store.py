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
