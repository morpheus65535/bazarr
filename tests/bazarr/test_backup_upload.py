"""
Tests for uploading backup archives into the backup directory.
"""
import io
import os
import sqlite3
import sys
import zipfile
from types import SimpleNamespace

import pytest
from flask import Flask
from werkzeug.exceptions import HTTPException

import utilities.backup as backup_module
from app.config import settings
from utilities.backup import BackupUploadError, save_uploaded_backup

VALID_NAME = 'bazarr_backup_v1.0.0_2026.01.01_00.00.00.zip'


def _sqlite_bytes(tmp_path) -> bytes:
    db_path = tmp_path / 'source.db'
    db_path.unlink(missing_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.execute('create table t (x integer)')
    return db_path.read_bytes()


def _make_archive(members: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return buffer.getvalue()


@pytest.fixture
def backup_dir(tmp_path):
    folder = tmp_path / 'backup'
    folder.mkdir()
    original = settings.backup.folder
    settings.backup.folder = str(folder)
    yield folder
    settings.backup.folder = original


@pytest.fixture
def valid_archive(tmp_path):
    return _make_archive({'bazarr.db': _sqlite_bytes(tmp_path), 'config.yaml': b'general: {}\n'})


def _leftover_temp_files(folder) -> list[str]:
    return [name for name in os.listdir(folder) if name.startswith('.upload_')]


def test_valid_archive_is_stored_under_its_name(backup_dir, valid_archive):
    stored = save_uploaded_backup(io.BytesIO(valid_archive), VALID_NAME)

    assert stored == VALID_NAME
    assert (backup_dir / VALID_NAME).read_bytes() == valid_archive
    assert _leftover_temp_files(backup_dir) == []


def test_uploaded_backup_is_listed_for_restore(backup_dir, valid_archive):
    save_uploaded_backup(io.BytesIO(valid_archive), VALID_NAME)

    assert [item['filename'] for item in backup_module.get_backup_files(fullpath=False)] == [VALID_NAME]


@pytest.mark.parametrize('name', [None, '', 'backup.zip', '../bazarr_backup_v1.zip', 'bazarr_backup_v1.tar',
                                  'sub/bazarr_backup_v1.zip', 'bazarr_backup_v1.zip.exe'])
def test_invalid_filenames_are_rejected(backup_dir, valid_archive, name):
    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(valid_archive), name)

    assert error.value.status_code == 400
    assert os.listdir(backup_dir) == []


def test_non_zip_content_is_rejected(backup_dir):
    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(b'this is not a zip'), VALID_NAME)

    assert error.value.status_code == 400
    assert os.listdir(backup_dir) == []


def test_archive_without_database_is_rejected(backup_dir):
    archive = _make_archive({'config.yaml': b'general: {}\n'})

    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(archive), VALID_NAME)

    assert error.value.status_code == 400
    assert os.listdir(backup_dir) == []


POSTGRESQL_CONFIG = b'postgresql:\n  enabled: true\n'


def test_postgresql_archive_with_only_config_is_stored(backup_dir):
    archive = _make_archive({'config.yaml': POSTGRESQL_CONFIG})

    stored = save_uploaded_backup(io.BytesIO(archive), VALID_NAME)

    assert stored == VALID_NAME
    assert (backup_dir / VALID_NAME).read_bytes() == archive


@pytest.mark.parametrize('config', [b'general: [unclosed\n', b'- just\n- a list\n', b''])
def test_archive_with_invalid_config_is_rejected(backup_dir, tmp_path, config):
    archive = _make_archive({'bazarr.db': _sqlite_bytes(tmp_path), 'config.yaml': config})

    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(archive), VALID_NAME)

    assert error.value.status_code == 400
    assert os.listdir(backup_dir) == []


def test_archive_without_config_is_rejected(backup_dir, tmp_path):
    archive = _make_archive({'bazarr.db': _sqlite_bytes(tmp_path)})

    with pytest.raises(BackupUploadError):
        save_uploaded_backup(io.BytesIO(archive), VALID_NAME)

    assert os.listdir(backup_dir) == []


