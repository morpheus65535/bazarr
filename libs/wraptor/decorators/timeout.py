from functools import wraps
import signal

class TimeoutException(Exception):
    pass

class timeout(object):
    """ Basic timeout decorator
        * Uses signals, so this can only be used in the main thread of execution
        * seconds must be a positive integer
        Signal implementation based on http://code.activestate.com/recipes/307871-timing-out-function/
    """
    def __init__(self, seconds=1):
        self.seconds = seconds

    def __call__(self, fn):
        def sig_handler(signum, frame):
            raise TimeoutException()

        @wraps(fn)
        def wrapped(*args, **kwargs):
            old = signal.signal(signal.SIGALRM, sig_handler)
            signal.alarm(self.seconds)
            try:
                result = fn(*args, **kwargs)
            finally:
                signal.signal(signal.SIGALRM, old)
            signal.alarm(0)
            return result

        return wrapped
