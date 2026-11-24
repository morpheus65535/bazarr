# coding=utf-8

import os
import secrets
import sqlite3
import shutil
import logging
import re
import tempfile

from datetime import datetime, timedelta, timezone
from zipfile import ZipFile, BadZipFile, ZIP_DEFLATED
from glob import glob
from pathlib import PurePosixPath
from typing import BinaryIO, Literal, overload

import yaml

from dynaconf.utils.parse_conf import converters as _DYNACONF_CONVERTERS

from app.get_args import args
from app.config import settings
from app.event_handler import event_stream
from app.jobs_queue import jobs_queue
from utilities.central import restart_bazarr

_BACKUP_FILENAME_RE = re.compile(r'^bazarr_backup_v[\w.\-]+\.zip$')


def _validate_backup_filename(filename: str | None) -> str | None:
    """
    Validate a backup filename and return a sanitized version of it.

    The function performs several checks to ensure that the supplied
    filename is safe to use when locating or creating backup files. An
    empty or missing filename is rejected. The filename must not contain
    any directory components, meaning that its base name must be identical
    to the original value, which prevents path traversal attempts. Finally,
    the filename must match the expected backup filename pattern. If any of
    these checks fail, ``None`` is returned; otherwise the validated
    filename is returned unchanged.

    :param filename: The backup filename to validate. May be ``None`` or an
        empty string, in which case validation fails.
    :return: The validated filename if it passes all safety checks,
        otherwise ``None``.
    """
    if not filename:
        return None
    safe_name = os.path.basename(filename)
    if safe_name != filename:
        return None
    if not _BACKUP_FILENAME_RE.match(safe_name):
        return None
    return safe_name


def _safe_extract(zip_obj: ZipFile, dest_path: str) -> None:
    """
    Safely extract all members of a ZIP archive into a destination
    directory, guarding against path traversal attacks.

    Before extraction, every member name in the archive is resolved to
    an absolute, normalized path relative to the destination directory.
    If any resolved path falls outside the destination directory (for
    example, due to ``..`` components or absolute paths embedded in the
    archive), the extraction is aborted and no files are written. Only
    when all members are verified to be contained within the destination
    directory is the archive extracted in full.

    :param zip_obj: An open ZIP archive whose contents should be
        extracted.
    :param dest_path: Path to the directory into which the archive
        members will be extracted. It is resolved to its real, absolute
        form for the containment check.
    :raises BadZipFile: If any archive member would be extracted to a
        location outside of the destination directory.
    :return: None
    """
    dest_real = os.path.realpath(dest_path)
    for member in zip_obj.namelist():
        member_real = os.path.realpath(os.path.join(dest_real, member))
        if member_real != dest_real and not member_real.startswith(dest_real + os.sep):
            raise BadZipFile(f'Unsafe path in backup archive: {member}')
    zip_obj.extractall(path=dest_path)


def _get_backup_path() -> str:
    """
    Resolve the backup directory path from the application settings and
    ensure that it exists on the file system.

    The path is read from the backup section of the global settings. If the
    directory is missing, it is created together with any required parent
    directories. The resolved path is logged at debug level before being
    returned to the caller.

    :return: Absolute or relative path to the backup directory as configured
        in the settings, guaranteed to exist after this call.
    :raises OSError: If the backup directory does not exist and cannot be
        created, for example due to insufficient permissions or an invalid
        path.
    """
    backup_dir = settings.backup.folder
    if not os.path.isdir(backup_dir):
        os.makedirs(backup_dir)
    logging.debug(f'Backup directory path is: {backup_dir}')
    return backup_dir


def _get_restore_path() -> str:
    """
    Build and return the path to the restore directory located inside the
    configured configuration directory.

    The restore directory is derived from the global ``args.config_dir``
    setting by appending a ``restore`` sub-folder. If the directory does
    not yet exist, it is created along with any missing parent directories.
    The resolved path is logged at debug level before being returned.

    :return: Absolute or relative path to the restore directory, depending
        on how ``args.config_dir`` was specified.
    :raises OSError: If the restore directory cannot be created, for
        example due to insufficient permissions or an invalid path.
    """
    restore_dir = os.path.join(args.config_dir, 'restore')
    if not os.path.isdir(restore_dir):
        os.makedirs(restore_dir)
    logging.debug(f'Restore directory path is: {restore_dir}')
    return restore_dir


