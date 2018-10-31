import sys
import inspect

class _SkippedBlock(Exception):
    pass

class maybe(object):
    def __init__(self, predicate):
        self.predicate = predicate

    def __empty_fn(self, *args, **kwargs):
        return None

    def __enter__(self):
        if not self.predicate():
            sys.settrace(self.__empty_fn)
            frame = inspect.currentframe(1)
            frame.f_trace = self.__trace

    def __trace(self, *args, **kwargs):
        raise _SkippedBlock()

    def __exit__(self, type, value, traceback):
        if isinstance(value, _SkippedBlock):
            sys.settrace(None)
            return True
        return False
