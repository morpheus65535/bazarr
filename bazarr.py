# coding=utf-8

from __future__ import absolute_import
from __future__ import print_function

import bazarr.libs
import subprocess as sp
import time
import os
import sys
import signal

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

    '''
    Waits all the provided processes for the specified amount of time in seconds.
    '''
    @staticmethod
    def __wait_for_processes(processes, timeout):
        reference_ts = time.time()
        elapsed = 0
        remaining_processes = list(processes)
        while elapsed < timeout and len(remaining_processes) > 0:
            remaining_time = timeout - elapsed
            for ep in list(remaining_processes):
                if ep.poll() is not None:
                    remaining_processes.remove(ep)
                else:
                    if remaining_time > 0:
                        if PY3:
                            try:
                                ep.wait(remaining_time)
                                remaining_processes.remove(ep)
                            except sp.TimeoutExpired:
                                pass
                        else:
                            '''
                            In python 2 there is no such thing as some mechanism to wait with a timeout.
                            '''
                            time.sleep(1)
                        elapsed = time.time() - reference_ts
                        remaining_time = timeout - elapsed
        return remaining_processes

    '''
    Sends to every single of the specified processes the given signal and (if live_processes is not None) append to it processes which are still alive.
    '''
    @staticmethod
    def __send_signal(processes, signal_no, live_processes=None):
        for ep in processes:
            if ep.poll() is None:
                if live_processes is not None:
                    live_processes.append(ep)
                try:
                    ep.send_signal(signal_no)
                except Exception as e:
                    print('Failed sending signal %s to process %s because of an unexpected error: %s' % (signal_no, ep.pid, e))
        return live_processes

    '''
    Flags this instance as should stop and terminates as smoothly as possible children processes.
    '''
    def stop(self):
        self.__should_stop = True
        live_processes = DaemonStatus.__send_signal(self.__processes, signal.SIGINT, list())
        live_processes = DaemonStatus.__wait_for_processes(live_processes, 120)
        DaemonStatus.__send_signal(live_processes, signal.SIGTERM)

    def should_stop(self):
        return self.__should_stop


def start_bazarr(process_registry=ProcessRegistry()):
    script = [sys.executable, "-u", os.path.normcase(os.path.join(dir_name, 'bazarr', 'main.py'))] + sys.argv[1:]
    
    ep = sp.Popen(script, stdout=sp.PIPE, stderr=sp.STDOUT, stdin=sp.PIPE)
    process_registry.register(ep)
    print("Bazarr starting...")
    try:
        while True:
            line = ep.stdout.readline()
            if line == '' or not line:
                # Process ended so let's unregister it
                process_registry.unregister(ep)
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
    
    
    def daemon(bazarr_runner = lambda: start_bazarr()):
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
                bazarr_runner()
    
    
    bazarr_runner = lambda: start_bazarr()
    
    should_stop = lambda: False

    if PY3:
        daemonStatus = DaemonStatus()

        def shutdown():
            # indicates that everything should stop
            daemonStatus.stop()
            # emulate a Ctrl C command on itself (bypasses the signal thing but, then, emulates the "Ctrl+C break")
            os.kill(os.getpid(), signal.SIGINT)

        signal.signal(signal.SIGTERM, lambda signal_no, frame: shutdown())

        should_stop = lambda: daemonStatus.should_stop()
        bazarr_runner = lambda: start_bazarr(daemonStatus)

    bazarr_runner()

    # Keep the script running forever until stop is requested through term or keyboard interrupt
    while not should_stop():
        daemon(bazarr_runner)
        time.sleep(1)