@overload
def get_backup_files(fullpath: Literal[True] = True) -> list[str]: ...


@overload
def get_backup_files(fullpath: Literal[False]) -> list[dict[str, str]]: ...


def get_backup_files(fullpath: bool = True) -> list[str] | list[dict[str, str]]:
    """
    Retrieve the list of Bazarr backup archive files located in the
    configured backup directory.

    The backup directory is resolved through ``_get_backup_path()`` and
    scanned for files matching the ``bazarr_backup_v*.zip`` naming pattern.
    The resulting list is sorted by file modification time in descending
    order, so the most recently created backup appears first. Depending on
    the ``fullpath`` flag, the function either returns the raw absolute
    paths of the matched files or a list of dictionaries describing each
    backup with a fixed type marker, the base filename, a human-readable
    file size and the modification date formatted as ``"%b %d %Y"``.

    :param fullpath: When ``True``, return the absolute paths of the backup
        files. When ``False``, return a list of dictionaries containing the
        ``type``, ``filename``, ``size`` and ``date`` of each backup file.
    :return: Either a list of absolute file paths or a list of dictionaries
        with descriptive metadata for each backup file, ordered from newest
        to oldest.
    :raises OSError: If the backup directory or one of the matched files
        cannot be accessed while retrieving its size or modification time.
    """
    backup_file_pattern = os.path.join(_get_backup_path(), 'bazarr_backup_v*.zip')
    file_list = glob(backup_file_pattern)
    file_list.sort(key=os.path.getmtime, reverse=True)
    if fullpath:
        return file_list
    else:
        return [{
            'type': 'backup',
            'filename': os.path.basename(x),
            'size': _sizeof_fmt(os.path.getsize(x)),
            'date': datetime.fromtimestamp(os.path.getmtime(x)).strftime("%b %d %Y")
        } for x in file_list]


