# coding=utf-8

# only methods can be specified here that do not cause other moudules to be loaded
# for other methods that use settings, etc., use utilities/helper.py

import logging
import os
from pathlib import Path

from literals import ENV_BAZARR_ROOT_DIR, DIR_LOG, ENV_STOPFILE, ENV_RESTARTFILE, EXIT_NORMAL, FILE_LOG


def get_bazarr_dir(sub_dir):
    path = os.path.join(os.environ[ENV_BAZARR_ROOT_DIR], sub_dir)
    return path


def make_bazarr_dir(sub_dir):
    path = get_bazarr_dir(sub_dir)
    if not os.path.exists(path):
        os.mkdir(path)


def get_log_file_path():
    path = os.path.join(get_bazarr_dir(DIR_LOG), FILE_LOG)
    return path


def get_stop_file_path():
    return os.environ[ENV_STOPFILE]


def get_restart_file_path():
    return os.environ[ENV_RESTARTFILE]


def stop_bazarr(status_code=EXIT_NORMAL):
    try:
        with open(get_stop_file_path(), 'w', encoding='UTF-8') as file:
            # write out status code for final exit
            file.write(f'{status_code}\n')
            file.close()
    except Exception as e:
        logging.error(f'BAZARR Cannot create stop file: {repr(e)}')
    logging.info('Bazarr is being shutdown...')
    os._exit(status_code)  # Don't raise SystemExit here since it's catch by waitress and it prevents proper exit


def restart_bazarr():
    try:
        Path(get_restart_file_path()).touch()
    except Exception as e:
        logging.error(f'BAZARR Cannot create restart file: {repr(e)}')
    logging.info('Bazarr is being restarted...')
    os._exit(EXIT_NORMAL)  # Don't raise SystemExit here since it's catch by waitress and it prevents proper exit
