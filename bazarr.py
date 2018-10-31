import subprocess as sp
import threading
import time
import os
import sys

from bazarr.get_argv import config_dir, arguments

dir_name = os.path.dirname(__file__)


def start_bazarr():
    script = [sys.executable, "-u", os.path.normcase(os.path.join(globals()['dir_name'], 'bazarr/main.py'))] + arguments

    ep = sp.Popen(script, stdout=sp.PIPE, stderr=sp.STDOUT, stdin=sp.PIPE)
    print "Bazarr starting..."
    try:
        for line in iter(ep.stdout.readline, ''):
            sys.stdout.write(line)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    restartfile = os.path.normcase(os.path.join(config_dir, 'bazarr.restart'))
    stopfile = os.path.normcase(os.path.join(config_dir, 'bazarr.stop'))

    try:
        os.remove(restartfile)
    except:
        pass

    try:
        os.remove(stopfile)
    except:
        pass

    def daemon():
        threading.Timer(1.0, daemon).start()
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


    daemon()

    start_bazarr()


    # Keep the script running forever.
    while True:
        time.sleep(0.001)