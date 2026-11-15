"""
Tests for security hardening: API key validation, throttled providers parsing and backup download paths.
"""
import datetime

import pytest
from flask import Flask

from app.config import settings
from app.get_providers import _parse_throttled_providers
from utilities.helper import is_valid_apikey


def _import_api_module(monkeypatch, name):
    """Import a bazarr api submodule without running the api package __init__ files, which import init and set up
    the whole application."""
    import importlib
    import os
    import sys
    import types
    from app import config

    bazarr_dir = os.path.dirname(os.path.dirname(config.__file__))
    parts = name.split('.')
    for depth in range(1, len(parts)):
        package_name = '.'.join(parts[:depth])
        if package_name not in sys.modules:
            package = types.ModuleType(package_name)
            package.__path__ = [os.path.join(bazarr_dir, *parts[:depth])]
            monkeypatch.setitem(sys.modules, package_name, package)
    return importlib.import_module(name)


@pytest.fixture
def apikey():
    original = settings.auth.apikey
    settings.auth.apikey = 'a' * 32
    yield settings.auth.apikey
    settings.auth.apikey = original


def test_is_valid_apikey_accepts_configured_key(apikey):
    assert is_valid_apikey(None, apikey, None)


def test_is_valid_apikey_rejects_wrong_or_missing_key(apikey):
    assert not is_valid_apikey(None, None, None)
    assert not is_valid_apikey('', 'b' * 32, None)


def test_is_valid_apikey_rejects_everything_when_key_is_empty():
    original = settings.auth.apikey
    settings.auth.apikey = ''
    try:
        assert not is_valid_apikey('', None, None)
        assert not is_valid_apikey(None, None, None)
    finally:
        settings.auth.apikey = original


def test_parse_throttled_providers_round_trip():
    data = {
        'opensubtitlescom': ('TooManyRequests', datetime.datetime(2026, 1, 2, 3, 4, 5, 678), '1 hour'),
        'addic7ed': ('DownloadLimitExceeded', datetime.datetime.now(), None),
    }
    assert _parse_throttled_providers(str(data)) == data
    assert _parse_throttled_providers('') == {}


@pytest.mark.parametrize('payload', [
    "__import__('os').system('id')",
    "{'a': (lambda: 1)()}",
    "{'a': ('x', datetime.datetime(__import__('os').getpid()), '')}",
    "{'a': ('x', os.system('id'), '')}",
    "['not', 'a', 'dict']",
])
def test_parse_throttled_providers_rejects_code(payload):
    with pytest.raises((ValueError, SyntaxError)):
        _parse_throttled_providers(payload)


def test_backup_download_blocks_traversal_and_prefix_bypass(tmp_path):
    from app.ui import backup_download

    backup_dir = tmp_path / 'backup'
    backup_dir.mkdir()
    (backup_dir / 'bazarr_backup_v1.zip').write_bytes(b'zip')
    sibling = tmp_path / 'backup_evil'
    sibling.mkdir()
    (sibling / 'secret.txt').write_text('secret')

    app = Flask(__name__)
    original_folder = settings.backup.folder
    original_auth = settings.auth.type
    settings.backup.folder = str(backup_dir)
    settings.auth.type = 'None'
    try:
        with app.test_request_context():
            assert backup_download('../backup_evil/secret.txt') == ('', 404)
            assert backup_download('../../etc/passwd') == ('', 404)
            response = backup_download('bazarr_backup_v1.zip')
            assert response.status_code == 200
            response.close()
    finally:
        settings.backup.folder = original_folder
        settings.auth.type = original_auth


@pytest.fixture
def ui_credentials():
    original = (settings.auth.username, settings.auth.password)
    yield
    settings.auth.username, settings.auth.password = original


def test_hash_password_is_salted_and_verifies():
    from app.config import hash_password, verify_password

    first, second = hash_password('hunter2'), hash_password('hunter2')
    assert first != second
    assert first.startswith('pbkdf2:sha256:')
    assert verify_password('hunter2', first)
    assert not verify_password('wrong', first)
    assert not verify_password('hunter2', '')


