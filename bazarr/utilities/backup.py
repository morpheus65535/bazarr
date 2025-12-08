# coding=utf-8

import os
import sqlite3
import shutil
import logging

from datetime import datetime, timedelta, timezone
from zipfile import ZipFile, BadZipFile, ZIP_DEFLATED
from glob import glob

from app.get_args import args
from app.config import settings
from app.jobs_queue import jobs_queue
from utilities.central import restart_bazarr


def get_backup_path():
    backup_dir = settings.backup.folder
    if not os.path.isdir(backup_dir):
        os.makedirs(backup_dir)
    logging.debug(f'Backup directory path is: {backup_dir}')
    return backup_dir


def get_restore_path():
    restore_dir = os.path.join(args.config_dir, 'restore')
    if not os.path.isdir(restore_dir):
        os.makedirs(restore_dir)
    logging.debug(f'Restore directory path is: {restore_dir}')
    return restore_dir


def get_backup_files(fullpath=True):
    backup_file_pattern = os.path.join(get_backup_path(), 'bazarr_backup_v*.zip')
    file_list = glob(backup_file_pattern)
    file_list.sort(key=os.path.getmtime, reverse=True)
    if fullpath:
        return file_list
    else:
        return [{
            'type': 'backup',
            'filename': os.path.basename(x),
            'size': sizeof_fmt(os.path.getsize(x)),
            'date': datetime.fromtimestamp(os.path.getmtime(x)).strftime("%b %d %Y")
        } for x in file_list]


def backup_to_zip(job_id=None):
    if not job_id:
        jobs_queue.add_job_from_function("Backup Database and Configuration File", is_progress=False)
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

            database_backup_file = os.path.join(get_backup_path(), 'bazarr_temp.db')
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

    with ZipFile(os.path.join(get_backup_path(), backup_filename), 'w', compression=ZIP_DEFLATED,
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


def restore_from_backup():
    if os.path.isfile(os.path.join(get_restore_path(), 'config.yaml')):
        restore_config_path = os.path.join(get_restore_path(), 'config.yaml')
        dest_config_path = os.path.join(args.config_dir, 'config', 'config.yaml')
        new_config = True
    else:
        restore_config_path = os.path.join(get_restore_path(), 'config.ini')
        dest_config_path = os.path.join(args.config_dir, 'config', 'config.ini')
        new_config = False

    restore_database_path = os.path.join(get_restore_path(), 'bazarr.db')
    dest_database_path = os.path.join(args.config_dir, 'db', 'bazarr.db')

    if os.path.isfile(restore_config_path) and os.path.isfile(restore_database_path):
        try:
            shutil.copy(restore_config_path, dest_config_path)
            os.remove(restore_config_path)
        except (OSError, FileNotFoundError):
            logging.exception(f'Unable to restore or delete config file to {dest_config_path}')
        else:
            if new_config:
                if os.path.isfile(os.path.join(get_restore_path(), 'config.ini')):
                    os.remove(os.path.join(get_restore_path(), 'config.ini'))
            else:
                if os.path.isfile(os.path.join(get_restore_path(), 'config.yaml')):
                    os.remove(os.path.join(get_restore_path(), 'config.yaml'))
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


def prepare_restore(filename):
    src_zip_file_path = os.path.join(get_backup_path(), filename)
    dest_zip_file_path = os.path.join(get_restore_path(), filename)
    success = False
    try:
        shutil.copy(src_zip_file_path, dest_zip_file_path)
    except (OSError, FileNotFoundError):
        logging.exception(f'Unable to copy backup archive to {dest_zip_file_path}')
    else:
        try:
            with ZipFile(dest_zip_file_path, 'r') as zipObj:
                zipObj.extractall(path=get_restore_path())
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


def backup_rotation():
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


def delete_backup_file(filename):
    backup_file_path = os.path.join(get_backup_path(), filename)
    try:
        os.remove(backup_file_path)
        return True
    except (OSError, FileNotFoundError):
        logging.debug(f'Unable to delete backup file {backup_file_path}')
    return False


def sizeof_fmt(num, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1000.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1000.0
    return f"{num:.1f} Y{suffix}"
