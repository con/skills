"""Local replay routes must not be mistaken for portable project metadata."""
import importlib.util
import pathlib
import subprocess

import pytest

HELPER = (pathlib.Path(__file__).resolve().parents[3] / 'skills' /
          'assess-alignment-with-stamped-principles/scripts/fresh_rerun.py')
spec = importlib.util.spec_from_file_location('replay_routes', HELPER)
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
UUID = 'e5f25f11-c272-473b-9eb3-792c8fb3a776'


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def repositories(tmp_path):
    source, clone = tmp_path / 'source', tmp_path / 'clone'
    for root in (source, clone):
        root.mkdir()
        git(root, 'init', '-q')
    return source, clone


def route(source, url='https://example.org/project.git',
          annexurl='annex+https://example.org/store'):
    for key, value in {'url': url, 'annexurl': annexurl, 'annex-uuid': UUID}.items():
        git(source, 'config', '--local', 'remote.storage.' + key, value)


def test_preserves_source_and_copies_only_explicit_route(repositories):
    source, clone = repositories
    route(source)
    git(source, 'config', '--local', 'remote.storage.uploadpack', 'never-copy-command')
    git(source, 'config', '--local', 'http.extraHeader', 'never-copy-header')
    before = (source / '.git/config').read_bytes()
    report = replay._local_annex_routes(source, clone)
    assert (source / '.git/config').read_bytes() == before
    assert report['host_scope'] == 'same-host'
    assert report['route_origin'] == 'local-source-git-config'
    copied = report['routes'][0]
    assert copied['source_remote'] == 'storage'
    assert git(clone, 'config', 'remote.' + copied['replay_remote'] + '.annexurl') == 'annex+https://example.org/store'
    assert 'never-copy' not in (clone / '.git/config').read_text()
    assert 'never-copy' not in repr(report)


@pytest.mark.parametrize('address', [
    'https://name:secret@example.org/store',
    'https://secret@example.org/store',
    'https://example.org/store?token=secret',
    'https://example.org/store#secret',
    'ext::secret-command',
    '/tmp/store\nsecret',
])
def test_rejects_credential_and_command_addresses_without_echo(repositories, address):
    source, clone = repositories
    route(source, annexurl=address)
    before = (clone / '.git/config').read_bytes()
    with pytest.raises(ValueError) as error:
        replay._local_annex_routes(source, clone)
    assert 'secret' not in str(error.value)
    assert (clone / '.git/config').read_bytes() == before


def test_absent_route_is_not_invented(repositories):
    source, clone = repositories
    git(source, 'config', 'remote.origin.url', 'https://example.org/project.git')
    before = (clone / '.git/config').read_bytes()
    assert replay._local_annex_routes(source, clone)['routes'] == []
    assert (clone / '.git/config').read_bytes() == before


def test_ambiguous_route_is_not_selected_arbitrarily(repositories):
    source, clone = repositories
    route(source)
    git(source, 'config', '--add', 'remote.storage.annexurl', 'https://example.org/other')
    with pytest.raises(ValueError, match='Ambiguous'):
        replay._local_annex_routes(source, clone)


def test_incomplete_route_is_not_silently_used(repositories):
    source, clone = repositories
    route(source)
    git(source, 'config', '--unset', 'remote.storage.annex-uuid')
    with pytest.raises(ValueError, match='Incomplete'):
        replay._local_annex_routes(source, clone)
