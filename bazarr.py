# coding=utf-8

import os
import platform
import subprocess
import sys
import time
import atexit

from bazarr.get_args import args


def check_python_version():
    python_version = platform.python_version_tuple()
    minimum_py3_tuple = (3, 7, 0)
    minimum_py3_str = ".".join(str(i) for i in minimum_py3_tuple)

    if int(python_version[0]) < minimum_py3_tuple[0]:
        print("Python " + minimum_py3_str + " or greater required. "
              "Current version is " + platform.python_version() + ". Please upgrade Python.")
        sys.exit(1)
    elif (int(python_version[0]) == minimum_py3_tuple[0] and int(python_version[1]) < minimum_py3_tuple[1]) or \
            (int(python_version[0]) != minimum_py3_tuple[0]):
        print("Python " + minimum_py3_str + " or greater required. "
              "Current version is " + platform.python_version() + ". Please upgrade Python.")
        sys.exit(1)


check_python_version()

dir_name = os.path.dirname(__file__)


def start_bazarr():
    script = [sys.executable, "-u", os.path.normcase(os.path.join(dir_name, 'bazarr', 'main.py'))] + sys.argv[1:]
    ep = subprocess.Popen(script, stdout=None, stderr=None, stdin=subprocess.DEVNULL)
    atexit.register(lambda: ep.kill())


def check_status():
    if os.path.exists(stopfile):
        try:
            os.remove(stopfile)
        except Exception:
            print('Unable to delete stop file.')
        finally:
            print('Bazarr exited.')
            sys.exit(0)

    if os.path.exists(restartfile):
        try:
            os.remove(restartfile)
        except Exception:
            print('Unable to delete restart file.')
        else:
            print("Bazarr is restarting...")
            start_bazarr()


if __name__ == '__main__':
    restartfile = os.path.join(args.config_dir, 'bazarr.restart')
    stopfile = os.path.join(args.config_dir, 'bazarr.stop')

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
    print("Bazarr starting...")
    start_bazarr()

    # Keep the script running forever until stop is requested through term or keyboard interrupt
    while True:
        check_status()
        try:
            time.sleep(5)
        except (KeyboardInterrupt, SystemExit):
            pass
