# coding=utf-8

import os
import sqlite3
import shutil
import logging
import re

from datetime import datetime, timedelta, timezone
from zipfile import ZipFile, BadZipFile, ZIP_DEFLATED
from glob import glob
from typing import Literal, overload

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

        try:
            database_src_con = sqlite3.connect(database_src_file)

            database_backup_file = os.path.join(_get_backup_path(), 'bazarr_temp.db')
            database_backup_con = sqlite3.connect(database_backup_file)

            with database_backup_con:
                database_src_con.backup(database_backup_con)

            database_backup_con.close()
            database_src_con.close()
        except Exception:
            database_backup_file = None
            logging.exception('Unable to backup database file.')

    config_file = os.path.join(args.config_dir, 'config', 'config.yaml')
    logging.debug(f'Config file path to backup is: {config_file}')

    with ZipFile(os.path.join(_get_backup_path(), backup_filename), 'w', compression=ZIP_DEFLATED,
                 compresslevel=9) as backupZip:
        if database_backup_file:
            backupZip.write(database_backup_file, 'bazarr.db')
            try:
                os.remove(database_backup_file)
            except (OSError, FileNotFoundError):
                logging.exception(f'Unable to delete temporary database backup file: {database_backup_file}')
        else:
            logging.debug('Database file is not included in backup. See previous exception')
        backupZip.write(config_file, 'config.yaml')

    jobs_queue.update_job_name(job_id=job_id, new_job_name="Backed up Database and Configuration File")
    event_stream(type='backup')


def restore_from_backup() -> None:
    """
    Restore Bazarr configuration and database files from a previously
    extracted backup located in the restore directory.

    The function first determines which configuration format is present in
    the restore directory, preferring the YAML configuration file over the
    legacy INI file. A restore is only performed when both the configuration
    file and the SQLite database file are found in the restore directory.
    When both are present, the configuration file is copied to the
    configuration directory and any leftover configuration file of the other
    format is removed from the restore directory. If PostgreSQL is not
    enabled, the database file is copied to the database directory and any
    stale SQLite shared-memory and write-ahead log files are removed. After
    a successful restore, all running web server connections are closed and
    Bazarr is restarted.

    If only one of the two required files is present, the partial backup is
    ignored and a debug message is logged. If neither file is present, the
    function returns without further action. All file system errors
    encountered during copy or removal operations are logged rather than
    propagated.

    :return: None.
    :rtype: None
    """
    if os.path.isfile(os.path.join(_get_restore_path(), 'config.yaml')):
        restore_config_path = os.path.join(_get_restore_path(), 'config.yaml')
        dest_config_path = os.path.join(args.config_dir, 'config', 'config.yaml')
        new_config = True
    else:
        restore_config_path = os.path.join(_get_restore_path(), 'config.ini')
        dest_config_path = os.path.join(args.config_dir, 'config', 'config.ini')
        new_config = False

    restore_database_path = os.path.join(_get_restore_path(), 'bazarr.db')
    dest_database_path = os.path.join(args.config_dir, 'db', 'bazarr.db')

    if os.path.isfile(restore_config_path) and os.path.isfile(restore_database_path):
        try:
            shutil.copy(restore_config_path, dest_config_path)
            os.remove(restore_config_path)
        except (OSError, FileNotFoundError):
            logging.exception(f'Unable to restore or delete config file to {dest_config_path}')
        else:
            if new_config:
                if os.path.isfile(os.path.join(_get_restore_path(), 'config.ini')):
                    os.remove(os.path.join(_get_restore_path(), 'config.ini'))
            else:
                if os.path.isfile(os.path.join(_get_restore_path(), 'config.yaml')):
                    os.remove(os.path.join(_get_restore_path(), 'config.yaml'))
        if not settings.postgresql.enabled:
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

            try:
                os.remove(restore_database_path)
            except (OSError, FileNotFoundError):
                logging.exception(f'Unable to delete {dest_database_path}')

        logging.info('Backup restored successfully. Bazarr will restart.')
        from app.server import webserver
        if webserver is not None:
            webserver.close_all()
        restart_bazarr()
    elif os.path.isfile(restore_config_path) or os.path.isfile(restore_database_path):
        logging.debug('Cannot restore a partial backup. You must have both config and database.')
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
