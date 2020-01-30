# coding=utf-8

from __future__ import absolute_import
from __future__ import print_function

import bazarr.libs
import subprocess as sp
import time
import os
import sys

from bazarr.get_args import args


def check_python_version():
    python_version = (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
    python_version_str = '.'.join(map(str, python_version))
    minimum_python3_version = (3, 6, 0)
    minimum_python3_version_str = '.'.join(map(str, minimum_python3_version))

    if python_version >= minimum_python3_version:
        pass
    else:
        print("Python " + minimum_python3_version_str + " or greater required. Current version is " +
              python_version_str + ". Please upgrade Python.")
        os._exit(0)


check_python_version()

dir_name = os.path.dirname(__file__)


def start_bazarr():
    script = [sys.executable, "-u", os.path.normcase(os.path.join(dir_name, 'bazarr', 'main.py'))] + sys.argv[1:]
    
    ep = sp.Popen(script, stdout=sp.PIPE, stderr=sp.STDOUT, stdin=sp.PIPE)
    print("Bazarr starting...")
    try:
        while True:
            line = ep.stdout.readline()
            if line == '' or not line:
                break
            sys.stdout.buffer.write(line)
            sys.stdout.flush()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    restartfile = os.path.normcase(os.path.join(args.config_dir, 'bazarr.restart'))
    stopfile = os.path.normcase(os.path.join(args.config_dir, 'bazarr.stop'))
    
    try:
        os.remove(restartfile)
    except:
        pass
    
    try:
        os.remove(stopfile)
    except:
        pass
    
    
    def daemon():
        if os.path.exists(stopfile):
            try:
                os.remove(stopfile)
            except:
                print('Unable to delete stop file.')
            else:
                print('Bazarr exited.')
                os._exit(0)
        
        if os.path.exists(restartfile):
            try:
                os.remove(restartfile)
            except:
                print('Unable to delete restart file.')
            else:
                start_bazarr()
    
    
    start_bazarr()
    
    # Keep the script running forever.
    while True:
        daemon()
        time.sleep(1)
