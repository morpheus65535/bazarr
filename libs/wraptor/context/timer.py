import time

class timer(object):
    __slots__ = ('name', 'interval', 'start', 'end')

    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.start = time.time() * 1e3
        return self

    def __exit__(self, *args):
        self.end = time.time() * 1e3
        self.interval = self.end - self.start

    def __str__(self):
        return "%s took %.03f ms" % (self.name, self.interval)
