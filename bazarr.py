# coding=utf-8

import subprocess as sp
import time
import os
import sys
import platform
import re

from bazarr.get_args import args


def check_python_version():
    python_version = platform.python_version_tuple()
    minimum_python_version_tuple = (2, 7, 13)
    minimum_python_version = ".".join(str(i) for i in minimum_python_version_tuple)

    if int(python_version[0]) > minimum_python_version_tuple[0]:
        print "Python 3 isn't supported. Please use Python " + minimum_python_version + " or greater."
        os._exit(0)

    elif int(python_version[1]) < minimum_python_version_tuple[1] or int(re.search(r'\d+', python_version[2]).group()) < minimum_python_version_tuple[2]:
        print "Python " + minimum_python_version + " or greater required. Current version is " + platform.python_version() + ". Please upgrade Python."
        os._exit(0)


check_python_version()

dir_name = os.path.dirname(__file__)


def start_bazarr():
    script = [sys.executable, "-u", os.path.normcase(os.path.join(dir_name, 'bazarr', 'main.py'))] + sys.argv[1:]
    
    ep = sp.Popen(script, stdout=sp.PIPE, stderr=sp.STDOUT, stdin=sp.PIPE)
    print "Bazarr starting..."
    try:
        for line in iter(ep.stdout.readline, ''):
            sys.stdout.write(line)
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
                print 'Unable to delete stop file.'
            else:
                print 'Bazarr exited.'
                os._exit(0)
        
        if os.path.exists(restartfile):
            try:
                os.remove(restartfile)
            except:
                print 'Unable to delete restart file.'
            else:
                start_bazarr()
    
    
    start_bazarr()
    
    # Keep the script running forever.
    while True:
        daemon()
        time.sleep(1)
