# coding=utf-8

import os
import sqlite3
import shutil
import logging

from datetime import datetime, timedelta
from zipfile import ZipFile, BadZipFile
from glob import glob

from get_args import args
from config import settings


def get_backup_path():
    backup_dir = os.path.join(args.config_dir, 'backup')
    if settings.backup.folder != 'None':
        backup_dir = settings.backup.folder
    if not os.path.isdir(backup_dir):
        os.mkdir(backup_dir)
    logging.debug(f'Backup directory path is: {backup_dir}')
    return backup_dir


def get_restore_path():
    restore_dir = os.path.join(args.config_dir, 'restore')
    if not os.path.isdir(restore_dir):
        os.mkdir(restore_dir)
    logging.debug(f'Restore directory path is: {restore_dir}')
    return restore_dir


def get_backup_files(fullpath=True):
    backup_file_pattern = os.path.join(get_backup_path(), 'bazarr_backup_v*.zip')
    file_list = glob(backup_file_pattern)
    if fullpath:
        return file_list
    else:
        return [{
            'type': 'backup',
            'filename': os.path.basename(x),
            'date': datetime.fromtimestamp(os.path.getmtime(x)).strftime("%b %d %Y")
        } for x in file_list]


def backup_to_zip():
    now = datetime.now()
    now_string = now.strftime("%Y.%m.%d_%H.%M.%S")
    backup_filename = f"bazarr_backup_v{os.environ['BAZARR_VERSION']}_{now_string}.zip"
    logging.debug(f'Backup filename will be: {backup_filename}')

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

    config_file = os.path.join(args.config_dir, 'config', 'config.ini')
    logging.debug(f'Config file path to backup is: {config_file}')

    with ZipFile(os.path.join(get_backup_path(), backup_filename), 'w') as backupZip:
        if database_backup_file:
            backupZip.write(database_backup_file, 'bazarr.db')
        else:
            logging.debug(f'Database file is not included in backup. See previous exception')
        backupZip.write(config_file, 'config.ini')

    try:
        os.remove(database_backup_file)
    except OSError:
        logging.exception(f'Unable to delete temporary database backup file: {database_backup_file}')


def restore_from_backup():
    restore_config_path = os.path.join(get_restore_path(), 'config.ini')
    dest_config_path = os.path.join(args.config_dir, 'config', 'config.ini')
    restore_database_path = os.path.join(get_restore_path(), 'bazarr.db')
    dest_database_path = os.path.join(args.config_dir, 'db', 'bazarr.db')

    if os.path.isfile(restore_config_path) and os.path.isfile(restore_database_path):
        try:
            shutil.copy(restore_config_path, dest_config_path)
        except OSError:
            logging.exception(f'Unable to restore config.ini to {dest_config_path}')

        try:
            shutil.copy(restore_database_path, dest_database_path)
        except OSError:
            logging.exception(f'Unable to restore bazarr.db to {dest_database_path}')
        else:
            try:
                if os.path.isfile(dest_database_path + '-shm'):
                    os.remove(dest_database_path + '-shm')
                if os.path.isfile(dest_database_path + '-wal'):
                    os.remove(dest_database_path + '-wal')
            except OSError:
                logging.exception('Unable to delete SHM and WAL file.')

        logging.info('Backup restored successfully. Bazarr will restart.')

        # todo: restart Bazarr
    else:
        logging.debug('Cannot restore a partial backup. You must have both config and database.')

    try:
        os.remove(restore_config_path)
    except OSError:
        logging.exception(f'Unable to delete {dest_config_path}')

    try:
        os.remove(restore_database_path)
    except OSError:
        logging.exception(f'Unable to delete {dest_database_path}')


def prepare_restore(filename):
    src_zip_file_path = os.path.join(get_backup_path(), filename)
    dest_zip_file_path = os.path.join(get_restore_path(), filename)
    success = False
    try:
        shutil.copy(src_zip_file_path, dest_zip_file_path)
    except OSError:
        logging.exception(f'Unable to copy backup archive to {dest_zip_file_path}')
    else:
        try:
            with ZipFile('sampleDir.zip', 'r') as zipObj:
                zipObj.extractall(path=dest_zip_file_path)
        except BadZipFile:
            logging.exception(f'Unable to extract files from backup archive {dest_zip_file_path}')

        success = True
    finally:
        try:
            os.remove(dest_zip_file_path)
        except OSError:
            logging.exception(f'Unable to delete backup archive {dest_zip_file_path}')

    if success:
        logging.debug('time to restart')
        # todo: restart Bazarr


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
        if datetime.fromtimestamp(os.path.getmtime(file)) + timedelta(days=backup_retention) < datetime.utcnow():
            logging.debug(f'Deleting old backup file {file}')
            try:
                os.remove(file)
            except OSError:
                logging.debug(f'Unable to delete backup file {file}')
    logging.debug('Finished cleaning up old backup files')


def delete_backup_file(filename):
    backup_file_path = os.path.join(get_backup_path(), filename)
    try:
        os.remove(backup_file_path)
        return True
    except OSError:
        logging.debug(f'Unable to delete backup file {backup_file_path}')
    return False
