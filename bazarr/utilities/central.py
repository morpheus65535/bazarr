# coding=utf-8

# only methods can be specified here that do not cause other moudules to be loaded
# for other methods that use settings, etc., use utilities/helper.py

import logging
import os
from pathlib import Path

from literals import ENV_BAZARR_ROOT_DIR, DIR_LOG, ENV_STOPFILE, ENV_RESTARTFILE, EXIT_NORMAL, FILE_LOG


def get_bazarr_dir(sub_dir: str) -> str:
    """
    Build the absolute path to a subdirectory inside the Bazarr root
    directory.

    The Bazarr root directory is read from the environment variable
    referenced by ``ENV_BAZARR_ROOT_DIR`` and the given subdirectory name
    is appended to it. No check is performed to verify that the resulting
    path actually exists on the filesystem.

    :param sub_dir: Name of the subdirectory, relative to the Bazarr root
        directory, whose full path should be built.
    :return: The joined path of the Bazarr root directory and the given
        subdirectory.
    :raises KeyError: If the environment variable referenced by
        ``ENV_BAZARR_ROOT_DIR`` is not set.
    """
    path = os.path.join(os.environ[ENV_BAZARR_ROOT_DIR], sub_dir)
    return path


def make_bazarr_dir(sub_dir: str) -> None:
    """
    Create a subdirectory inside the Bazarr data directory if it does not
    already exist.

    The full path is resolved by combining the Bazarr base directory with the
    given subdirectory name. If the resulting path is already present on the
    filesystem, no action is taken; otherwise a single directory level is
    created. Parent directories are not created.

    :param sub_dir: Name of the subdirectory to create inside the Bazarr
        data directory.
    :return: None.
    :raises OSError: If the directory cannot be created, for example due to
        insufficient permissions or a missing parent directory.
    """
    path = get_bazarr_dir(sub_dir)
    if not os.path.exists(path):
        os.mkdir(path)


def get_log_file_path() -> str:
    """
    Build the absolute path to the Bazarr log file.

    The path is composed by joining the Bazarr log directory,
    resolved through the application directory helper, with the
    configured log file name.

    :return: Absolute path to the Bazarr log file.
    """
    path = os.path.join(get_bazarr_dir(DIR_LOG), FILE_LOG)
    return path


def get_stop_file_path() -> str:
    """
    Retrieve the path to the stop file from the environment.

    The path is read from the environment variable whose name is
    defined by the ``ENV_STOPFILE`` constant. The stop file is
    typically used as a signal for a running process to stop
    gracefully.

    :return: The path to the stop file as stored in the environment
        variable.
    :raises KeyError: If the environment variable identified by
        ``ENV_STOPFILE`` is not set.
    """
    return os.environ[ENV_STOPFILE]


def get_restart_file_path() -> str:
    """
    Retrieve the path to the restart file from the environment.

    Reads the environment variable identified by ``ENV_RESTARTFILE``
    and returns its value, which is expected to be the filesystem path
    of the restart file used to resume a previously interrupted
    operation. The variable must be set before this function is called.

    :return: The filesystem path to the restart file as stored in the
        environment variable.
    :raises KeyError: If the environment variable identified by
        ``ENV_RESTARTFILE`` is not set.
    """
    return os.environ[ENV_RESTARTFILE]


def stop_bazarr(status_code: int = EXIT_NORMAL) -> None:
    """
    Shut down the Bazarr application immediately with the given exit status.

    A stop file is created at the location returned by ``get_stop_file_path()``
    and the requested status code is written into it so that the final exit
    status can be picked up by the launcher process. If the stop file cannot
    be created, the failure is logged and the shutdown continues anyway.
    A shutdown message is then logged and the interpreter is terminated
    directly without raising ``SystemExit``, because such an exception would
    be intercepted by the waitress server and prevent a proper exit.

    :param status_code: Exit status code to write to the stop file and to use
        when terminating the process. Defaults to ``EXIT_NORMAL``.
    :return: This function never returns; the process is terminated.
    :raises Exception: No exception is propagated; errors raised while
        creating the stop file are caught and logged.

    """
    try:
        with open(get_stop_file_path(), 'w', encoding='UTF-8') as file:
            # write out status code for final exit
            file.write(f'{status_code}\n')
            file.close()
    except Exception as e:
        logging.error(f'BAZARR Cannot create stop file: {repr(e)}')
    logging.info('Bazarr is being shutdown...')
    os._exit(status_code)  # Don't raise SystemExit here since it's catch by waitress and it prevents proper exit


def restart_bazarr() -> None:
    """
    Trigger a restart of the Bazarr application.

    Creates (touches) the restart marker file at the location returned by
    ``get_restart_file_path`` so that the surrounding launcher knows the
    process should be started again, logs the restart intention, and then
    terminates the current process immediately with the ``EXIT_NORMAL``
    exit code. The process is terminated via ``os._exit`` rather than by
    raising ``SystemExit`` because the latter would be intercepted by the
    waitress server and prevent a proper shutdown. Any failure while
    creating the restart file is logged as an error but does not stop the
    process from exiting.

    :return: This function never returns normally since the process is
        terminated.

    """
    try:
        Path(get_restart_file_path()).touch()
    except Exception as e:
        logging.error(f'BAZARR Cannot create restart file: {repr(e)}')
    logging.info('Bazarr is being restarted...')
    os._exit(EXIT_NORMAL)  # Don't raise SystemExit here since it's catch by waitress and it prevents proper exit
