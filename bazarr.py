import subprocess as sp
import threading
import time
import os
import signal
import logging
import sys
import getopt

log = logging.getLogger()
log.setLevel(logging.DEBUG)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setLevel(logging.INFO)
log.addHandler(out_hdlr)

arguments = []
try:
    opts, args = getopt.getopt(sys.argv[1:],"h:",["no-update", "config="])
except getopt.GetoptError:
    print 'daemon.py -h --no-update --config <config_directory>'
    sys.exit(2)
for opt, arg in opts:
    arguments.append(opt)
    if arg != '':
        arguments.append(arg)


def start_bazarr():
    script = ['python','main.py'] + globals()['arguments']

    pidfile = os.path.normcase(os.path.join(os.path.dirname(__file__), 'bazarr.pid'))
    if os.path.exists(pidfile):
        logging.error("Bazarr already running, please stop it first.")
    else:
        ep = sp.Popen(script, stdout=sp.PIPE, stderr=sp.STDOUT)
        try:
            file = open(pidfile,'w')
        except:
            logging.error("Error trying to write pid file.")
        else:
            file.write(str(ep.pid))
            file.close()
            logging.info("Bazarr starting with process id: " + str(ep.pid) + "...")
            for line in iter(ep.stdout.readline, ''):
                sys.stdout.write(line)


def shutdown_bazarr(restarting):
    pidfile = os.path.normcase(os.path.join(os.path.dirname(__file__), 'bazarr.pid'))
    if os.path.exists(pidfile):
        try:
            file = open(pidfile,'r')
        except:
            logging.error("Error trying to read pid file.")
        else:
            pid = file.read()
            file.close()
            try:
                os.remove(pidfile)
            except:
                logging.error("Unable to delete pid file.")
            else:
                logging.info('Bazarr stopping...')
                if restarting is False:
                    stopfile = os.path.normcase(os.path.join(os.path.dirname(__file__), 'bazarr.stop'))
                    file = open(stopfile, 'w')
                    file.write('')
                    file.close()
                os.kill(int(pid), signal.SIGINT)
    else:
        logging.warn("pid file doesn't exist. You must start Bazarr first.")


def restart_bazarr():
    restartfile = os.path.normcase(os.path.join(os.path.dirname(__file__), 'bazarr.restart'))
    file = open(restartfile, 'w')
    file.write('')
    file.close()


if __name__ == '__main__':
    pidfile = os.path.normcase(os.path.join(os.path.dirname(__file__), 'bazarr.pid'))
    restartfile = os.path.normcase(os.path.join(os.path.dirname(__file__), 'bazarr.restart'))
    stopfile = os.path.normcase(os.path.join(os.path.dirname(__file__), 'bazarr.stop'))

    try:
        os.remove(pidfile)
        os.remove(restartfile)
        os.remove(stopfile)
    except:
        pass

    def daemon():
        threading.Timer(1.0, daemon).start()
        if os.path.exists(stopfile):
            try:
                os.remove(stopfile)
            except:
                logging.error('Unable to delete stop file.')
            else:
                logging.info('Bazarr exited.')
                os._exit(0)

        if os.path.exists(restartfile):
            try:
                os.remove(restartfile)
            except:
                logging.error('Unable to delete restart file.')
            else:
                shutdown_bazarr(True)
                start_bazarr()


    daemon()

    start_bazarr()

    # Keep the script running forever.
    while True:
        time.sleep(0.001)