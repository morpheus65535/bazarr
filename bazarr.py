# coding=utf-8

import os
import platform
import signal
import subprocess
import sys
import time

from bazarr.app.get_args import args
from bazarr.literals import EXIT_PYTHON_UPGRADE_NEEDED, EXIT_NORMAL, FILE_RESTART, FILE_STOP, ENV_RESTARTFILE, ENV_STOPFILE, EXIT_INTERRUPT


def exit_program(status_code):
    print(f'Bazarr exited with status code {status_code}.')
    raise SystemExit(status_code)


def check_python_version():
    python_version = platform.python_version_tuple()
    minimum_py3_tuple = (3, 8, 0)
    minimum_py3_str = ".".join(str(i) for i in minimum_py3_tuple)

    if int(python_version[0]) < minimum_py3_tuple[0]:
        print("Python " + minimum_py3_str + " or greater required. "
              "Current version is " + platform.python_version() + ". Please upgrade Python.")
        exit_program(EXIT_PYTHON_UPGRADE_NEEDED)
    elif int(python_version[0]) == 3 and int(python_version[1]) > 12:
        print("Python version greater than 3.12.x is unsupported. Current version is " + platform.python_version() +
              ". Keep in mind that even if it works, you're on your own.")
    elif (int(python_version[0]) == minimum_py3_tuple[0] and int(python_version[1]) < minimum_py3_tuple[1]) or \
            (int(python_version[0]) != minimum_py3_tuple[0]):
        print("Python " + minimum_py3_str + " or greater required. "
              "Current version is " + platform.python_version() + ". Please upgrade Python.")
        exit_program(EXIT_PYTHON_UPGRADE_NEEDED)


def get_python_path():
    if sys.platform == "darwin":
        # Do not run Python from within macOS framework bundle.
        python_bundle_path = os.path.join(sys.base_exec_prefix, "Resources", "Python.app", "Contents", "MacOS", "Python")
        if os.path.exists(python_bundle_path):
            import tempfile

            python_path = os.path.join(tempfile.mkdtemp(), "python")
            os.symlink(python_bundle_path, python_path)

            return python_path

    return sys.executable


check_python_version()

dir_name = os.path.dirname(__file__)


def start_bazarr():
    script = [get_python_path(), "-u", os.path.normcase(os.path.join(dir_name, 'bazarr', 'main.py'))] + sys.argv[1:]
    ep = subprocess.Popen(script, stdout=None, stderr=None, stdin=subprocess.DEVNULL, env=os.environ)
    print(f"Bazarr starting child process with PID {ep.pid}...")
    return ep


def terminate_child():
    print(f"Terminating child process with PID {child_process.pid}")
    child_process.terminate()


def get_stop_status_code(input_file):
    try:
        with open(input_file, 'r') as file:
            # read status code from file, if it exists
            line = file.readline()
            try:
                status_code = int(line)
            except (ValueError, TypeError):
                status_code = EXIT_NORMAL
            file.close()
    except Exception:
        status_code = EXIT_NORMAL
    return status_code


def check_status():
    global child_process
    if os.path.exists(stop_file):
        status_code = get_stop_status_code(stop_file)
        try:
            print("Deleting stop file...")
            os.remove(stop_file)
        except Exception:
            print('Unable to delete stop file.')
        finally:
            terminate_child()
            exit_program(status_code)

    if os.path.exists(restart_file):
        try:
            print("Deleting restart file...")
            os.remove(restart_file)
        except Exception:
            print('Unable to delete restart file.')
        finally:
            terminate_child()
            print("Bazarr is restarting...")
            child_process = start_bazarr()


def interrupt_handler(signum, frame):
    # catch and ignore keyboard interrupt Ctrl-C
    # the child process Server object will catch SIGINT and perform an orderly shutdown
    global interrupted
    if not interrupted:
        # ignore user hammering Ctrl-C; we heard you the first time!
        interrupted = True
        print('Handling keyboard interrupt...')
    else:
        print("Stop doing that! I heard you the first time!")


if __name__ == '__main__':
    interrupted = False
    signal.signal(signal.SIGINT, interrupt_handler)
    restart_file = os.path.join(args.config_dir, FILE_RESTART)
    stop_file = os.path.join(args.config_dir, FILE_STOP)
    os.environ[ENV_STOPFILE] = stop_file
    os.environ[ENV_RESTARTFILE] = restart_file

    # Cleanup leftover files
    try:
        os.remove(restart_file)
    except FileNotFoundError:
        pass

    try:
        os.remove(stop_file)
    except FileNotFoundError:
        pass

    # Initial start of main bazarr process
    child_process = start_bazarr()

    # Keep the script running forever until stop is requested through term, special files or keyboard interrupt
    while True:
        check_status()
        try:
            time.sleep(5)
        except (KeyboardInterrupt, SystemExit, ChildProcessError):
            # this code should never be reached, if signal handling is working properly
            print('Bazarr exited main script file via keyboard interrupt.')
            exit_program(EXIT_INTERRUPT)