def backup_to_zip(job_id: int | None = None, wait_for_completion: bool = False) -> None:
    """
    Create a compressed zip archive containing a backup of the Bazarr SQLite
    database (when PostgreSQL is not enabled) and the configuration file.

    When no job identifier is supplied, the backup is not performed directly;
    instead, a new job wrapping this function is enqueued in the jobs queue and
    the function returns immediately. When a job identifier is supplied, the
    backup is executed: a consistent copy of the SQLite database is produced
    using the SQLite online backup API, then the database copy and the
    ``config.yaml`` file are written into a timestamped zip archive named
    after the current Bazarr version in the backup directory. The temporary
    database copy is removed afterwards. If the database copy fails, the
    archive is still created but contains only the configuration file. Upon
    completion the job name is updated and a ``backup`` event is emitted to
    the event stream.

    :param job_id: Identifier of the job under which the backup runs. If
        ``None`` or falsy, a job is scheduled instead of performing the backup
        directly.
    :param wait_for_completion: Whether the caller should block until the
        scheduled backup job has completed. Only relevant when ``job_id`` is
        not provided.
    :return: None
    :raises OSError: If the zip archive cannot be created or the
        configuration file cannot be read from the configuration directory.

    The archive is created with owner-only permissions (``0600``) on POSIX
    systems. On Windows the owner-only mode is not enforced, so the archive
    inherits the access control list of the backup directory.
    """
    if not job_id:
        jobs_queue.add_job_from_function("Backing up Database and Configuration File", is_progress=False,
                                         wait_for_completion=wait_for_completion)
        return

    now = datetime.now()
    database_backup_file = None
    now_string = now.strftime("%Y.%m.%d_%H.%M.%S")
    backup_filename = f"bazarr_backup_v{os.environ['BAZARR_VERSION']}_{now_string}.zip"
    logging.debug(f'Backup filename will be: {backup_filename}')

    if not settings.postgresql.enabled:
        database_src_file = os.path.join(args.config_dir, 'db', 'bazarr.db')
        logging.debug(f'Database file path to backup is: {database_src_file}')

        database_src_con = None
        database_backup_con = None
        try:
            database_src_con = sqlite3.connect(database_src_file)

            database_backup_fd, database_backup_file = tempfile.mkstemp(prefix='bazarr_temp_', suffix='.db')
            os.close(database_backup_fd)
            database_backup_con = sqlite3.connect(database_backup_file)

            with database_backup_con:
                database_src_con.backup(database_backup_con)
        except Exception:
            logging.exception('Unable to backup database file.')
            if database_backup_file:
                try:
                    os.remove(database_backup_file)
                except (OSError, FileNotFoundError):
                    logging.exception(f'Unable to delete temporary database backup file: {database_backup_file}')
            database_backup_file = None
        finally:
            for database_con in (database_backup_con, database_src_con):
                if database_con is not None:
                    database_con.close()

    config_file = os.path.join(args.config_dir, 'config', 'config.yaml')
    logging.debug(f'Config file path to backup is: {config_file}')

    try:
        backup_file_path = os.path.join(_get_backup_path(), backup_filename)
        backup_fd = os.open(backup_file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(backup_fd, 'wb') as backup_file, ZipFile(backup_file, 'w', compression=ZIP_DEFLATED,
                                                                compresslevel=9) as backupZip:
            if database_backup_file:
                backupZip.write(database_backup_file, 'bazarr.db')
            else:
                logging.debug('Database file is not included in backup. See previous exception')
            backupZip.write(config_file, 'config.yaml')
    finally:
        if database_backup_file:
            try:
                os.remove(database_backup_file)
            except (OSError, FileNotFoundError):
                logging.exception(f'Unable to delete temporary database backup file: {database_backup_file}')

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Backed up Database and Configuration File")
    event_stream(type='backup')


def _is_template_value(value: object) -> bool:
    """
    Check whether a single parsed value is a Dynaconf template value.

    Dynaconf only evaluates a string when its first space-delimited word is
    exactly one of its converter names, such as ``@get``, ``@read_file`` or
    ``@format``. Other strings that start with ``@``, for example a password
    like ``@hunter2``, are loaded literally and are not templates.

    :param value: Parsed YAML scalar.
    :return: ``True`` if Dynaconf would evaluate the string, ``False`` otherwise.
    """
    return isinstance(value, str) and value.partition(' ')[0] in _DYNACONF_CONVERTERS


def _has_template_values(node: object) -> bool:
    """
    Check whether a parsed configuration contains Dynaconf template values.

    :param node: Parsed YAML value, possibly a nested mapping or list.
    :return: ``True`` if any string in the structure is a Dynaconf template
        value, ``False`` otherwise.
    """
    if isinstance(node, dict):
        return any(_has_template_values(value) for value in node.values())
    if isinstance(node, list):
        return any(_has_template_values(value) for value in node)
    return _is_template_value(node)


def _load_config_yaml(content: bytes) -> dict[str, object] | None:
    """
    Parse the content of a Bazarr YAML configuration file.

    :param content: Raw bytes of the ``config.yaml`` file.
    :return: The parsed mapping, or ``None`` if the content is not valid YAML,
        does not describe a mapping, or contains Dynaconf template values.
    """
    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError:
        return None
    if not isinstance(config, dict) or _has_template_values(config):
        return None
    return config


def _uses_postgresql(config: dict[str, object]) -> bool:
    """
    Tell whether a parsed configuration enables the PostgreSQL backend.

    :param config: Parsed configuration mapping.
    :return: ``True`` only if ``postgresql.enabled`` is the boolean ``True``.
    """
    section = config.get('postgresql')
    return isinstance(section, dict) and section.get('enabled') is True


def _read_restore_config(config_path: str) -> dict[str, object] | None:
    """
    Read and validate a configuration file located in the restore directory.

    :param config_path: Path to the ``config.yaml`` file to read.
    :return: The parsed configuration, or ``None`` if the file cannot be read,
        is invalid, or contains Dynaconf template values.
    """
    try:
        with open(config_path, 'rb') as config_file:
            return _load_config_yaml(config_file.read())
    except OSError:
        return None


def _restore_config_uses_postgresql(config_path: str) -> bool:
    """
    Check whether a configuration file in the restore directory enables PostgreSQL.

    Unreadable or invalid files are treated as not using PostgreSQL, so that a
    SQLite database is required before anything is restored.

    :param config_path: Path to the ``config.yaml`` file to inspect.
    :return: ``True`` if the file parses and enables PostgreSQL, ``False``
        otherwise.
    """
    config = _read_restore_config(config_path)
    return config is not None and _uses_postgresql(config)


def restore_from_backup() -> None:
    """
    Restore Bazarr configuration and database files from a previously
    extracted backup located in the restore directory.

    The configuration file is required and must be valid YAML without Dynaconf
    template values; otherwise the backup is refused and its files are removed
    from the restore directory. The YAML configuration file is preferred over
    the legacy INI file. The SQLite database file is required
    unless the restored configuration enables PostgreSQL, because backups taken
    on a PostgreSQL instance contain only the configuration file. When the
    database is required and missing, the partial backup is ignored and a debug
    message is logged.

    When the restore proceeds, the configuration file is copied to the
    configuration directory and any leftover configuration file of the other
    format is removed from the restore directory. The SQLite database file is
    copied to the database directory only if the restored configuration does
    not use PostgreSQL, and any stale SQLite shared-memory and write-ahead log
    files are removed. After a successful restore, all running web server
    connections are closed and Bazarr is restarted.

    If neither a configuration file nor a database file is present, the function
    returns without further action. All file system errors encountered during
    copy or removal operations are logged rather than propagated.

    :return: None.
    :rtype: None
    """
    restore_dir = _get_restore_path()
    if os.path.isfile(os.path.join(restore_dir, 'config.yaml')):
        restore_config_path = os.path.join(restore_dir, 'config.yaml')
        dest_config_path = os.path.join(args.config_dir, 'config', 'config.yaml')
        new_config = True
    else:
        restore_config_path = os.path.join(restore_dir, 'config.ini')
        dest_config_path = os.path.join(args.config_dir, 'config', 'config.ini')
        new_config = False

    restore_database_path = os.path.join(restore_dir, 'bazarr.db')
    dest_database_path = os.path.join(args.config_dir, 'db', 'bazarr.db')

    has_config = os.path.isfile(restore_config_path)
    has_database = os.path.isfile(restore_database_path)

    if new_config and has_config and _read_restore_config(restore_config_path) is None:
        logging.error('Refusing to restore backup: config.yaml is invalid or contains template values.')
        for leftover in (restore_config_path, restore_database_path):
            try:
                os.remove(leftover)
            except FileNotFoundError:
                pass
            except OSError:
                logging.exception(f'Unable to delete {leftover}')
        return

    uses_postgresql = new_config and has_config and _restore_config_uses_postgresql(restore_config_path)

    if has_config and (has_database or uses_postgresql):
        try:
            shutil.copy(restore_config_path, dest_config_path)
            os.remove(restore_config_path)
        except (OSError, FileNotFoundError):
            logging.exception(f'Unable to restore or delete config file to {dest_config_path}')
        else:
            if new_config:
                if os.path.isfile(os.path.join(restore_dir, 'config.ini')):
                    os.remove(os.path.join(restore_dir, 'config.ini'))
            else:
                if os.path.isfile(os.path.join(restore_dir, 'config.yaml')):
                    os.remove(os.path.join(restore_dir, 'config.yaml'))
        if has_database and not uses_postgresql:
            try:
                shutil.copy(restore_database_path, dest_database_path)
            except (OSError, FileNotFoundError):
                logging.exception(f'Unable to restore or delete db to {dest_database_path}')
            else:
                try:
                    if os.path.isfile(f'{dest_database_path}-shm'):
                        os.remove(f'{dest_database_path}-shm')
                    if os.path.isfile(f'{dest_database_path}-wal'):
                        os.remove(f'{dest_database_path}-wal')
                except (OSError, FileNotFoundError):
                    logging.exception('Unable to delete SHM and WAL file.')
        if has_database:
            try:
                os.remove(restore_database_path)
            except (OSError, FileNotFoundError):
                logging.exception(f'Unable to delete {restore_database_path}')

        logging.info('Backup restored successfully. Bazarr will restart.')
        from app.server import webserver
        if webserver is not None:
            webserver.close_all()
        restart_bazarr()
    elif has_config or has_database:
        logging.debug('Cannot restore a partial backup. You must have a config file, and a database unless the '
                      'configuration uses PostgreSQL.')
    else:
        logging.debug('No backup to restore.')
        return

    try:
        os.remove(restore_config_path)
    except FileNotFoundError:
        pass
    except (OSError, FileNotFoundError):
        logging.exception(f'Unable to delete {dest_config_path}')


def prepare_restore(filename: str) -> bool:
    """
    Prepare a backup archive for restoration and trigger an application
    restart.

    The given backup filename is first validated to prevent path traversal
    or otherwise unsafe names. The corresponding archive is then copied
    from the backup directory into the restore directory, its contents are
    safely extracted into the restore directory, and the copied archive is
    removed afterwards regardless of whether extraction succeeded. Any
    failure during copying, extraction or cleanup is logged rather than
    propagated. When the archive has been extracted successfully, the
    running web server (if any) is shut down and the application is
    restarted so that the restored files take effect.

    :param filename: Name of the backup archive located in the backup
        directory that should be restored.
    :return: ``True`` if the archive was copied and extracted successfully
        and a restart was initiated, ``False`` if the filename was rejected
        or the copy or extraction step failed.
    """
    safe_filename = _validate_backup_filename(filename)
    if safe_filename is None:
        logging.error('Invalid backup filename refused for restore.')
        return False
    src_zip_file_path = os.path.join(_get_backup_path(), safe_filename)
    dest_zip_file_path = os.path.join(_get_restore_path(), safe_filename)
    success = False
    try:
        shutil.copy(src_zip_file_path, dest_zip_file_path)
    except (OSError, FileNotFoundError):
        logging.exception(f'Unable to copy backup archive to {dest_zip_file_path}')
    else:
        try:
            with ZipFile(dest_zip_file_path, 'r') as zipObj:
                _safe_extract(zipObj, _get_restore_path())
        except BadZipFile:
            logging.exception(f'Unable to extract files from backup archive {dest_zip_file_path}')
        else:
            success = True
    finally:
        try:
            os.remove(dest_zip_file_path)
        except (OSError, FileNotFoundError):
            logging.exception(f'Unable to delete backup archive {dest_zip_file_path}')

    if success:
        logging.debug('time to restart')
        from app.server import webserver        
        if webserver is not None:
            webserver.close_all()
        restart_bazarr()

    return success


def backup_rotation() -> None:
    """
    Rotate backup files by removing those that have exceeded the configured
    retention period.

    The retention period is read from the application settings and must be
    a valid integer representing a number of days. If the configured value
    cannot be interpreted as an integer, an error is logged and the
    function exits without performing any cleanup. Otherwise, every backup
    file whose last modification time plus the retention period lies in the
    past (relative to the current UTC time) is deleted. Failures to delete
    an individual file are logged at debug level and do not interrupt the
    processing of the remaining files.

    :return: None
    """
    backup_retention = settings.backup.retention
    try:
        int(backup_retention)
    except ValueError:
        logging.error('Backup retention time must be a valid integer. Please fix this in your settings.')
        return

    backup_files = get_backup_files()

    logging.debug(f'Cleaning up backup files older than {backup_retention} days')
    for file in backup_files:
        if (datetime.fromtimestamp(os.path.getmtime(file), tz=timezone.utc) + timedelta(days=int(backup_retention)) <
                datetime.now(tz=timezone.utc)):
            logging.debug(f'Deleting old backup file {file}')
            try:
                os.remove(file)
            except (OSError, FileNotFoundError):
                logging.debug(f'Unable to delete backup file {file}')
    logging.debug('Finished cleaning up old backup files')


def delete_backup_file(filename: str) -> bool:
    """
    Delete a backup file located in the configured backup directory.

    The provided filename is first validated to ensure it is a safe backup
    filename (e.g. no path traversal). If validation fails, an error is logged
    and the deletion is refused. Otherwise the file is removed from the backup
    directory. Failures during removal, such as the file not existing or lacking
    permissions, are logged at debug level and reported through the return
    value rather than propagated to the caller.

    :param filename: Name of the backup file to delete, relative to the
        backup directory.
    :return: ``True`` if the file was successfully deleted, ``False`` if the
        filename was invalid or the file could not be removed.
    """
    safe_filename = _validate_backup_filename(filename)
    if safe_filename is None:
        logging.error('Invalid backup filename refused for deletion.')
        return False
    backup_file_path = os.path.join(_get_backup_path(), safe_filename)
    try:
        os.remove(backup_file_path)
        return True
    except (OSError, FileNotFoundError):
        logging.debug(f'Unable to delete backup file {backup_file_path}')
    return False


BACKUP_UPLOAD_MAX_BYTES = 1024 ** 3
_BACKUP_UPLOAD_MAX_UNCOMPRESSED_BYTES = 4 * 1024 ** 3
_BACKUP_UPLOAD_MAX_CONFIG_BYTES = 1024 * 1024
_BACKUP_UPLOAD_CHUNK_SIZE = 1024 * 1024
_SQLITE_MAGIC = b'SQLite format 3\x00'


class BackupUploadError(Exception):
    """
    Error raised when an uploaded backup archive is refused.

    The message is safe to return to the client. The status code is the HTTP
    status the API layer should answer with.
    """

    def __init__(self, message: str, status_code: int) -> None:
        """
        Create the upload error.

        :param message: Human-readable reason the upload was refused.
        :param status_code: HTTP status code to answer with.
        """
        super().__init__(message)
        self.status_code = status_code


def _is_safe_member_name(name: str) -> bool:
    """
    Check that a ZIP member name is a plain relative path without traversal.

    :param name: Member name as stored in the archive.
    :return: ``True`` if the name is relative, uses forward slashes only and
        contains no ``..`` component, ``False`` otherwise.
    """
    if '\\' in name or ':' in name.split('/')[0]:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and '..' not in path.parts


def _validate_backup_archive(archive_path: str) -> None:
    """
    Verify that a file is a complete Bazarr backup archive.

    The archive must be a readable ZIP whose CRCs check out and must not
    contain unsafe member names or expand beyond the uncompressed size limit.
    It must contain a ``config.yaml`` that parses to a mapping. A SQLite
    database file is required unless the configuration enables PostgreSQL,
    because backups taken on a PostgreSQL instance have no database file. When
    a database file is present it must start with the SQLite header.

    :param archive_path: Path to the archive file to inspect.
    :raises BackupUploadError: If the file is not a valid backup archive.
    :return: None
    """
    invalid = BackupUploadError('The uploaded file is not a valid Bazarr backup archive.', 400)
    try:
        with ZipFile(archive_path, 'r') as archive:
            if archive.testzip() is not None:
                raise invalid
            members = archive.infolist()
            if sum(member.file_size for member in members) > _BACKUP_UPLOAD_MAX_UNCOMPRESSED_BYTES:
                raise BackupUploadError('The uploaded backup archive expands to too much data.', 413)
            names = {member.filename for member in members}
            if not all(_is_safe_member_name(member.filename) for member in members):
                raise invalid
            if 'config.yaml' not in names:
                raise invalid
            config_member = archive.getinfo('config.yaml')
            if config_member.file_size > _BACKUP_UPLOAD_MAX_CONFIG_BYTES:
                raise invalid
            config = _load_config_yaml(archive.read(config_member))
            if config is None:
                raise invalid
            if 'bazarr.db' in names:
                with archive.open('bazarr.db') as database_member:
                    if database_member.read(len(_SQLITE_MAGIC)) != _SQLITE_MAGIC:
                        raise invalid
            elif not _uses_postgresql(config):
                raise BackupUploadError('The backup has no database file and does not use PostgreSQL, so it '
                                        'cannot be restored.', 400)
    except BadZipFile:
        raise invalid


def save_uploaded_backup(stream: BinaryIO, filename: str | None) -> str:
    """
    Store an uploaded backup archive in the configured backup directory.

    The uploaded filename must match the same pattern used for backups that
    Bazarr creates itself, otherwise the archive would not be listed or
    restorable. The data is streamed into a hidden temporary file in the
    backup directory, never under a name the backup list reads, and is capped
    at ``BACKUP_UPLOAD_MAX_BYTES``. Only after the archive passes validation
    is it moved to its final name. Existing backups are never overwritten. The
    temporary file is removed on every failure path. The file is created with
    owner-only permissions (``0600``) on POSIX systems.
    On Windows the owner-only mode is not enforced, so the file inherits the access
    control list of the backup directory.

    :param stream: Binary stream carrying the uploaded archive.
    :param filename: Filename supplied by the client.
    :raises BackupUploadError: If the filename is invalid (400), a backup with
        the same name already exists (409), the upload exceeds the size limit
        (413) or the file is not a valid backup archive (400).
    :return: The validated filename under which the backup was stored.
    """
    safe_filename = _validate_backup_filename(filename)
    if safe_filename is None:
        raise BackupUploadError('Invalid filename. Expected a Bazarr backup archive name.', 400)

    backup_dir = _get_backup_path()
    final_path = os.path.join(backup_dir, safe_filename)
    if os.path.exists(final_path):
        raise BackupUploadError('A backup with this name already exists.', 409)

    temp_path = os.path.join(backup_dir, f'.upload_{secrets.token_hex(16)}.tmp')
    fd = os.open(temp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        written = 0
        with os.fdopen(fd, 'wb') as temp_file:
            while chunk := stream.read(_BACKUP_UPLOAD_CHUNK_SIZE):
                written += len(chunk)
                if written > BACKUP_UPLOAD_MAX_BYTES:
                    raise BackupUploadError('The uploaded backup archive is too large.', 413)
                temp_file.write(chunk)
        _validate_backup_archive(temp_path)
        if os.path.exists(final_path):
            raise BackupUploadError('A backup with this name already exists.', 409)
        os.replace(temp_path, final_path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logging.exception(f'Unable to delete temporary upload file {temp_path}')

    logging.info(f'Backup archive uploaded: {safe_filename}')
    return safe_filename


def _sizeof_fmt(num: float, suffix: str = "B") -> str:
    """
    Format a numeric byte-like value into a human-readable string using
    SI (decimal, base 1000) unit prefixes.

    The value is repeatedly divided by 1000 until its absolute value drops
    below 1000, selecting the matching prefix from the sequence
    "", "K", "M", "G", "T", "P", "E", "Z". If the value still exceeds the
    largest available prefix, the "Y" prefix is applied to the remaining
    value. The result is rendered with one decimal place, followed by a
    space, the selected prefix and the given suffix.

    :param num: Numeric value to format, expressed in base units
        (e.g. bytes). Negative values are supported and keep their sign.
    :param suffix: Unit suffix appended after the SI prefix,
        defaults to "B".
    :return: Human-readable representation of ``num`` with an SI prefix
        and the given suffix, for example "1.5 KB" or "12.0 MB".
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1000.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f} Y{suffix}"
