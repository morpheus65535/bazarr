# coding=utf-8

import os
import platform
import signal
import subprocess
import sys
import time
import atexit

from bazarr.app.get_args import args
from bazarr.literals import *

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
    elif int(python_version[0]) == 3 and int(python_version[1]) > 11:
        print("Python version greater than 3.11.x is unsupported. Current version is " + platform.python_version() +
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


def end_child_process(ep):
    try:
        if os.name != 'nt':
            try:
                ep.send_signal(signal.SIGINT)
            except ProcessLookupError:
                pass
        else:
            import win32api
            import win32con
            try:
                win32api.GenerateConsoleCtrlEvent(win32con.CTRL_C_EVENT, ep.pid)
            except KeyboardInterrupt:
                pass
    except:
        ep.terminate()


def start_bazarr():
    script = [get_python_path(), "-u", os.path.normcase(os.path.join(dir_name, 'bazarr', 'main.py'))] + sys.argv[1:]
    ep = subprocess.Popen(script, stdout=None, stderr=None, stdin=subprocess.DEVNULL)
    atexit.register(end_child_process, ep=ep)
    signal.signal(signal.SIGTERM, lambda signal_no, frame: end_child_process(ep))
    print(f"Bazarr starting child process with PID {ep.pid}...")
    return ep


def get_stop_status_code(input_file):
    try:
        with open(input_file,'r') as file:
            # read status code from file, if it exists
            line = file.readline()
            try:
                status_code = int(line)
            except (ValueError, TypeError):
                status_code = EXIT_NORMAL
            file.close()
    except:
        status_code = EXIT_NORMAL
    return status_code


def check_status():
    global child_process
    if os.path.exists(stopfile):
        status_code = get_stop_status_code(stopfile)
        try:
            print(f"Deleting stop file...")
            os.remove(stopfile)
        except Exception as e:
            print('Unable to delete stop file.')
        finally:
            print(f"Terminating child process with PID {child_process.pid}")
            child_process.terminate()
            exit_program(status_code)

    if os.path.exists(restartfile):
        try:
            print(f"Deleting restart file...")
            os.remove(restartfile)
        except Exception:
            print('Unable to delete restart file.')
        finally:
            print(f"Terminating child process with PID {child_process.pid}")
            child_process.terminate()
            print(f"Bazarr is restarting...")
            child_process = start_bazarr()


if __name__ == '__main__':
    restartfile = os.path.join(args.config_dir, FILE_RESTART)
    stopfile = os.path.join(args.config_dir, FILE_STOP)
    os.environ[ENV_STOPFILE] = stopfile
    os.environ[ENV_RESTARTFILE] = restartfile

    # Cleanup leftover files
    try:
        os.remove(restartfile)
    except FileNotFoundError:
        pass

    try:
        os.remove(stopfile)
    except FileNotFoundError:
        pass

    # Initial start of main bazarr process
    child_process = start_bazarr()

    # Keep the script running forever until stop is requested through term, special files or keyboard interrupt
    while True:
        check_status()
        try:
            if sys.platform.startswith('win'):
                time.sleep(5)
            else:
                os.wait()
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit, ChildProcessError):
            print(f'Bazarr exited main script file via keyboard interrupt.')
            exit_program(EXIT_NORMAL)