def test_database_member_must_be_sqlite(backup_dir):
    archive = _make_archive({'bazarr.db': b'plain text, not a database', 'config.yaml': b'general: {}\n'})

    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(archive), VALID_NAME)

    assert error.value.status_code == 400
    assert os.listdir(backup_dir) == []


@pytest.mark.parametrize('member', ['../evil.yaml', '/etc/evil.yaml', 'sub/../../evil.yaml', 'C:evil.yaml',
                                    'dir\\..\\evil.yaml'])
def test_archive_with_unsafe_member_names_is_rejected(backup_dir, tmp_path, member):
    archive = _make_archive({'bazarr.db': _sqlite_bytes(tmp_path), 'config.yaml': b'general: {}\n', member: b'x'})

    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(archive), VALID_NAME)

    assert error.value.status_code == 400
    assert os.listdir(backup_dir) == []


def test_existing_backup_is_never_overwritten(backup_dir, valid_archive):
    original = b'original backup content'
    (backup_dir / VALID_NAME).write_bytes(original)

    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(valid_archive), VALID_NAME)

    assert error.value.status_code == 409
    assert (backup_dir / VALID_NAME).read_bytes() == original
    assert _leftover_temp_files(backup_dir) == []


def test_oversized_upload_is_refused_and_cleaned_up(backup_dir, valid_archive, monkeypatch):
    monkeypatch.setattr(backup_module, 'BACKUP_UPLOAD_MAX_BYTES', len(valid_archive) - 1)

    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(valid_archive), VALID_NAME)

    assert error.value.status_code == 413
    assert os.listdir(backup_dir) == []


def test_upload_endpoint_requires_apikey(backup_dir, valid_archive):
    from api.system.backups import SystemBackupsUpload

    original = settings.auth.apikey
    settings.auth.apikey = 'a' * 32
    try:
        with Flask(__name__).test_request_context('/system/backups/upload', method='POST'):
            with pytest.raises(HTTPException) as error:
                SystemBackupsUpload().post()
            assert error.value.code == 401
    finally:
        settings.auth.apikey = original

    assert os.listdir(backup_dir) == []


UPLOAD_URL = '/api/system/backups/upload'


def test_endpoint_stores_archive_with_valid_apikey(api_client, api_key, backup_dir, valid_archive):
    response = api_client.post(UPLOAD_URL, headers={'X-API-KEY': api_key},
                               data={'file': (io.BytesIO(valid_archive), VALID_NAME)},
                               content_type='multipart/form-data')

    assert response.status_code == 204
    assert (backup_dir / VALID_NAME).read_bytes() == valid_archive


def test_endpoint_rejects_missing_apikey_without_storing(api_client, backup_dir, valid_archive):
    response = api_client.post(UPLOAD_URL, data={'file': (io.BytesIO(valid_archive), VALID_NAME)},
                               content_type='multipart/form-data')

    assert response.status_code == 401
    assert os.listdir(backup_dir) == []


def test_endpoint_rejects_invalid_archive(api_client, api_key, backup_dir):
    response = api_client.post(UPLOAD_URL, headers={'X-API-KEY': api_key},
                               data={'file': (io.BytesIO(b'not a zip'), VALID_NAME)},
                               content_type='multipart/form-data')

    assert response.status_code == 400
    assert os.listdir(backup_dir) == []


def test_endpoint_reports_conflict_for_existing_name(api_client, api_key, backup_dir, valid_archive):
    (backup_dir / VALID_NAME).write_bytes(b'existing')

    response = api_client.post(UPLOAD_URL, headers={'X-API-KEY': api_key},
                               data={'file': (io.BytesIO(valid_archive), VALID_NAME)},
                               content_type='multipart/form-data')

    assert response.status_code == 409
    assert (backup_dir / VALID_NAME).read_bytes() == b'existing'


def test_endpoint_enforces_request_size_limit(api_client, api_key, backup_dir, monkeypatch):
    import api.system.backups as backups_api

    monkeypatch.setattr(backups_api, 'BACKUP_UPLOAD_MAX_BYTES', 0)
    oversized = os.urandom(2 * 1024 * 1024)

    response = api_client.post(UPLOAD_URL, headers={'X-API-KEY': api_key},
                               data={'file': (io.BytesIO(oversized), VALID_NAME)},
                               content_type='multipart/form-data')

    assert response.status_code == 413
    assert os.listdir(backup_dir) == []


