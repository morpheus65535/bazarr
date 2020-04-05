# coding=utf-8

import bazarr.libs
import os
import signal
import subprocess
import sys
import time

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


class ProcessRegistry:

    def register(self, process):
        pass

    def unregister(self, process):
        pass


class DaemonStatus(ProcessRegistry):

    def __init__(self):
        self.__should_stop = False
        self.__processes = set()

    def register(self, process):
        self.__processes.add(process)

    def unregister(self, process):
        self.__processes.remove(process)

    @staticmethod
    def __send_signal(processes, signal_no, live_processes=None):
        """
        Sends to every single of the specified processes the given signal and (if live_processes is not None) append to
        it processes which are still alive.
        """
        for ep in processes:
            if ep.poll() is None:
                if live_processes is not None:
                    live_processes.append(ep)
                try:
                    ep.send_signal(signal_no)
                except Exception as e:
                    print('Failed sending signal %s to process %s because of an unexpected error: %s' % (
                        signal_no, ep.pid, e))
        return live_processes

    def stop(self):
        """
        Flags this instance as should stop and terminates as smoothly as possible children processes.
        """
        self.__should_stop = True
        DaemonStatus.__send_signal(self.__processes, signal.SIGINT, list())

    def force_stop(self):
        self.__should_stop = True
        DaemonStatus.__send_signal(self.__processes, signal.SIGTERM)

    def should_stop(self):
        return self.__should_stop


def start_bazarr(process_registry=ProcessRegistry()):
    script = [sys.executable, "-u", os.path.normcase(os.path.join(dir_name, 'bazarr', 'main.py'))] + sys.argv[1:]

    print("Bazarr starting...")
    ep = subprocess.Popen(script, stdout=None, stderr=None, stdin=subprocess.DEVNULL)
    process_registry.register(ep)
    try:
        ep.wait()
        process_registry.unregister(ep)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    restartfile = os.path.normcase(os.path.join(args.config_dir, 'bazarr.restart'))
    stopfile = os.path.normcase(os.path.join(args.config_dir, 'bazarr.stop'))

    try:
        os.remove(restartfile)
    except Exception:
        pass

    try:
        os.remove(stopfile)
    except Exception:
        pass


    def daemon(bazarr_runner=lambda: start_bazarr()):
        if os.path.exists(stopfile):
            try:
                os.remove(stopfile)
            except Exception:
                print('Unable to delete stop file.')
            else:
                print('Bazarr exited.')
                sys.exit(0)

        if os.path.exists(restartfile):
            try:
                os.remove(restartfile)
            except Exception:
                print('Unable to delete restart file.')
            else:
                bazarr_runner()

    def should_stop():
        return daemonStatus.should_stop()

    def bazarr_runner():
        start_bazarr(daemonStatus)

    daemonStatus = DaemonStatus()

    def force_shutdown():
        # force the killing of children processes
        daemonStatus.force_stop()
        # if a new SIGTERM signal is caught the standard behaviour should be followed
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        # emulate a Ctrl C command on itself (bypasses the signal thing but, then, emulates the "Ctrl+C break")
        os.kill(os.getpid(), signal.SIGINT)

    def shutdown():
        # indicates that everything should stop
        daemonStatus.stop()
        # if a new sigterm signal is caught it should force the shutdown of children processes
        signal.signal(signal.SIGTERM, lambda signal_no, frame: force_shutdown())

    signal.signal(signal.SIGTERM, lambda signal_no, frame: shutdown())

    bazarr_runner()

    # Keep the script running forever until stop is requested through term or keyboard interrupt
    while not should_stop():
        daemon(bazarr_runner)
        time.sleep(1)