def test_legacy_md5_password_is_upgraded_on_login(ui_credentials):
    import hashlib
    from unittest.mock import patch
    from utilities import helper

    settings.auth.username = 'admin'
    settings.auth.password = hashlib.md5(b'hunter2').hexdigest()
    with patch('app.config.write_config') as write_config:
        assert not helper._verify_user_password('admin', 'wrong')
        assert helper._verify_user_password('admin', 'hunter2')
        write_config.assert_called_once()
    assert settings.auth.password.startswith('pbkdf2:sha256:')
    assert helper._verify_user_password('admin', 'hunter2')
    assert not helper._verify_user_password('admin', 'wrong')
    assert not helper._verify_user_password('other', 'hunter2')


def test_password_change_invalidates_cached_login(ui_credentials):
    from app.config import hash_password
    from utilities import helper

    settings.auth.username = 'admin'
    settings.auth.password = hash_password('old')
    assert helper._verify_user_password('admin', 'old')
    settings.auth.password = hash_password('new')
    assert not helper._verify_user_password('admin', 'old')
    assert helper._verify_user_password('admin', 'new')


def test_concurrent_legacy_upgrade_writes_config_once(ui_credentials):
    import hashlib
    import threading
    from unittest.mock import patch
    from app.config import verify_password
    from utilities import helper

    settings.auth.username = 'admin'
    settings.auth.password = hashlib.md5(b'hunter2').hexdigest()
    results = []
    with patch('app.config.write_config') as write_config:
        threads = [threading.Thread(target=lambda: results.append(helper._verify_user_password('admin', 'hunter2')))
                   for _ in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert write_config.call_count == 1
    assert results == [True] * 12
    assert verify_password('hunter2', settings.auth.password)


def test_failed_logins_back_off_per_client_and_username(ui_credentials):
    from app.config import hash_password
    from unittest.mock import patch
    from utilities import helper

    settings.auth.username = 'admin'
    settings.auth.password = hash_password('right')
    client = 'test-client-backoff'
    helper._login_failures.clear()
    try:
        for _ in range(helper._LOGIN_FAILURES_FREE):
            assert not helper._verify_user_password('admin', 'wrong', client=client)
        assert helper._login_backoff_remaining(helper._login_failures_key(client, 'admin')) > 0
        # during backoff even the right password is refused without hashing
        with patch('app.config.verify_password') as verify:
            assert not helper._verify_user_password('admin', 'right', client=client)
            verify.assert_not_called()
        # other clients are not affected
        assert helper._verify_user_password('admin', 'right', client='another-client')
    finally:
        helper._login_failures.clear()


def test_failed_logins_for_other_username_do_not_lock_out_admin(ui_credentials):
    from app.config import hash_password
    from utilities import helper

    settings.auth.username = 'admin'
    settings.auth.password = hash_password('right')
    proxy = '127.0.0.1'  # every client behind a reverse proxy shares this address
    helper._login_failures.clear()
    try:
        for _ in range(helper._LOGIN_FAILURES_FREE + 3):
            assert not helper._verify_user_password('root', 'guess', client=proxy)
        assert helper._verify_user_password('admin', 'right', client=proxy)
    finally:
        helper._login_failures.clear()


def test_login_backoff_is_capped():
    import time
    from utilities import helper

    key = ('test-client-cap', 'admin')
    helper._login_failures[key] = (100, time.monotonic())
    try:
        assert 0 < helper._login_backoff_remaining(key) <= helper._LOGIN_BACKOFF_MAX <= 30
    finally:
        helper._login_failures.pop(key, None)


def test_login_api_returns_429_with_retry_after_when_throttled(ui_credentials, monkeypatch):
    from app.config import hash_password
    SystemAccount = _import_api_module(monkeypatch, 'api.system.account').SystemAccount
    from utilities import helper

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    original_type = settings.auth.type
    settings.auth.type = 'form'
    settings.auth.username = 'admin'
    settings.auth.password = hash_password('right')
    helper._login_failures.clear()

    def login(password):
        with app.test_request_context('/api/system/account?action=login', method='POST',
                                      data={'username': 'admin', 'password': password},
                                      environ_base={'REMOTE_ADDR': '10.0.0.9'}):
            return SystemAccount().post()

    try:
        for _ in range(helper._LOGIN_FAILURES_FREE - 1):
            assert login('wrong') == ('Authentication failed', 403)
        message, status, headers = login('wrong')
        assert status == 429
        assert 'Too many failed login attempts' in message
        assert 1 <= int(headers['Retry-After']) <= helper._LOGIN_BACKOFF_MAX
        # the right password is refused with the same explicit message during backoff
        import time
        helper._login_failures[('10.0.0.9', 'admin')] = (helper._LOGIN_FAILURES_FREE + 4, time.monotonic())
        assert login('right')[1] == 429
    finally:
        settings.auth.type = original_type
        helper._login_failures.clear()


def test_wrong_username_still_runs_password_hash(ui_credentials):
    from app.config import hash_password
    from unittest.mock import patch
    from utilities import helper

    settings.auth.username = 'admin'
    settings.auth.password = hash_password('right')
    with patch('app.config.verify_password', return_value=True) as verify:
        assert not helper._verify_user_password('nobody', 'right')
        verify.assert_called_once()


def test_malformed_unicode_never_raises(ui_credentials, apikey):
    from app.config import hash_password
    from utilities import helper

    settings.auth.username = 'admin'
    settings.auth.password = hash_password('right')
    assert not helper._verify_user_password('\ud800', 'right')
    assert not helper._verify_user_password('admin', '\ud800')
    assert not is_valid_apikey('\ud800')


def test_validate_auth_requires_credentials(ui_credentials):
    from dynaconf.validator import ValidationError
    from app.config import validate_auth

    original_type = settings.auth.type
    try:
        settings.auth.type = 'form'
        settings.auth.username = 'admin'
        settings.auth.password = ''
        with pytest.raises(ValidationError):
            validate_auth()
        settings.auth.username = ''
        settings.auth.password = 'x'
        with pytest.raises(ValidationError):
            validate_auth()
        settings.auth.username = 'admin'
        validate_auth()
        settings.auth.type = None
        settings.auth.password = ''
        validate_auth()
    finally:
        settings.auth.type = original_type


@pytest.mark.parametrize('embedding,scheme,expected', [
    (False, 'https', 'SameSite=Lax'),
    (True, 'http', 'SameSite=Lax'),
    (True, 'https', 'SameSite=None'),
])
def test_session_cookie_samesite(embedding, scheme, expected):
    from flask import session
    from app.app import BazarrSessionInterface

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    app.session_interface = BazarrSessionInterface()

    @app.route('/login')
    def login():
        session['logged_in'] = True
        return ''

    original = settings.auth.allow_iframe_embedding
    settings.auth.allow_iframe_embedding = embedding
    try:
        cookie = app.test_client().get('/login', base_url=f'{scheme}://localhost').headers['Set-Cookie']
    finally:
        settings.auth.allow_iframe_embedding = original
    assert expected in cookie
    assert 'HttpOnly' in cookie
    assert ('Secure' in cookie) == (expected == 'SameSite=None')


# --- socket.io ---

def test_socketio_connect_requires_apikey(apikey):
    from app.app import socketio_connect

    app = Flask(__name__)
    with app.test_request_context('/api/socket.io'):
        with pytest.raises(ConnectionRefusedError):
            socketio_connect(None)
        with pytest.raises(ConnectionRefusedError):
            socketio_connect({'apikey': 'b' * 32})
        socketio_connect({'apikey': apikey})
    with app.test_request_context('/api/socket.io', headers={'X-API-KEY': apikey}):
        socketio_connect(None)


# --- release archive (zip slip) ---

@pytest.mark.parametrize('name', [
    'bazarr/../../evil.py',
    'bazarr/../outside/evil.py',
    'bazarr//etc/cron.d/evil',
])
def test_release_archive_rejects_paths_outside_bazarr_dir(tmp_path, name):
    from app.check_update import check_release_archive_paths

    with pytest.raises(ValueError):
        check_release_archive_paths(['bazarr/', 'bazarr/bazarr.py', name], 'bazarr/', str(tmp_path / 'bazarr'))


def test_release_archive_accepts_regular_release(tmp_path):
    from app.check_update import check_release_archive_paths

    names = ['bazarr/', 'bazarr/bazarr.py', 'bazarr/frontend/build/index.html', 'bazarr/libs/']
    check_release_archive_paths(names, 'bazarr/', str(tmp_path / 'bazarr'))


def test_backup_download_does_not_follow_symlinks_out_of_backup_folder(tmp_path):
    from app.ui import backup_download

    backup_dir = tmp_path / 'backup'
    backup_dir.mkdir()
    secret = tmp_path / 'secret.txt'
    secret.write_text('secret')
    (backup_dir / 'bazarr_backup_link.zip').symlink_to(secret)

    original_folder, original_auth = settings.backup.folder, settings.auth.type
    settings.backup.folder = str(backup_dir)
    settings.auth.type = 'None'
    try:
        with Flask(__name__).test_request_context():
            assert backup_download('bazarr_backup_link.zip') == ('', 404)
    finally:
        settings.backup.folder, settings.auth.type = original_folder, original_auth


# --- indexed external subtitles only ---

MOVIE_ID = 1
EPISODE_ID = 10
MOVIE_SUBS = '/data/movies/Foo (2020)/Foo.en.srt'  # as presented to the UI, path mapping applied
MOVIE_REF_SUBS = '/data/movies/Foo (2020)/Foo.fr.srt'
EPISODE_SUBS = '/data/tv/Bar/Season 1/Bar.S01E01.en.srt'


@pytest.fixture
def media_db(monkeypatch, apikey):
    """In-memory database with one movie and one episode, each with indexed external subtitles.

    Path mappings sources are substrings of their targets (/movies -> /data/movies) so mapping a path twice would
    produce a wrong path.
    """
    from sqlalchemy import create_engine, insert
    from sqlalchemy.orm import Session
    import app.database as db_module
    import languages.get_languages
    from utilities import video_analyzer
    from utilities.path_mappings import path_mappings

    engine = create_engine('sqlite://')
    db_module.Base.metadata.create_all(engine)
    session = Session(engine)
    session.execute(insert(db_module.TableShows).values(sonarrSeriesId=1, title='Bar', path='/tv/Bar'))
    session.execute(insert(db_module.TableEpisodes).values(
        sonarrEpisodeId=EPISODE_ID, sonarrSeriesId=1, title='Pilot', season=1, episode=1,
        path='/tv/Bar/Season 1/Bar.S01E01.mkv'))
    session.execute(insert(db_module.TableEpisodesSubtitles).values(
        language='en', hi=False, forced=False, path='/tv/Bar/Season 1/Bar.S01E01.en.srt',
        sonarrEpisodeId=EPISODE_ID, sonarrSeriesId=1))
    session.execute(insert(db_module.TableMovies).values(
        radarrId=MOVIE_ID, title='Foo', tmdbId='1', path='/movies/Foo (2020)/Foo.mkv'))
    for language in ('en', 'fr'):
        session.execute(insert(db_module.TableMoviesSubtitles).values(
            language=language, hi=False, forced=False, path=f'/movies/Foo (2020)/Foo.{language}.srt',
            radarrId=MOVIE_ID))
    session.commit()

    api_utils = _import_api_module(monkeypatch, 'api.utils')
    subtitles_api = _import_api_module(monkeypatch, 'api.subtitles.subtitles')
    for module in (db_module, api_utils, subtitles_api, video_analyzer):
        monkeypatch.setattr(module, 'database', session)
    monkeypatch.setattr(path_mappings, 'path_mapping_series', [['/tv', '/data/tv']])
    monkeypatch.setattr(path_mappings, 'path_mapping_movies', [['/movies', '/data/movies']])
    monkeypatch.setattr(languages.get_languages, 'language_from_alpha2', lambda code: code)
    monkeypatch.setattr(languages.get_languages, 'alpha3_from_alpha2', lambda code: code)
    yield session
    session.close()


def test_is_known_external_subtitles(media_db, monkeypatch):
    is_known_external_subtitles = _import_api_module(monkeypatch, 'api.utils').is_known_external_subtitles

    assert is_known_external_subtitles(MOVIE_SUBS)
    assert is_known_external_subtitles(MOVIE_SUBS, media_type='movie', media_id=MOVIE_ID)
    assert is_known_external_subtitles(EPISODE_SUBS, media_type='episode', media_id=EPISODE_ID)
    # wrong media id or type
    assert not is_known_external_subtitles(MOVIE_SUBS, media_type='movie', media_id=MOVIE_ID + 1)
    assert not is_known_external_subtitles(MOVIE_SUBS, media_type='episode')
    # arbitrary files and garbage
    assert not is_known_external_subtitles('/etc/passwd')
    assert not is_known_external_subtitles('/data/movies/Foo (2020)/../../../etc/passwd')
    assert not is_known_external_subtitles('')
    assert not is_known_external_subtitles(None)


def test_subtitles_contents_only_reads_indexed_subtitles(media_db, apikey, monkeypatch):
    SubtitleNameContents = _import_api_module(monkeypatch, 'api.subtitles.subtitles_contents').SubtitleNameContents

    app = Flask(__name__)
    with app.test_request_context('/api/subtitles/contents', query_string={'subtitlePath': '/etc/passwd'},
                                  headers={'X-API-KEY': apikey}):
        assert SubtitleNameContents().get() == ('Subtitles file not found', 404)


def _patch_subtitles(apikey, **params):
    import sys
    Subtitles = sys.modules['api.subtitles.subtitles'].Subtitles  # imported by media_db fixture

    params.setdefault('language', 'en')
    with Flask(__name__).test_request_context('/api/subtitles', method='PATCH', query_string=params,
                                              headers={'X-API-KEY': apikey}):
        return Subtitles().patch()


@pytest.fixture
def fake_sync(monkeypatch, media_db):
    subtitles_api = _import_api_module(monkeypatch, 'api.subtitles.subtitles')

    calls = []
    monkeypatch.setattr(subtitles_api, 'sync_subtitles', lambda **kwargs: calls.append(kwargs))
    monkeypatch.setattr(subtitles_api, 'event_stream', lambda *args, **kwargs: None)
    return calls


def test_patch_subtitles_rejects_unindexed_path(media_db, apikey, fake_sync):
    result = _patch_subtitles(apikey, action='sync', type='movie', id=MOVIE_ID, path='/etc/passwd')
    assert result == ('Subtitles file not found', 404)
    result = _patch_subtitles(apikey, action='sync', type='movie', id=MOVIE_ID + 1, path=MOVIE_SUBS)
    assert result == ('Subtitles file not found', 404)
    assert fake_sync == []


def test_patch_subtitles_rejects_arbitrary_sync_reference(media_db, apikey, fake_sync, monkeypatch):
    monkeypatch.setattr('os.path.exists', lambda path: True)
    result = _patch_subtitles(apikey, action='sync', type='movie', id=MOVIE_ID, path=MOVIE_SUBS,
                              reference='/etc/passwd')
    assert result == ('Invalid sync reference', 400)
    assert fake_sync == []


@pytest.mark.parametrize('media_type,media_id,subtitles_path', [
    ('movie', MOVIE_ID, MOVIE_SUBS),
    ('episode', EPISODE_ID, EPISODE_SUBS),
])
def test_sync_references_from_ui_are_accepted(media_db, apikey, fake_sync, monkeypatch, media_type, media_id,
                                              subtitles_path):
    """External subtitles offered as sync reference must be the mapped path and accepted by the sync action."""
    from utilities import video_analyzer
    import app.database as db_module
    from sqlalchemy import insert

    if media_type == 'episode':
        media_db.execute(insert(db_module.TableEpisodesSubtitles).values(
            language='fr', hi=False, forced=False, path='/tv/Bar/Season 1/Bar.S01E01.fr.srt',
            sonarrEpisodeId=EPISODE_ID, sonarrSeriesId=1))
        media_db.commit()
    monkeypatch.setattr(video_analyzer, 'parse_video_metadata', lambda *args, **kwargs: {'ffprobe': {'audio': []}})
    monkeypatch.setattr('os.path.exists', lambda path: True)

    references = video_analyzer.subtitles_sync_references(
        subtitles_path,
        sonarr_episode_id=media_id if media_type == 'episode' else None,
        radarr_movie_id=media_id if media_type == 'movie' else None)
    external = references['external_subtitles_tracks']
    assert len(external) == 1
    reference = external[0]['path']
    assert reference == subtitles_path.replace('.en.srt', '.fr.srt')

    result = _patch_subtitles(apikey, action='sync', type=media_type, id=media_id, path=subtitles_path,
                              reference=reference)
    assert result == ('', 204)
    assert fake_sync[0]['reference'] == reference