@pytest.fixture
def restore_env(tmp_path, monkeypatch):
    """Point the restore logic at a temporary application data directory and stub the restart."""
    config_dir = tmp_path / 'appdata'
    (config_dir / 'config').mkdir(parents=True)
    (config_dir / 'db').mkdir()
    (config_dir / 'restore').mkdir()
    monkeypatch.setattr(backup_module.args, 'config_dir', str(config_dir))
    restarts: list[bool] = []
    monkeypatch.setattr(backup_module, 'restart_bazarr', lambda: restarts.append(True))
    monkeypatch.setitem(sys.modules, 'app.server', SimpleNamespace(webserver=None))
    (config_dir / 'config' / 'config.yaml').write_text('existing: true\n')
    return SimpleNamespace(config_dir=config_dir, restore_dir=config_dir / 'restore', restarts=restarts)


def test_restore_applies_config_only_postgresql_backup(restore_env):
    (restore_env.restore_dir / 'config.yaml').write_bytes(POSTGRESQL_CONFIG)

    backup_module.restore_from_backup()

    assert (restore_env.config_dir / 'config' / 'config.yaml').read_bytes() == POSTGRESQL_CONFIG
    assert not (restore_env.config_dir / 'db' / 'bazarr.db').exists()
    assert not (restore_env.restore_dir / 'config.yaml').exists()
    assert restore_env.restarts == [True]


def test_restore_ignores_config_only_sqlite_backup(restore_env):
    (restore_env.restore_dir / 'config.yaml').write_text('general: {}\n')

    backup_module.restore_from_backup()

    assert (restore_env.config_dir / 'config' / 'config.yaml').read_text() == 'existing: true\n'
    assert not (restore_env.restore_dir / 'config.yaml').exists()
    assert restore_env.restarts == []


def test_restore_requires_database_for_legacy_ini(restore_env):
    (restore_env.restore_dir / 'config.ini').write_text('[general]\n')

    backup_module.restore_from_backup()

    assert (restore_env.config_dir / 'config' / 'config.yaml').read_text() == 'existing: true\n'
    assert restore_env.restarts == []


def test_restore_applies_full_sqlite_backup(restore_env, tmp_path):
    (restore_env.restore_dir / 'config.yaml').write_text('general: {}\n')
    (restore_env.restore_dir / 'bazarr.db').write_bytes(_sqlite_bytes(tmp_path))

    backup_module.restore_from_backup()

    assert (restore_env.config_dir / 'config' / 'config.yaml').read_text() == 'general: {}\n'
    assert (restore_env.config_dir / 'db' / 'bazarr.db').read_bytes() == _sqlite_bytes(tmp_path)
    assert not (restore_env.restore_dir / 'bazarr.db').exists()
    assert restore_env.restarts == [True]


def test_restore_of_postgresql_config_does_not_copy_database(restore_env, tmp_path):
    (restore_env.restore_dir / 'config.yaml').write_bytes(POSTGRESQL_CONFIG)
    (restore_env.restore_dir / 'bazarr.db').write_bytes(_sqlite_bytes(tmp_path))

    backup_module.restore_from_backup()

    assert (restore_env.config_dir / 'config' / 'config.yaml').read_bytes() == POSTGRESQL_CONFIG
    assert not (restore_env.config_dir / 'db' / 'bazarr.db').exists()
    assert not (restore_env.restore_dir / 'bazarr.db').exists()
    assert restore_env.restarts == [True]


def test_restore_refuses_invalid_config_without_database(restore_env):
    (restore_env.restore_dir / 'config.yaml').write_text('general: [unclosed\n')

    backup_module.restore_from_backup()

    assert (restore_env.config_dir / 'config' / 'config.yaml').read_text() == 'existing: true\n'
    assert restore_env.restarts == []


