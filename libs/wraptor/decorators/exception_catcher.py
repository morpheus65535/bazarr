from functools import wraps
import sys
import Queue

def exception_catcher(fn):
    """ Catch exceptions raised by the decorated function.
        Call check() to raise any caught exceptions.
    """
    exceptions = Queue.Queue()

    @wraps(fn)
    def wrapped(*args, **kwargs):
        try:
            ret = fn(*args, **kwargs)
        except Exception:
            exceptions.put(sys.exc_info())
            raise
        return ret

    def check():
        try:
            item = exceptions.get(block=False)
            klass, value, tb = item
            raise klass, value, tb
        except Queue.Empty:
            pass

    setattr(wrapped, 'check', check)
    return wrapped