@pytest.mark.parametrize('config', [
    b'probe: "@read_file /etc/hosts"\npostgresql:\n  enabled: true\n',
    b'postgresql:\n  enabled: true\n  password: "@get SECRET"\n',
    b'general:\n  items:\n    - "@format {this.X}"\n',
])
def test_archive_with_dynaconf_template_values_is_rejected(backup_dir, config):
    archive = _make_archive({'config.yaml': config})

    with pytest.raises(BackupUploadError) as error:
        save_uploaded_backup(io.BytesIO(archive), VALID_NAME)

    assert error.value.status_code == 400
    assert os.listdir(backup_dir) == []


def test_restore_refuses_config_with_template_values(restore_env, tmp_path):
    (restore_env.restore_dir / 'config.yaml').write_text('probe: "@read_file /etc/hosts"\n')
    (restore_env.restore_dir / 'bazarr.db').write_bytes(_sqlite_bytes(tmp_path))

    backup_module.restore_from_backup()

    assert (restore_env.config_dir / 'config' / 'config.yaml').read_text() == 'existing: true\n'
    assert not (restore_env.config_dir / 'db' / 'bazarr.db').exists()
    assert list(restore_env.restore_dir.iterdir()) == []
    assert restore_env.restarts == []


@pytest.mark.skipif(os.name == 'nt', reason='Windows does not enforce POSIX file modes')
def test_uploaded_backup_is_owner_only(backup_dir, valid_archive):
    save_uploaded_backup(io.BytesIO(valid_archive), VALID_NAME)

    assert (backup_dir / VALID_NAME).stat().st_mode & 0o777 == 0o600


@pytest.mark.skipif(os.name == 'nt', reason='Windows does not enforce POSIX file modes')
def test_scheduled_backup_archive_is_owner_only(backup_dir, restore_env, monkeypatch):
    monkeypatch.setenv('BAZARR_VERSION', '1.0.0')
    monkeypatch.setattr(backup_module, 'jobs_queue', SimpleNamespace(update_job_name=lambda **_: None))
    monkeypatch.setattr(backup_module, 'event_stream', lambda **_: None)
    original = settings.postgresql.enabled
    settings.postgresql.enabled = True
    try:
        backup_module.backup_to_zip(job_id=1)
    finally:
        settings.postgresql.enabled = original

    archives = [name for name in os.listdir(backup_dir) if name.startswith('bazarr_backup_v')]
    assert len(archives) == 1
    archive_path = backup_dir / archives[0]
    assert archive_path.stat().st_mode & 0o777 == 0o600
    with zipfile.ZipFile(archive_path) as archive:
        assert archive.namelist() == ['config.yaml']


@pytest.mark.parametrize('password', ['@hunter2', '@Secr3t!pass', '@ pass word', ' @get SECRET', '@hunter2 extra'])
def test_archive_with_literal_at_password_is_accepted(backup_dir, password):
    config = f'postgresql:\n  enabled: true\n  password: "{password}"\n'.encode()
    archive = _make_archive({'config.yaml': config})

    assert save_uploaded_backup(io.BytesIO(archive), VALID_NAME) == VALID_NAME


def test_restore_applies_config_with_literal_at_password(restore_env, tmp_path):
    (restore_env.restore_dir / 'config.yaml').write_text('postgresql:\n  enabled: false\n  password: "@hunter2"\n')
    (restore_env.restore_dir / 'bazarr.db').write_bytes(_sqlite_bytes(tmp_path))

    backup_module.restore_from_backup()

    assert 'password: "@hunter2"' in (restore_env.config_dir / 'config' / 'config.yaml').read_text()
    assert restore_env.restarts == [True]


@pytest.mark.parametrize('password', ['@hunter2', '@Secr3t!pass', '@ pass word'])
def test_dynaconf_loads_literal_at_password_unchanged(tmp_path, password):
    from dynaconf import Dynaconf

    config_path = tmp_path / 'config.yaml'
    config_path.write_text(f'password: "{password}"\n')

    loaded = Dynaconf(settings_file=str(config_path), core_loaders=['YAML'])

    assert loaded.get('password') == password
